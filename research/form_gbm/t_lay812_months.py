"""The $8-$12 lay band (8 Nov 2026, founder: "What profit does that add since June"): v10 holdout from 3 Jun, lay 1u at BSP
when BSP is $8-$12 and at least 1.6x our price, first starters out, 8% commission, $200 a lay, month by month; the
$15-$40 band beside it on the same footing."""
import numpy as np, collections
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
p10 = np.load("v10_profit_preds.npz")["p10"]; bs = z["bsp"].astype(float); won = z["finish"] == 1
cols = list(z["cols"]); fs = z["X"][:, cols.index("firstStarter")] == 1
ok = np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=ok.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1)
m = race_ok[ri]; s = np.bincount(ri, weights=np.where(m, p10, 0), minlength=nR); pm = np.where(m, p10 / np.where(s[ri] > 0, s[ri], 1), np.nan); ours = 1 / pm
print(f"holdout {min(date[m])} to {max(date[m])}")
for lo, hi in ((8, 12), (15, 40)):
    sel = m & ~fs & (bs >= lo) & (bs <= hi) & (bs >= 1.6 * ours)
    pl = np.where(won, -(bs - 1), 0.92); mo = collections.defaultdict(lambda: [0, 0, 0.0])
    for i in np.where(sel)[0]:
        a = mo[date[i][:7]]; a[0] += 1; a[1] += won[i]; a[2] += pl[i]
    print(f"\n${lo}-${hi}: {sel.sum()} lays, {won[sel].sum()} winners (BSP said {np.sum(1/bs[sel]):.1f}), {pl[sel].sum():+.2f}u = ${pl[sel].sum()*200:+,.0f} at $200")
    for k in sorted(mo): n, w, p = mo[k]; print(f"  {k}  {n:4d} lays {w:3d} won {p:+7.2f}u  ${p*200:+9,.0f}")
