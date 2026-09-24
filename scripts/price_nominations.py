"""Price a NOMINATION list on the form-only price, before acceptances. Read-only.

    python scripts/price_nominations.py --file data/nominations/X.txt --distance 1200 --date 2026-09-30

A nomination has no barrier, weight, rider or Form King race form yet, so each horse is
rated off its most recent Form King entry we hold (the database first, then the history
files), with the figures that belong to that OTHER race cleared: barrier, weight, rider,
days since the last run, run in the campaign, weight-for-age difference and the intent
flags all take the field average. A horse we hold nothing on is listed unpriced rather than
guessed at (it may be unraced, or have raced where we have not pulled). The prices are
across every priced nomination, so they shorten when the field is cut.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fk import backtest as B  # noqa: E402
from fk import fields as F  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
# Raw figures that describe the race the stored entry was for, not the one being priced.
OTHER_RACE = ["barrier", "weight_rel", "days_log", "run_in_prep", "wfa_diff", "jockey_win", "jt_combo_win", "exp", "open",
              "trainer_only", "jockey_only", "apprentice_claim", "dual_acceptor", "emergency"]


def key(name: str) -> str:
    """'Prolocutor (NZ)' and "He's On Point" -> 'prolocutor', 'hesonpoint'."""
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\(.*?\)", "", name.lower()))


def latest_entries(names: list[str], history_dir: Path | None) -> dict[str, tuple[str, dict]]:
    """{name key: (date, entry raw)} for the newest stored entry of each nominated horse."""
    want = {key(n) for n in names}
    found: dict[str, tuple[str, dict]] = {}

    def offer(k, date, raw):
        if k in want and (k not in found or date > found[k][0]):
            found[k] = (date, raw)
    try:
        from _common import load_settings
        from fk.db import Db
        db = Db(load_settings().database_url)
        for name, date, raw in db.conn.execute(
                """select h.name, m.meeting_date::text, e.raw
                   from fk.entries e join fk.horses h using (horse_id) join fk.races r using (race_id)
                        join fk.meetings m using (meeting_id)
                   where regexp_replace(regexp_replace(lower(h.name), '\\(.*?\\)', '', 'g'), '[^a-z0-9]', '', 'g') = any(%s)""",
                (sorted(want),)):
            offer(key(name), date, raw)
    except Exception as ex:  # noqa: BLE001
        print(f"database skipped: {type(ex).__name__}: {ex}")
    if history_dir and history_dir.exists():
        from fk import history as H
        for p in H.files(history_dir):
            for b in H.read_file(p):
                for e in b.get("entries") or []:
                    offer(key(F.horse_name(e) or ""), str(b.get("date") or p.name[:10]), e)
    return found


def price(names: list[str], found: dict, model: dict, distance: int | None, date: str | None, lws: float | None):
    from fk import projection as P
    runners, source = [], {}
    for n in names:
        k = key(n)
        r = None
        if k in found:
            r = B.runner_from_entry(found[k][1], distance, lws, date)
        if r is None:
            continue
        source[k] = f"latest entry {found[k][0]}"
        for f in OTHER_RACE:
            r.raw[f] = None
        r.horse_id, r.name = k, n
        runners.append(r)
    B.race_features(runners)
    B.shape_features(runners, {}, P.tempo_score(None))
    p = B.predict(model["beta"], runners)
    return sorted(((pi, r.name, source[r.horse_id]) for r, pi in zip(runners, p)), reverse=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--distance", type=int)
    ap.add_argument("--date")
    ap.add_argument("--lws", type=float)
    ap.add_argument("--history", default=str(ROOT / "history"))
    a = ap.parse_args()
    names = [ln.strip() for ln in Path(a.file).read_text(encoding="utf-8").splitlines() if ln.strip()]
    model = json.loads((ROOT / "config" / "form_price.json").read_text())
    found = latest_entries(names, Path(a.history))
    rows = price(names, found, model, a.distance, a.date, a.lws)
    print(f"{Path(a.file).stem}: {len(names)} nominations, {len(found)} with a Form King record; model {model['model']}\n")
    print("| rank | horse | Form $ | Take at | rated off |")
    print("|---|---|---|---|---|")
    for i, (pi, name, src) in enumerate(rows, 1):
        fp = 1 / pi
        print(f"| {i} | {name} | {fp:.2f} | {fp * 1.2:.2f} | {src} |")
    missing = [n for n in names if key(n) not in {key(r[1]) for r in rows}]
    if missing:
        print(f"\nNot priced, no Form King record held: {', '.join(missing)}")
    print("\nJSON " + json.dumps([{"horse": n, "prob": round(pi, 5), "source": s} for pi, n, s in rows]))


if __name__ == "__main__":
    main()
