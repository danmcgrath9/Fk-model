"""Tote v bookie SP v Betfair SP on every past run held in our stored fields (26 Oct 2026, the founder's tote question,
second pass). Each entry's raw pastEvents carry, per run, the benchmark's sp, bsp and bestToteWin and the finish, for
every runner (winners and losers) and every state. Runs are deduplicated by race and horse; trials and runs missing any
of the three prices are dropped. $1 on every runner in a band, settled at each price source; Betfair gross and after 8%.
Banded by bookie SP so each column is the same runners. DB only, no credits.
    python scripts/tote_vs_sp_past.py"""
from __future__ import annotations
import os, collections
import psycopg

q = """select p->>'raceId', coalesce(p->'horse'->>'id', p->>'horseId', e.horse_id::text), p->>'date', p->>'state',
          (p->>'finishPosition')::int, (p->'benchmark'->>'sp')::numeric, (p->'benchmark'->>'bsp')::numeric,
          (p->'benchmark'->>'bestToteWin')::numeric, coalesce((p->>'trial')::boolean, false)
       from fk.entries e, jsonb_array_elements(coalesce(e.raw->'pastEvents', '[]'::jsonb)) p
       where p ? 'benchmark'"""
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    rows = c.execute(q).fetchall()
seen, R = set(), []
for rid, hid, d, stt, fin, sp, bsp, tote, trial in rows:
    if trial or not rid or fin is None or not sp or not bsp or not tote: continue
    k = (rid, hid)
    if k in seen: continue
    seen.add(k); R.append(dict(race=rid, date=(d or "")[:10], state=stt, fin=fin, sp=float(sp), bsp=float(bsp), tote=float(tote)))
R = [x for x in R if x["sp"] > 1 and x["bsp"] > 1 and x["tote"] > 1]
print(f"{len(rows)} past-run rows, {len(R)} unique runs with all three prices, {sum(x['fin'] == 1 for x in R)} winners, "
      f"{len({x['race'] for x in R})} races, {min(x['date'] for x in R)} to {max(x['date'] for x in R)}")
print("by state:", dict(collections.Counter(x["state"] for x in R).most_common()))
def roi(xs, k, comm=0.0):
    return sum(((x[k] - 1) * (1 - comm)) if x["fin"] == 1 else -1 for x in xs) / len(xs)
bands = [(1, 2), (2, 3), (3, 5), (5, 8), (8, 13), (13, 21), (21, 51), (51, 1e9), (1, 1e9)]
def table(xs, title):
    print(f"\n## {title}\n| SP band | runs | winners | SP | tote | BSP | BSP after 8% | tote/SP median | BSP/SP median |\n|---|---|---|---|---|---|---|---|---|")
    for lo, hi in bands:
        s = [x for x in xs if lo <= x["sp"] < hi]
        if not s: continue
        md = lambda k: sorted(x[k] / x["sp"] for x in s)[len(s) // 2]
        lab = "all" if (lo, hi) == (1, 1e9) else f"${lo}-${hi:g}" if hi < 1e9 else f"${lo}+"
        print(f"| {lab} | {len(s)} | {sum(x['fin'] == 1 for x in s)} | {100*roi(s,'sp'):+.1f}% | {100*roi(s,'tote'):+.1f}% | "
              f"{100*roi(s,'bsp'):+.1f}% | {100*roi(s,'bsp',0.08):+.1f}% | {md('tote'):.2f} | {md('bsp'):.2f} |")
table(R, "All states")
for stt in ("VIC", "NSW", "QLD"):
    xs = [x for x in R if x["state"] == stt]
    if len(xs) > 2000: table(xs, stt)
print("\n## Winners: which paid most (BSP after 8%)")
W = [x for x in R if x["fin"] == 1]; c = collections.Counter()
for x in W:
    o = {"SP": x["sp"], "tote": x["tote"], "BSP after 8%": 1 + (x["bsp"] - 1) * 0.92}; c[max(o, key=o.get)] += 1
for k, v in c.most_common(): print(f"{k}: {v} ({100*v/len(W):.0f}%)")
print("\n## Overround (sum of 1/price in complete fields, median per race)")
by = collections.defaultdict(list)
for x in R: by[x["race"]].append(x)
for k in ("sp", "tote", "bsp"):
    o = sorted(sum(1 / x[k] for x in v) for v in by.values() if len(v) >= 6)
    print(f"{k}: median {100*o[len(o)//2]:.1f}% over {len(o)} races (only races with 6+ of their runners in our data)")
