"""The three books on the v10 holdout by month, 3 Jun to 8 Oct 2026 (stops the day before going live, so the live weeks
are not counted twice): the open book with the live staking (x2 at 2.2x under $8, 10u cap) at the open less 7%; the lay
rule (BSP $15-$40, >= 1.6x ours, 1u at BSP, 8% comm); the favourite-back rule (BSP favourite $4-$7, ours >= 1.6x BSP, 1u
at BSP, 8% comm)."""
import numpy as np, collections
src = open("t_all_rules.py").read().split('summ(plan(pm0), "all rules')[0]
exec(src)
CUT = "2026-10-08"
b = plan(pmS); idx = np.array([i for i, _ in b]); st0 = np.array([s for _, s in b])
e = pmS[idx] * o[idx]; ours_ = 1 / pmS[idx]; big = (e >= 2.2) & (ours_ < 8); st = np.minimum(10, np.where(big, st0 * 2, st0))
plo = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st)
mo = collections.OrderedDict()
def add(k, col, v, s=0.0):
    a = mo.setdefault(k, {"open": 0.0, "open_st": 0.0, "lay": 0.0, "lay_n": 0, "fav": 0.0, "fav_n": 0}); a[col] += v
    if col == "open": a["open_st"] += s
for j, i in enumerate(idx):
    if dd[i] <= CUT: add(dd[i][:7], "open", plo[j], st[j])
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
p10 = np.load("v10_profit_preds.npz")["p10"]; oo = z["open"].astype(float); bs = z["bsp"].astype(float); ww = z["finish"] == 1
okr = np.isfinite(oo) & (oo > 1) & np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (rdate <= CUT) & (np.bincount(ri, weights=ww.astype(float), minlength=nR) >= 1)
m = race_ok[ri]; s = np.bincount(ri, weights=np.where(m, p10, 0), minlength=nR); pm = np.where(m, p10 / np.where(s[ri] > 0, s[ri], 1), np.nan); ours = 1 / pm
gl = m & (bs >= 15) & (bs <= 40) & (bs >= 1.6 * ours)
for i in np.where(gl)[0]: add(date[i][:7], "lay", -(bs[i] - 1) if ww[i] else 0.92); mo[date[i][:7]]["lay_n"] += 1
minb = np.full(nR, np.inf)
for i in np.where(m)[0]: minb[ri[i]] = min(minb[ri[i]], bs[i])
gf = m & (bs <= minb[ri] + 1e-9) & (bs >= 4) & (bs < 7) & (ours >= 1.6 * bs)
for i in np.where(gf)[0]: add(date[i][:7], "fav", (bs[i] - 1) * 0.92 if ww[i] else -1.0); mo[date[i][:7]]["fav_n"] += 1
print("| month | open u | open $50 | lays n | lays u | lays $200 | faves n | faves u | faves $500 | total $ |")
T = collections.Counter()
for k in sorted(mo):
    a = mo[k]; d = a["open"] * 50 + a["lay"] * 200 + a["fav"] * 500
    for c in ("open", "open_st", "lay", "lay_n", "fav", "fav_n"): T[c] += a[c]
    T["d"] += d
    print(f"| {k} | {a['open']:+.0f}u | ${a['open']*50:+,.0f} | {a['lay_n']} | {a['lay']:+.1f}u | ${a['lay']*200:+,.0f} | {a['fav_n']} | {a['fav']:+.1f}u | ${a['fav']*500:+,.0f} | ${d:+,.0f} |")
print(f"| TOTAL | {T['open']:+.0f}u ({100*T['open']/T['open_st']:+.0f}%) | ${T['open']*50:+,.0f} | {T['lay_n']:.0f} | {T['lay']:+.1f}u | ${T['lay']*200:+,.0f} | {T['fav_n']:.0f} | {T['fav']:+.1f}u | ${T['fav']*500:+,.0f} | ${T['d']:+,.0f} |")
