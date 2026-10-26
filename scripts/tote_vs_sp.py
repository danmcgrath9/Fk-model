"""World/TAB tote against bookie SP against Betfair SP (26 Oct 2026, founder: "an analysis on the world tote prices versus
the bookie SP for me, versus BSP"). DB only, no credits.

Form King's result per runner carries toteWin (final TAB win dividend), bestToteWin (best of the three TAB totes),
startingPrice (bookmaker SP) and betfairStartingPrice. A tote dividend is declared only for the winner, so the
comparison is on winners: $1 on every runner in a set loses the same $1 on every loser whatever the price source, so
return = (sum of the winners' price - runners) / runners is exact for each source on the same set of runners.
Betfair is shown gross and after 8% commission on winnings.
    python scripts/tote_vs_sp.py [since YYYY-MM-DD]"""
from __future__ import annotations
import os, sys, statistics as st
import psycopg

since = sys.argv[1] if len(sys.argv) > 1 else "2025-01-01"
q = """select r.race_id, m.meeting_date::text, coalesce(res.finish_position, (e.raw->'horseResult'->>'finishPosition')::int),
          coalesce(res.starting_price, (e.raw->'horseResult'->>'startingPrice')::numeric),
          coalesce((res.raw->>'betfairStartingPrice')::numeric, (e.raw->'horseResult'->>'betfairStartingPrice')::numeric),
          coalesce((res.raw->>'toteWin')::numeric, (e.raw->'horseResult'->>'toteWin')::numeric),
          coalesce((res.raw->>'bestToteWin')::numeric, (e.raw->'horseResult'->>'bestToteWin')::numeric)
       from fk.entries e join fk.races r using (race_id) join fk.meetings m using (meeting_id)
            left join fk.results res on res.race_id = e.race_id and res.horse_id = e.horse_id
       where m.meeting_date >= %s"""
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    rows = c.execute(q, (since,)).fetchall()
R = [dict(race=a, date=d, fin=f, sp=float(sp) if sp else None, bsp=float(b) if b else None, tote=float(t) if t else None,
          btote=float(bt) if bt else None) for a, d, f, sp, b, t, bt in rows]
runners = [x for x in R if x["fin"] and x["sp"] and x["sp"] > 1]
win = [x for x in runners if x["fin"] == 1]
print(f"since {since}: {len(R)} entries, {len(runners)} runners with a finish and an SP, {len(win)} winners")
print(f"winners with toteWin {sum(1 for x in win if x['tote'])}, bestToteWin {sum(1 for x in win if x['btote'])}, BSP {sum(1 for x in win if x['bsp'])}")
print(f"losers carrying a toteWin value: {sum(1 for x in runners if x['fin'] != 1 and x['tote'])} (a tote dividend is declared for the winner only)")
# races where the winner has all four prices; every runner of those races counts
ok = {x["race"] for x in win if x["tote"] and x["btote"] and x["bsp"]}
run = [x for x in runners if x["race"] in ok and x["bsp"]]
W = [x for x in run if x["fin"] == 1]
print(f"\ncomplete races: {len(ok)}; runners {len(run)}; winners {len(W)}")
print("\n## Winners: price paid against SP (median ratio)")
for k, nm in (("tote", "TAB tote"), ("btote", "best tote"), ("bsp", "Betfair SP")):
    r = [x[k] / x["sp"] for x in W]
    print(f"{nm:11s} / SP: median {st.median(r):.3f}, mean {st.mean(r):.3f}, bigger than SP {100*sum(v > 1.0001 for v in r)/len(r):.0f}%")
bands = [(1, 2), (2, 3), (3, 5), (5, 8), (8, 13), (13, 21), (21, 51), (51, 1e9)]
print("\n## $1 on every runner, banded by bookie SP (same runners for each column)")
print("| SP band | runners | winners | SP | TAB tote | best tote | BSP | BSP after 8% |\n|---|---|---|---|---|---|---|---|")
def roi(xs, k, comm=0.0):
    w = [x for x in xs if x["fin"] == 1]
    return (sum(1 + (x[k] - 1) * (1 - comm) for x in w) - len(xs)) / len(xs)
for lo, hi in bands + [(1, 1e9)]:
    xs = [x for x in run if lo <= x["sp"] < hi]
    if not xs: continue
    w = sum(x["fin"] == 1 for x in xs); lab = "all" if (lo, hi) == (1, 1e9) else f"${lo}-${hi:g}" if hi < 1e9 else f"${lo}+"
    print(f"| {lab} | {len(xs)} | {w} | {100*roi(xs,'sp'):+.1f}% | {100*roi(xs,'tote'):+.1f}% | {100*roi(xs,'btote'):+.1f}% | {100*roi(xs,'bsp'):+.1f}% | {100*roi(xs,'bsp',0.08):+.1f}% |")
print("\n## Winners: which paid most")
best = {"SP": 0, "TAB tote": 0, "best tote": 0, "Betfair SP (after 8%)": 0}
for x in W:
    c = {"SP": x["sp"], "TAB tote": x["tote"], "best tote": x["btote"], "Betfair SP (after 8%)": 1 + (x["bsp"] - 1) * 0.92}
    best[max(c, key=c.get)] += 1
for k, v in best.items(): print(f"{k}: {v} ({100*v/len(W):.0f}%)")
