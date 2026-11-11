"""How complete are the form lines? For every runner of a resulted VIC race since 1 Jul 2025: how many last-start
race-mates we know of, how many have a next run that counts (after the last start, before race day), and how many
are OPEN (no counting run known, and what we know of the horse stops before race day), plus the horses whose
Get Horse Form would close the most OPEN slots. DB and history files only, no credits.

    python scripts/racemate_gaps.py [--history history] [--top 3000]
See scripts/racemates.py for the rules."""
from __future__ import annotations

import argparse
import collections
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import racemates as RM  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--history", default="history")
ap.add_argument("--top", type=int, default=3000)
a = ap.parse_args()
t0 = time.time()
runs, fields, horizon, runners = RM.load(a.history)
RM.index_partial(runs, fields)
rows, benefit = RM.analyse(runs, fields, horizon, runners)
print(f"loaded in {time.time() - t0:.0f}s: {len(runs)} horses with runs, {len(fields)} races held whole, {len(rows)} runners with a last start")

mean = lambda v: sum(v) / len(v) if v else float("nan")
whole = [r for r in rows if r[4]]
print(f"\nlast start is a race held whole: {len(whole)} of {len(rows)} ({len(whole) / len(rows):.0%})")
print("| runners | race-mates known | next run counting | open |")
print("|---|---|---|---|")
for lab_, rr in (("all", rows), ("last start held whole", whole), ("last start not held whole", [r for r in rows if not r[4]])):
    print(f"| {lab_} ({len(rr)}) | {mean([r[1] for r in rr]):.2f} | {mean([r[2] for r in rr]):.2f} | {mean([r[3] for r in rr]):.2f} |")
print("\nby month: counting / open per runner")
by = collections.defaultdict(list)
for r in rows:
    by[r[0][:7]].append(r)
for m in sorted(by):
    rr = by[m]
    print(f"  {m}  {mean([r[2] for r in rr]):.2f} / {mean([r[3] for r in rr]):.2f}  ({len(rr)} runners)")

tot = sum(benefit.values())
print(f"\nOPEN race-mate slots: {tot}, across {len(benefit)} horses")
ranked = benefit.most_common()
cum = 0
for i, (h, n) in enumerate(ranked, 1):
    cum += n
    if i in (100, 250, 500, 1000, 1500, 2000, 3000, 4000, 6000) or i == len(ranked):
        print(f"  top {i:5} horses ({2 * i:6} credits): {cum:6} slots ({cum / tot:.0%})")
last = collections.Counter()
for h, _ in ranked[:a.top]:
    rs = runs.get(h, ())
    last[(rs[-1][0][:7] if rs else "none")] += 1
print(f"\ntop {a.top}: month of the latest run we hold")
for m in sorted(last):
    print(f"  {m}  {last[m]}")
