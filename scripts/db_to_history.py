"""Move old races' runners out of the database into the history files.

    python scripts/db_to_history.py copy   [--keep-days 21] [--history history]
    python scripts/db_to_history.py verify  --check DIR
    python scripts/db_to_history.py delete  --check DIR --yes

Why (13 Oct 2026). Supabase's free plan caps the organisation at about 1.1 GB and 5.5 GB of
downloads a month, and the horse database alone was 1,124 MB, 529 MB of it fk.entries:
every runner's whole Form King reply, kept for every race since May. The daily retrain
also read all of it every morning, which is most of the 11 GB of downloads. A race that
has run never changes, and fk/history.py already keeps past days as compressed files on
the repo's "history" release, which the export, the fit and the trials read beside the
database. This puts the database's old races there too, so the database holds only the
last few weeks and the morning read is small.

Three steps, each its own run, so nothing is deleted until a fresh download proves the
files hold it:

  copy    Every resulted race before (today - keep_days), exactly as Db.resulted_races
          returns it (results folded in, state and the pulled-before-the-jump flag
          included), written into the day files under --history (merged with what is
          there) and listed in <history>/moved.json with a fingerprint of each race.
          The workflow uploads the changed day files and moved.json to the release.
  verify  Reads a FRESH download of the release (--check) and confirms every race in
          moved.json is there with the same fingerprint. Exit 1 on any miss.
  delete  Runs verify first, then deletes those races' fk.entries rows (and nothing
          else: fk.races, fk.results, fk.speedmaps and the horse tables stay) and
          VACUUM FULLs fk.entries to give the space back. Needs --yes.

What stays the same for the model: H.resulted_races yields the same rows from the files
that the database used to, and the pulled-before-the-jump split now reads both places
(H.pulled_before_jump). Db.resulted_races only counts a race as held while its runners
are, so a moved race's leftover fk.results rows cannot hide the file copy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _common import today_melbourne  # noqa: E402
from fk import history as H  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "moved.json"
DELETE_BATCH = 200


def _plain(v: Any) -> Any:
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    raise TypeError(f"not JSON: {type(v).__name__}")


def normalise(row: dict) -> dict:
    """The row as the file will hold it: a JSON round trip, so the fingerprint taken here
    is the fingerprint of what is read back."""
    return json.loads(json.dumps(row, default=_plain))


def fingerprint(bundle: dict) -> str:
    return hashlib.sha256(json.dumps(bundle, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()


def plan_days(rows: list[dict]) -> dict[str, list[dict]]:
    by_day: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_day[str(r["date"])[:10]].append(r)
    return dict(sorted(by_day.items()))


def check(manifest: dict[str, str], directory: Path) -> list[str]:
    """Race ids in the manifest that the files do not hold exactly. Empty = all present."""
    held = {b["race_id"]: fingerprint(b) for p in H.files(directory) for b in H.read_file(p)}
    return sorted(rid for rid, fp in manifest.items() if held.get(rid) != fp)


def cmd_copy(a) -> None:
    from _common import load_settings
    from fk.db import Db
    cutoff = (today_melbourne() - timedelta(days=a.keep_days)).isoformat()
    db = Db(load_settings().database_url)
    rows = [normalise(r) for r in db.resulted_races(None, before=cutoff)]
    out = Path(a.history)
    days = plan_days(rows)
    for day, bundles in days.items():
        H.write_day(out, day, bundles)
    manifest = {r["race_id"]: fingerprint(r) for r in rows}
    (out / MANIFEST).write_text(json.dumps({"cutoff": cutoff, "races": manifest}, indent=0, sort_keys=True))
    (out / "changed_days.txt").write_text("".join(f"{H.day_path(out, d).name}\n" for d in days))
    runners = sum(len(r["entries"]) for r in rows)
    pre = sum(1 for r in rows if r.get("pulled_before_jump"))
    print(f"copied {len(rows)} races ({runners} runners, {pre} pulled before the jump) from {len(days)} days "
          f"before {cutoff} into {out}; first day {next(iter(days), '-')}, last {next(reversed(days), '-') if days else '-'}")


def load_manifest(directory: Path) -> tuple[str, dict[str, str]]:
    m = json.loads((Path(directory) / MANIFEST).read_text())
    return m["cutoff"], m["races"]


def cmd_verify(a) -> int:
    cutoff, manifest = load_manifest(Path(a.check))
    missing = check(manifest, Path(a.check))
    if missing:
        print(f"VERIFY FAILED: {len(missing)} of {len(manifest)} races not held exactly by the release, e.g. {missing[:5]}")
        return 1
    print(f"verified: all {len(manifest)} races before {cutoff} are on the release, byte for byte")
    return 0


def cmd_delete(a) -> int:
    if not a.yes:
        print("delete needs --yes")
        return 2
    if cmd_verify(a) != 0:
        print("nothing deleted")
        return 1
    from psycopg import connect
    from _common import load_settings
    cutoff, manifest = load_manifest(Path(a.check))
    ids = sorted(manifest)
    url = load_settings().database_url
    with connect(url, autocommit=True) as conn:
        def sizes() -> str:
            db_mb, e_mb = conn.execute(
                "select pg_database_size(current_database()), pg_total_relation_size('fk.entries')").fetchone()
            return f"database {db_mb / 1024 / 1024:.1f} MB, fk.entries {e_mb / 1024 / 1024:.1f} MB"
        print(f"before: {sizes()}")
        gone = 0
        for i in range(0, len(ids), DELETE_BATCH):
            # the date guard is belt and braces: a race id in the manifest is before the cutoff by construction
            cur = conn.execute(
                """delete from fk.entries e using fk.races r, fk.meetings m
                   where e.race_id = r.race_id and r.meeting_id = m.meeting_id
                     and e.race_id = any(%s) and m.meeting_date < %s::date""",
                (ids[i:i + DELETE_BATCH], cutoff))
            gone += cur.rowcount
        print(f"deleted {gone} runner rows from {len(ids)} races")
        conn.execute("vacuum full fk.entries")
        print(f"after:  {sizes()}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("copy")
    c.add_argument("--keep-days", type=int, default=21)
    c.add_argument("--history", default=str(ROOT / "history"))
    for name in ("verify", "delete"):
        p = sub.add_parser(name)
        p.add_argument("--check", required=True, help="a fresh download of the history release")
        if name == "delete":
            p.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    if a.cmd == "copy":
        cmd_copy(a)
        return 0
    return cmd_verify(a) if a.cmd == "verify" else cmd_delete(a)


if __name__ == "__main__":
    sys.exit(main())
