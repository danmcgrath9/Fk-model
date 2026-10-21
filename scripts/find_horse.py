"""Find horses we hold by part of a name (case-insensitive), with their recent starts. DB only, no credits.

    python scripts/find_horse.py zoe
"""
from __future__ import annotations

import os
import sys

import psycopg

with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for pat in sys.argv[1:]:
        hs = c.execute("select horse_id, name from fk.horses where name ilike %s order by name limit 25", (f"%{pat}%",)).fetchall()
        print(f"## '{pat}': {len(hs)} horse(s)")
        for hid, name in hs:
            print(f"{name} ({hid})")
            for d, mid, rn, fin, sp in c.execute(
                    """select r2.meeting_id::text, r2.meeting_id, r2.race_number, res.finish_position, res.starting_price
                       from fk.entries e join fk.races r2 using (race_id)
                       left join fk.results res on res.race_id = e.race_id and res.horse_id = e.horse_id
                       where e.horse_id = %s order by r2.meeting_id desc limit 8""", (hid,)).fetchall():
                print(f"   {mid} R{rn} finish {fin} SP {sp}")
