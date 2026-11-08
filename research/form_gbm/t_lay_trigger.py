"""Lay trigger for the most PROFIT, not the best ROI (8 Nov 2026, founder: "we don't care as much as ROI as just money";
"Yep run"). v10 holdout from 3 Jun, two halves by date; lay 1u at BSP when BSP is in the band and at least X times our
price, first starters out, 8% commission, $200 a lay. Totals per trigger, and each slice between triggers on its own
(the lays a lower trigger ADDS), because more profit only comes from slices that are positive in both halves."""
import numpy as np
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
p10 = np.load("v10_profit_preds.npz")["p10"]; bs = z["bsp"].astype(float); won = z["finish"] == 1
cols = list(z["cols"]); fs = z["X"][:, cols.index("firstStarter")] == 1
ok = np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=ok.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1)
m = race_ok[ri]; s = np.bincount(ri, weights=np.where(m, p10, 0), minlength=nR); pm = np.where(m, p10 / np.where(s[ri] > 0, s[ri], 1), np.nan); ours = 1 / pm
H1 = np.array([d < "2026-08-01" for d in date]); pl = np.where(won, -(bs - 1), 0.92); ratio = bs / ours
X = (1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 2.0, 2.5)
def cell(sel):
    n = int(sel.sum()); w = int(won[sel].sum()); e = float(np.sum(1 / bs[sel])); p = float(pl[sel].sum())
    return n, w, e, p
for lo, hi in ((8, 12), (15, 40)):
    base = m & ~fs & (bs >= lo) & (bs <= hi)
    print(f"\n=== ${lo}-${hi} band: lay when BSP >= X x ours")
    print("  X     | all: lays won(BSP said) units  $          | Jun-Jul units | Aug-Oct units")
    for x in X:
        sel = base & (ratio >= x); n, w, e, p = cell(sel); _, _, _, p1 = cell(sel & H1); _, _, _, p2 = cell(sel & ~H1)
        print(f"  {x:<4}  | {n:4d} {w:3d} ({e:5.1f}) {p:+8.2f}u ${p*200:+9,.0f} | {p1:+8.2f}u | {p2:+8.2f}u")
    print("  slices (what each step down adds):")
    edges = list(X) + [99]
    for a, b in zip(edges[:-1], edges[1:]):
        sel = base & (ratio >= a) & (ratio < b); n, w, e, p = cell(sel); _, _, _, p1 = cell(sel & H1); _, _, _, p2 = cell(sel & ~H1)
        print(f"   {a}-{b if b < 99 else '+':<4} {n:4d} lays {w:3d} won ({e:5.1f}) {p:+8.2f}u  halves {p1:+7.2f} / {p2:+7.2f}")
