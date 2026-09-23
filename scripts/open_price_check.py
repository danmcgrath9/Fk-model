"""Which opening price the live model had for each race on a day. Read-only.

    python scripts/open_price_check.py --date 2026-09-23 [--track Geelong]

The model's market input is each runner's avgOpen as stored in fk.entries.raw (the race
form, pulled the evening before). A runner with none there is filled with the field's
average chance, which makes an outsider look like an ordinary runner. This prints, per
race, how many runners carried one in the entry, and how many the morning odds snapshots
hold, so the gap is a number rather than a guess.
"""
from __future__ import annotations

import argparse

from _common import load_settings
from fk import fields as F
from fk.db import Db


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--track")
    ap.add_argument("--state", default="VIC")
    a = ap.parse_args()
    db = Db(load_settings().database_url)
    print("| Track | Race | Runners | Open price in the entry | Open price in the morning snapshot |")
    print("|---|---|---|---|---|")
    for r in db.races_on(a.date, a.state):
        track = r.get("track") or ""
        if a.track and not track.lower().startswith(a.track.lower()):
            continue
        entries = [e for e in db.entries_for_race(r["race_id"]) if not e.get("scratched")]
        in_entry = sum(1 for e in entries if (F.entry_odds(e["raw"] or {}) or {}).get("avgOpen") is not None)
        snap = db.latest_odds(r["race_id"])
        in_snap = sum(1 for e in entries if snap.get(e["horse_id"], {}).get("opening") is not None)
        print(f"| {track} | R{r['race_number']} | {len(entries)} | {in_entry} | {in_snap} |")


if __name__ == "__main__":
    main()
