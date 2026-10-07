"""Results for stored meetings: race, horse, finish, starting price, BSP. DB only, no credits.

    python scripts/meeting_results.py pakenham-synthetic-20261005 mildura-20261006
"""
from __future__ import annotations

import os
import sys

import psycopg

with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for mid in sys.argv[1:]:
        rows = c.execute("""select r.race_number, coalesce(e.raw->'horse'->>'name', e.raw->>'horseName', e.raw->>'name'),
                                   coalesce(res.finish_position, (e.raw->'horseResult'->>'finishPosition')::int),
                                   coalesce(res.starting_price, (e.raw->'horseResult'->>'startingPrice')::numeric),
                                   coalesce((res.raw->>'betfairStartingPrice')::numeric, (e.raw->'horseResult'->>'betfairStartingPrice')::numeric)
                            from fk.entries e join fk.races r using (race_id)
                                 left join fk.results res on res.race_id = e.race_id and res.horse_id = e.horse_id
                            where r.meeting_id = %s order by r.race_number, 3 nulls last""", (mid,)).fetchall()
        print(f"## {mid}: {len(rows)} entries")
        for rn, name, fin, sp, bsp in rows:
            print(f"R{rn} {name!s:24s} finish {fin}  SP {sp}  BSP {bsp}")
