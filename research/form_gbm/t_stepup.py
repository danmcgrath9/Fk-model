"""First time up in trip, by the last start's sectionals: do they win more than Betfair SP says? (and than our model says)
python t_stepup.py  (run in the model dir: ds/model_ds.npz, p_oof_blend9.npy)
Step-up = today's trip at least 200m past the longest race (not trial) in the last 10. Last-start sections are lengths
against the class standard (positive = faster): last600 = the last 600m, to600 = start to the 600 (the mid race)."""
import numpy as np, collections
z = np.load("ds/model_ds.npz", allow_pickle=True); p = np.load("p_oof_blend9.npy")
pf = list(z["past_fields"]); P = z["P"]; ri = z["race_idx"]; dist = z["distance"][ri]
fin = z["finish"].astype(float); bsp = z["bsp"].astype(float)
ok = np.isfinite(bsp) & (bsp > 1)
qb = np.where(ok, 1 / np.where(ok, bsp, 1), 0)
sb = np.bincount(ri, weights=qb); qb = qb / np.where(sb[ri] > 0, sb[ri], 1)
sp_ = np.bincount(ri, weights=p); pm = p / sp_[ri]
D = P[:, :, pf.index("distance")]; T = P[:, :, pf.index("trial")]; F = P[:, :, pf.index("finish")]
race = (T == 0) & np.isfinite(F) & (D > 0)
longest = np.where(race, D, 0).max(1)
has = race.any(1)
first_run = race.argmax(1)  # newest race run
l6 = P[np.arange(len(P)), first_run, pf.index("last600")]; t6 = P[np.arange(len(P)), first_run, pf.index("to600")]
step = has & (dist >= longest + 200); same = has & (dist <= longest)
won = fin == 1
def row(name, m):
    m = m & ok
    n = m.sum(); w = won[m].sum(); eb = qb[m].sum(); em = pm[m].sum()
    roi = (np.where(won[m], (bsp[m] - 1) * 0.92, -1)).sum() / max(n, 1)
    print(f"| {name} | {n} | {w} | {eb:.1f} | {w/eb:.2f} | {w/em:.2f} | {100*roi:+.1f}% |")
print("| group | runners | won | BSP expected | A/E vs BSP | A/E vs our model | flat ROI at BSP (8% comm) |")
print("|---|---|---|---|---|---|---|")
row("all runners", has)
row("not stepping up", same)
row("first time up 200m+", step)
row("first time up 400m+", has & (dist >= longest + 400))
q = np.nanpercentile(l6[has & np.isfinite(l6)], [33, 67]); q2 = np.nanpercentile(t6[has & np.isfinite(t6)], [33, 67])
print(f"\nlast-start last600 terciles (lengths vs class): {q[0]:.2f} / {q[1]:.2f}; to600: {q2[0]:.2f} / {q2[1]:.2f}\n")
print("| group | runners | won | BSP expected | A/E vs BSP | A/E vs our model | flat ROI at BSP (8% comm) |")
print("|---|---|---|---|---|---|---|")
for lab, m in [("step-up, last600 top third", l6 > q[1]), ("step-up, last600 middle", (l6 > q[0]) & (l6 <= q[1])), ("step-up, last600 bottom third", l6 <= q[0]),
               ("step-up, to600 (mid) top third", t6 > q2[1]), ("step-up, both top third", (l6 > q[1]) & (t6 > q2[1])),
               ("step-up, last600 top third, BSP under $8", (l6 > q[1]) & (bsp < 8)), ("step-up, last600 top third, BSP $8+", (l6 > q[1]) & (bsp >= 8)),
               ("same/shorter trip, last600 top third", None)]:
    if m is None: row(lab, same & (l6 > q[1]) & np.isfinite(l6)); continue
    row(lab, step & m & np.isfinite(l6))
