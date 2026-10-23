"""The Betfair-side table from t_month_bsp.py, split into the two halves of the holdout by date, so a bucket only
counts if it holds in both. Same clean holdout (v10 stage-1 trees trained before 3 Jun 2026). python t_lay_halves.py"""
import numpy as np
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
p10 = np.load("v10_profit_preds.npz")["p10"]; o = z["open"].astype(float); bs = z["bsp"].astype(float); won = z["finish"] == 1
okr = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1)
m = race_ok[ri]
def norm(v, mask):
    s = np.bincount(ri, weights=np.where(mask, v, 0), minlength=nR); return np.where(mask, v / np.where(s[ri] > 0, s[ri], 1), np.nan)
pm = norm(p10, m); qb = norm(np.where(m, 1 / bs, 0), m); ratio = pm / qb
COMM = 0.08
dates_h = sorted(set(rdate[race_ok])); cut = dates_h[len(dates_h) // 2]
print(f"halves split at {cut}")
print("| ours / BSP (chance) | half | runners | wins | expected at BSP | A/E | flat 1u BACK at BSP | flat 1u LAY at BSP |\n|---|---|---|---|---|---|---|---|")
for lo_, hi_ in ((0, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0), (1.0, 1.25), (1.25, 1.6), (1.6, 2.0), (2.0, 99), (1.6, 99)):
    for hname, hm in (("early", date < cut), ("late", date >= cut)):
        g = m & hm & (ratio >= lo_) & (ratio < hi_); n = g.sum()
        if n == 0: continue
        exp = qb[g].sum(); w_ = won[g].sum()
        back = np.where(won[g], (bs[g] - 1) * (1 - COMM), -1.0).mean(); lay = np.where(won[g], -(bs[g] - 1), 1 - COMM).mean()
        print(f"| {lo_:.2f} to {hi_:.2f} | {hname} | {n} | {w_} | {exp:.1f} | {w_/exp:.2f} | {100*back:+.1f}% | {100*lay:+.1f}% |")
# lay at BSP where ours/BSP >= 1.6: by the BSP price band, both halves
print("\nLay at BSP, ours/BSP >= 1.6, by BSP price band\n| BSP band | half | runners | wins | expected | A/E | LAY ROI | liability per 1u lay (mean price-1) |\n|---|---|---|---|---|---|---|---|")
for lo_, hi_ in ((1, 4), (4, 8), (8, 15), (15, 30), (30, 1000)):
    for hname, hm in (("early", date < cut), ("late", date >= cut)):
        g = m & hm & (ratio >= 1.6) & (bs >= lo_) & (bs < hi_); n = g.sum()
        if n == 0: continue
        exp = qb[g].sum(); w_ = won[g].sum(); lay = np.where(won[g], -(bs[g] - 1), 1 - COMM).mean()
        print(f"| ${lo_}-${hi_} | {hname} | {n} | {w_} | {exp:.1f} | {w_/exp:.2f} | {100*lay:+.1f}% | {np.mean(bs[g]-1):.1f} |")
