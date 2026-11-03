"""Laying short ones we rate much longer (3 Nov 2026, founder: "our favourites that we have at like 2x the price? Or
favourites we have between $4-$7 that are 1.6x the price?"). v10 holdout from 3 Jun, lay 1u at BSP, 8% commission,
split into the two halves of the holdout by date; a cell only counts if both halves agree."""
import numpy as np
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
p10 = np.load("v10_profit_preds.npz")["p10"]; o = z["open"].astype(float); bs = z["bsp"].astype(float); won = z["finish"] == 1
okr = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1)
m = race_ok[ri]
s = np.bincount(ri, weights=np.where(m, p10, 0), minlength=nR); pm = np.where(m, p10 / np.where(s[ri] > 0, s[ri], 1), np.nan); ours = 1 / pm
# the BSP favourite of each race
minb = np.full(nR, np.inf)
for i in np.where(m)[0]: minb[ri[i]] = min(minb[ri[i]], bs[i])
fav = m & (bs <= minb[ri] + 1e-9)
cut = sorted(set(rdate[race_ok]))[len(set(rdate[race_ok])) // 2]
print("| cut | half | lays | winners | BSP expected | A/E | lay 1u at BSP | mean liability |\n|---|---|---|---|---|---|---|---|")
def row(name, g):
    for h, hm in (("early", date < cut), ("late", date >= cut)):
        gg = g & hm; n = gg.sum()
        if n == 0: print(f"| {name} | {h} | 0 | | | | | |"); continue
        exp = (1 / bs[gg]).sum(); w = won[gg].sum(); pl = np.where(won[gg], -(bs[gg] - 1), 0.92).sum()
        print(f"| {name} | {h} | {n} | {w} | {exp:.1f} | {w/exp:.2f} | {pl:+.1f}u ({100*pl/n:+.0f}%) | {np.mean(bs[gg]-1):.1f}u |")
row("BSP favourite, ours >= 2x BSP", fav & (ours >= 2 * bs))
row("BSP favourite, ours >= 1.6x BSP", fav & (ours >= 1.6 * bs))
row("BSP favourite $4-$7, ours >= 1.6x", fav & (bs >= 4) & (bs <= 7) & (ours >= 1.6 * bs))
row("any runner BSP $4-$7, ours >= 1.6x", m & (bs >= 4) & (bs <= 7) & (ours >= 1.6 * bs))
row("any runner BSP $4-$7, ours >= 2x", m & (bs >= 4) & (bs <= 7) & (ours >= 2 * bs))
row("any runner BSP under $4, ours >= 1.6x", m & (bs < 4) & (ours >= 1.6 * bs))
row("any runner BSP $7-$15, ours >= 1.6x", m & (bs >= 7) & (bs < 15) & (ours >= 1.6 * bs))
row("any runner BSP $7-$15, ours >= 2x", m & (bs >= 7) & (bs < 15) & (ours >= 2 * bs))
