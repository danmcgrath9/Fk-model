"""Final place and win dividends for every stored VIC runner from a date on, as CSV, for the place-betting
research (research/form_gbm/t_place.py). DB plus the history files, no Form King calls.

    python scripts/place_divs.py 2026-05-06
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fk import fields as F
from fk import history as H

since = sys.argv[1] if len(sys.argv) > 1 else "2026-05-06"
KEYS = ("finishPosition", "totePlace", "betfairPlaceDiv", "toteWin", "bestToteWin", "betfairStartingPrice")
print("race_id,horse_id," + ",".join(KEYS))
seen = set()


def emit(race_id, horse_id, res):
    if not isinstance(res, dict) or (race_id, horse_id) in seen:
        return
    seen.add((race_id, horse_id))
    print(f"{race_id},{horse_id}," + ",".join("" if res.get(k) is None else str(res.get(k)) for k in KEYS))


with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    rows = c.execute("""select e.race_id, e.horse_id, coalesce(e.raw->'horseResult', res.raw)
                        from fk.entries e join fk.races r using (race_id) join fk.meetings m using (meeting_id)
                             left join fk.results res on res.race_id = e.race_id and res.horse_id = e.horse_id
                        where m.state = 'VIC' and m.meeting_date >= %s""", (since,)).fetchall()
    for rid, hid, res in rows:
        emit(rid, hid, res)
for race in H.resulted_races(Path("history"), "VIC"):
    if str(race.get("date", "")) < since:
        continue
    for e in race.get("entries", []):
        hid = F.horse_id(e)
        emit(race["race_id"], hid, e.get("horseResult"))
print(f"# {len(seen)} runners", file=sys.stderr)
