"""The rail position of every race we hold, and each runner's actual settling position in it, recovered from the
past-run records of horses that raced later (15 Oct 2026, founder: "every track should have its known biases ... based
on the rail position"). Read-only, no Form King calls: each past run carries benchmark.railMetres and posSettling, and
a race we hold appears as a past run of every horse that raced again.

    python scripts/race_rails.py [--state VIC] [--history history]

Prints:  R <TAB> race_id <TAB> rail metres (the most common value seen)      one line per race
         S <TAB> race_id <TAB> horse_id <TAB> settling position <TAB> runners   one line per runner seen
"""
from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import load_settings  # noqa: E402
from fk import fields as F  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--history", default=str(ROOT / "history"))
    a = ap.parse_args()
    from fk import history as H
    from fk.db import Db
    db = Db(load_settings().database_url)
    rows = list(db.resulted_races(a.state))
    in_db = {r["race_id"] for r in rows}
    rows += list(H.resulted_races(Path(a.history), a.state, skip=in_db))
    rails: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    settle: dict[tuple[str, str], tuple] = {}
    for row in rows:
        for e in row.get("entries") or []:
            hid = F.horse_id(e)
            for p in F.entry_past_events(e):
                rid = str(p.get("raceId") or "")
                if not rid:
                    continue
                b = p.get("benchmark") if isinstance(p.get("benchmark"), dict) else {}
                if b.get("railMetres") is not None:
                    rails[rid][b["railMetres"]] += 1
                s = p.get("posSettling")
                if s not in (None, 0, "0", "") and (rid, hid) not in settle:
                    settle[(rid, hid)] = (s, p.get("numRunners"))
    for rid, c in rails.items():
        print(f"R\t{rid}\t{c.most_common(1)[0][0]}")
    for (rid, hid), (s, n) in settle.items():
        print(f"S\t{rid}\t{hid}\t{s}\t{n}")
    print(f"# {len(rails)} races with a rail, {len(settle)} runner settling positions")


if __name__ == "__main__":
    main()
