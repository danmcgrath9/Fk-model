"""Tote v bookie SP v Betfair SP for given meetings, runner by runner (26 Oct 2026, founder: "have a look at Flemington
Saturday? Pretty sure every winner paid under the SP of bookie"). DB only, no credits.
    python scripts/meeting_tote.py flemington-20261024 [more meeting ids]"""
from __future__ import annotations
import os, sys, statistics as st
import psycopg

q = """select r.race_number, coalesce(e.raw->'horse'->>'name', e.raw->>'horseName', e.raw->>'name'),
          coalesce(res.finish_position, (e.raw->'horseResult'->>'finishPosition')::int),
          coalesce(res.starting_price, (e.raw->'horseResult'->>'startingPrice')::numeric),
          coalesce((res.raw->>'bestToteWin')::numeric, (e.raw->'horseResult'->>'bestToteWin')::numeric),
          coalesce((res.raw->>'betfairStartingPrice')::numeric, (e.raw->'horseResult'->>'betfairStartingPrice')::numeric)
       from fk.entries e join fk.races r using (race_id)
            left join fk.results res on res.race_id = e.race_id and res.horse_id = e.horse_id
       where r.meeting_id = %s order by r.race_number, 3 nulls last"""
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for mid in sys.argv[1:]:
        rows = [r for r in c.execute(q, (mid,)).fetchall() if r[2] and r[3] and r[4]]
        print(f"## {mid}: {len(rows)} runners with SP and tote")
        print("| R | winner | SP | tote | BSP | tote v SP |\n|---|---|---|---|---|---|")
        for rn, nm, fin, sp, tote, bsp in rows:
            if fin == 1: print(f"| R{rn} | {nm} | ${float(sp):.2f} | ${float(tote):.2f} | {('$%.2f' % float(bsp)) if bsp else '-'} | {100*(float(tote)/float(sp)-1):+.1f}% |")
        r = [float(t) / float(s) for _, _, _, s, t, _ in rows]
        w = [float(t) / float(s) for _, _, f, s, t, _ in rows if f == 1]
        print(f"winners: tote under SP {sum(v < 1 for v in w)} of {len(w)}, equal {sum(v == 1 for v in w)}; median tote/SP {st.median(w):.3f}")
        print(f"all runners: tote under SP {sum(v < 1 for v in r)} of {len(r)} ({100*sum(v < 1 for v in r)/len(r):.0f}%), over {sum(v > 1 for v in r)}; median tote/SP {st.median(r):.3f}")
        for lo, hi in ((1, 5), (5, 13), (13, 1e9)):
            b = [float(t) / float(s) for _, _, _, s, t, _ in rows if lo <= float(s) < hi]
            if b: print(f"  SP ${lo}-{hi if hi < 1e9 else '+'}: {len(b)} runners, tote under SP {sum(v < 1 for v in b)}, median tote/SP {st.median(b):.3f}")
        print()
