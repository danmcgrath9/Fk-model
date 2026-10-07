"""Rail position (Form King's railPosition text) for every stored VIC race, as CSV race_id,date,track,rail, for the
rail-bias research (research/form_gbm/t_rail.py). DB plus the history files, no Form King calls.

    python scripts/rail_positions.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fk import history as H


def find_rail(d, depth=0):
    """The first railPosition in a race or meeting payload, skipping runner lists."""
    if depth > 4:
        return None
    if isinstance(d, dict):
        v = d.get("railPosition")
        if isinstance(v, str) and v.strip():
            return v.strip()
        for k, x in d.items():
            if k in ("entries", "runners", "pastEvents", "form"):
                continue
            r = find_rail(x, depth + 1)
            if r:
                return r
    elif isinstance(d, list):
        for x in d[:3]:
            r = find_rail(x, depth + 1)
            if r:
                return r
    return None


seen = set()
print("race_id,date,track,rail")
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for rid, d, trk, rraw, mraw in c.execute(
            """select r.race_id, m.meeting_date, m.track, r.raw, m.raw from fk.races r join fk.meetings m using (meeting_id)
               where m.state = 'VIC'""").fetchall():
        rail = find_rail(rraw) or find_rail(mraw)
        if rail:
            seen.add(rid)
            print(f'{rid},{d},{trk},"{rail.replace(chr(34), "")}"')
for b in H.resulted_races(Path("history"), "VIC", skip=seen):
    rail = find_rail({k: v for k, v in b.items() if k != "entries"})
    if rail:
        seen.add(b["race_id"])
        print(f'{b["race_id"]},{b.get("date")},{b.get("track")},"{rail.replace(chr(34), "")}"')
print(f"# {len(seen)} races with a rail", file=sys.stderr)
