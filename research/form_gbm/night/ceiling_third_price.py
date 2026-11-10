"""The ceiling on a third price: the walk-forward THREE-MODEL blend from queue 3 (every member trained inside the fold,
live weights), the closest thing here to the live stage 1. Plain live rules at Form King's open (nl.run: edge 1.2,
$1.60-$15, three steps, flat 16c; first starters IN, no blocks), four periods.
    python3.13 ceiling_third_price.py   (night folder, after queue3.py)"""
import numpy as np
import nl
P = {f: np.load(f"preds/m_live_blend_{f}.npy").astype(float) for f in "AB"}
print("| ceiling | " + " | ".join(n for f in "BA" for n, _, _ in nl.PERIODS[f][:2]) + " | all four |\n|---|---|---|---|---|---|")
rows = {}
for c in (3.0, 4.0, 6.0, 10.0, 1e9):
    cells = []; tot = [0, 0, 0.0, 0.0]
    for f in "BA":
        for name, lo, hi in nl.PERIODS[f][:2]:
            m = (nl.date >= lo) & (nl.date < hi); n, w, st, pl = nl.run(P[f], m, ceil=c); cells.append(f"{pl:+.0f}u ({n})"); tot = [tot[0] + n, tot[1] + w, tot[2] + st, tot[3] + pl]
    rows[c] = tot; print(f"| {'none' if c > 100 else f'{c:g}x'} | " + " | ".join(cells) + f" | {tot[3]:+.0f}u on {tot[0]} bets, {tot[1]} won ({100*tot[3]/tot[2]:+.0f}%) |", flush=True)
a, b_ = rows[3.0], rows[6.0]
print(f"6x against 3x: {b_[0]-a[0]} more bets, {b_[1]-a[1]} more winners, {b_[3]-a[3]:+.0f}u ({100*(b_[3]/a[3]-1):+.0f}%)")
