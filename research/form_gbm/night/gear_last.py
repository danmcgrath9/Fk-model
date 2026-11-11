"""Founder, 11 Nov 2026 (Magna Sententia, Sandown Guineas): "got blinkers on first start last time, and I'm guessing rated
through the roof? By putting more emphasis on ratings when the gear is on would that help? Because it's been smashed in
betting". Does a big rating run in first-time gear repeat more than our price assumes?
For each runner: was its LAST start run in first-time blinkers (or any first-time gear), and how far did that run beat its
previous best? Then next-start winners against OUR chance (stage 2 walk-forward for 2026, the cross-fitted blend for
2025) and against BSP's, first starters out, races with a full BSP book and one winner.
    python3.13 gear_last.py   (night folder)"""
import numpy as np
import nl
D, ri, nR, date, won, bs = nl.D, nl.ri, nl.nR, nl.date, nl.won, nl.bs
P = np.where(date >= "2026-06-03", np.load("preds/s2_base_A.npy"), np.where(date >= "2026-01-01", np.load("preds/s2_base_B.npy"), np.load("p_oof_chal.npy"))).astype(float)
cols = list(D["cols"]); X = D["X"]; pf = list(D["past_fields"]); PP = D["P"]
fsr = X[:, cols.index("firstStarter")] == 1
okb = np.isfinite(bs) & (bs > 1); rok = (np.bincount(ri, weights=~okb, minlength=nR) == 0) & (np.bincount(ri, weights=won, minlength=nR) == 1)
ok = rok[ri] & ~fsr; qb = np.where(okb, 1 / bs, 0); qb = qb / np.maximum(np.bincount(ri, weights=qb, minlength=nR)[ri], 1e-9)
rid = D["race_id"].astype(str); hid = D["horse_id"].astype(str)
row = {(rid[ri[i]], hid[i]): i for i in range(len(ri))}
last = np.array([row.get((str(D["past_race_ids"][i][0]), hid[i]), -1) for i in range(len(ri))])
have = last >= 0
g = lambda c: np.where(have, X[np.maximum(last, 0), cols.index(c)].astype(float), np.nan)
blk1 = g("gd_blinkers_on1") > 0
any1 = np.zeros(len(ri), bool)
for c in ("gd_blinkers_on1", "gd_visors_on1", "gd_winkers_on1", "gd_tongue_on1", "gd_bandages_on1"): any1 |= g(c) > 0
r = pf.index("rating"); last_r = PP[:, 0, r].astype(float); prev_best = np.nanmax(np.where(np.isfinite(PP[:, 1:6, r]), PP[:, 1:6, r], -np.inf), 1)
jump = np.where(np.isfinite(last_r) & np.isfinite(prev_best), last_r - prev_best, np.nan)
print(f"runners whose last start is in the dataset: {have.sum()} of {len(ri)}; of them last start in first-time blinkers {int((blk1 & have).sum())}, any first-time gear {int((any1 & have).sum())}")
PER = (("Jul-Dec25", "2025-07-01", "2026-01-01"), ("Jan-2Jun26", "2026-01-01", "2026-06-03"), ("3Jun-9Nov26", "2026-06-03", "2027-01-01"))
def row_(lab, m):
    m = m & ok & have; n, w = int(m.sum()), int(won[m].sum()); eo, eb = float(P[m].sum()), float(qb[m].sum())
    gap = float(np.exp(np.mean(np.log(np.maximum(qb[m], 1e-6) / np.maximum(P[m], 1e-6))))) if n else np.nan
    per = " | ".join(f"{int(won[m & (date >= a) & (date < b)].sum())} v {P[m & (date >= a) & (date < b)].sum():.1f} ours / {qb[m & (date >= a) & (date < b)].sum():.1f} BSP" for _, a, b in PER)
    print(f"| {lab} | {n} | {w} | {eo:.1f} | {eb:.1f} | {w/max(eo,1e-9):.2f} | {w/max(eb,1e-9):.2f} | {gap:.2f}x | {per} |")
print("\n| last start | runners | won | we expected | BSP expected | won / ours | won / BSP | BSP rates them vs us (geo mean) | by era: won v ours / BSP |\n|---|---|---|---|---|---|---|---|---|")
row_("every runner with a known last start", np.ones(len(ri), bool))
row_("first-time blinkers, any rating", blk1)
row_("first-time blinkers, new peak by 3+", blk1 & (jump >= 3))
row_("first-time blinkers, new peak by 6+", blk1 & (jump >= 6))
row_("any first-time gear, new peak by 6+", any1 & (jump >= 6))
row_("NO gear change, new peak by 6+", ~any1 & (jump >= 6))
row_("NO gear change, new peak by 3+", ~any1 & (jump >= 3))
row_("first-time blinkers, no new peak", blk1 & (jump < 0))
