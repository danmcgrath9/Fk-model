"""Every stored runner's full gear list, for the gear-detail trial (15 Oct 2026, founder: "Why don't we do any of
that?" on gear item, gear off and gear in past runs). Read-only, no Form King calls.

    python scripts/gear_table.py [--state VIC] [--history history]

Prints one line per runner: race_id <TAB> date <TAB> horse_id <TAB> JSON list of [gear name, worn, change code],
from the same resulted races export_dataset.py reads (database first, then the history files). The past-run rows
carry no gear, so "the horse's gear last start" comes from joining its earlier races in this table.
"""
from __future__ import annotations

import argparse
import json
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
    n = 0
    codes: dict[str, int] = {}
    for row in rows:
        date = str(row.get("date") or row.get("meeting_date") or "")[:10]
        for e in row.get("entries") or []:
            gear = []
            for g in e.get("gear") or []:
                if isinstance(g, dict):
                    ch = str(g.get("change") or "")
                    gear.append([str(g.get("gear") or ""), bool(g.get("on")), ch])
                    codes[ch] = codes.get(ch, 0) + 1
            print(f"{row['race_id']}\t{date}\t{F.horse_id(e)}\t{json.dumps(gear, separators=(',', ':'))}")
            n += 1
    print(f"# {n} runners; change codes: {json.dumps(codes)}", file=sys.stderr)
    print(f"# {n} runners; change codes: {json.dumps(codes)}")


if __name__ == "__main__":
    main()
