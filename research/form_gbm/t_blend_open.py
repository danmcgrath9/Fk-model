"""Benter's last step, never tested here: combine our price with the OPENING market price by a fitted logit blend,
and see what it does to (a) distance from BSP, (b) picking winners, (c) the bets we would place at the open.
Holdout = races from 2026-05-06. Stage-2 v6 is refitted on the races before the cut (3 seeds, live rounds) and
predicts the holdout; blend weights (two numbers) are cross-fitted on halves of the holdout by date, so every holdout
figure is out of sample. Run in the model dir: python3.13 t_blend_open.py"""
import numpy as np, bench as b, lightgbm as lgb, gbm, stage2, sys, os
from scipy.optimize import minimize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stake_rule
D = b.load(); p = np.load("p_oof_blend9.npy"); ri = D["race_idx"]; nR = D["n_races"]; rd = D["date"][ri]
Z = np.load("ds/model_ds.npz", allow_pickle=True); openp = Z["open"].astype(float); fin = Z["finish"].astype(float); bsp = Z["bsp"].astype(float)
cut = "2026-05-06"; hold = rd >= cut
# ---- stage-2 v6 features, exactly as the live training builds them
res = np.clip(np.log(np.maximum(D["q"], 1e-4)) - np.log(np.maximum(p, 1e-4)), -3, 3)
jw = np.nan_to_num(D["X"][:, D["colidx"]["jockeyForm_lastTwelveMonthWinPercentage"]].astype(float), nan=0)
lastj = np.array([next((x for x in row if x), "") for row in D["past_jockeys"].astype(str)])
E = stage2.encodings(rd, D["horse_id"], D["trainer"], D["jockey"], D["sire"], D["track"][ri], res)
A, Bk, C = stage2.extras(rd, ri, D["horse_id"], D["trainer"], D["jockey"], lastj, p, jw, res)
X, L = stage2.design(E, p, ri, nR); SEC = stage2.sections(np.load("S_hist.npy"), np.load("S_fields.npy", allow_pickle=True), D["P"], D["past_fields"], ri, nR)
TV = stage2.travel(D["training_location"], D["track"][ri], ri, nR)
lid, lf = stage2.last_start(D["P"], D["past_fields"], D["past_race_ids"])
CO = stage2.collateral(D["race_id"][ri], D["date"][ri], D["horse_id"], D["finish"], D["q"], lid, D["date"][ri], D["horse_id"], lf, ri, nR)
X = np.column_stack([X, A, Bk, C, SEC, stage2.trials(D["P"], D["past_fields"], ri), TV, CO])
# ---- fit on dev races only (the encodings above are rolling, so they carry no holdout leak), predict the holdout
dev_r = np.unique(ri[~hold]); keep = ~hold
P = dict(learning_rate=0.03, num_leaves=7, min_data_in_leaf=200, feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10, verbose=-1, objective="none", num_threads=4)
# remap race ids on the dev subset for the objective
ri_dev = np.unique(ri[keep], return_inverse=True)[1]
f = gbm.make_obj(ri_dev, ri_dev.max() + 1, D["q"][keep])
preds = []
for s in range(3):
    P["seed"] = s; bst = lgb.Booster(params=P, train_set=lgb.Dataset(X[keep], init_score=L[keep]))
    for _ in range(400): bst.update(fobj=f)
    preds.append(bst.predict(X))
s2 = L + np.mean(preds, 0)
p2 = b.softmax_races(s2)  # stage-2 v6 chance, out of sample on the holdout
def norm_race(v):
    s = np.bincount(ri, weights=v, minlength=nR); return v / np.where(s[ri] > 0, s[ri], 1)
okopen = np.isfinite(openp) & (openp > 1)
qo = np.where(okopen, 1 / np.where(okopen, openp, 1), np.nan)
# races where every runner has an open price, a BSP and a winner: the test set
rok = np.ones(nR, bool)
for v in (okopen, np.isfinite(bsp) & (bsp > 1)): rok &= np.bincount(ri, weights=~v, minlength=nR) == 0
rok &= np.bincount(ri, weights=fin == 1, minlength=nR) == 1
m = rok[ri] & hold
qo = norm_race(np.nan_to_num(qo)); q = D["q"]
def blend(a, bo, lp, lo):
    z = a * lp + bo * lo; z = z - np.array([z[ri == r].max() if (ri == r).any() else 0 for r in range(nR)])[ri] if False else z
    e = np.exp(z - 20); return norm_race(e)
lp2 = np.log(np.maximum(p2, 1e-6)); lo = np.log(np.maximum(qo, 1e-6))
def fit(mask, target):
    """target 'win': maximise winner log-likelihood; 'bsp': minimise KL(BSP || blend)."""
    def loss(w):
        bl = blend(w[0], w[1], lp2, lo)[mask]
        if target == "win": return -np.sum(np.log(np.maximum(bl[fin[mask] == 1], 1e-9)))
        return np.sum(q[mask] * np.log(q[mask] / np.maximum(bl, 1e-9)))
    return minimize(loss, [0.7, 0.5], method="Nelder-Mead").x
dates_h = np.unique(rd[m]); mid = dates_h[len(dates_h) // 2]
halves = [m & (rd < mid), m & (rd >= mid)]
out = {}
for target in ("win", "bsp"):
    bl = np.zeros(len(ri)); ws = []
    for i in (0, 1):
        w = fit(halves[1 - i], target); ws.append(w); bl[halves[i]] = blend(w[0], w[1], lp2, lo)[halves[i]]
    out[target] = (bl, ws)
def kl(pp): return float(np.sum(q[m] * np.log(q[m] / np.maximum(pp[m], 1e-9))) / rok[hold[ri] & rok[ri]].size if False else np.sum(q[m] * np.log(q[m] / np.maximum(pp[m], 1e-9))) / len(np.unique(ri[m])))
def ll(pp): w = m & (fin == 1); return float(-np.mean(np.log(np.maximum(pp[w], 1e-9))))
nrace = len(np.unique(ri[m]))
print(f"holdout test set: {nrace} races, {m.sum()} runners (every runner with an open price and a BSP)\n")
print("| price | KL to BSP | winner log loss |"); print("|---|---|---|")
for lab, pp in [("opening market", qo), ("stage-1 OOF (ours, before stage 2)", p), ("stage-2 v6 (ours)", p2), ("blend fitted to winners", out["win"][0]), ("blend fitted to BSP", out["bsp"][0])]:
    print(f"| {lab} | {kl(pp):.4f} | {ll(pp):.4f} |")
print(f"\nblend weights (ours, open), fitted to winners: {[list(np.round(w,2)) for w in out['win'][1]]}; to BSP: {[list(np.round(w,2)) for w in out['bsp'][1]]}")
# ---- bets at the open under the live rules, model price vs blended price for selection
field = np.bincount(ri, minlength=nR)
def bets(pp, label):
    rows = []
    for i in np.where(m)[0]:
        pr = pp[i]; o = openp[i]
        if not (1.6 <= 1 / pr <= 15): continue
        if not (o >= 1.2 / pr and o < 3 / pr): continue
        st = stake_rule.stake(pr, o, False, int(field[ri[i]]))
        if st <= 0: continue
        rows.append((o, bsp[i], fin[i] == 1, st, pr))
    n = len(rows); w = sum(r[2] for r in rows)
    flat_o = sum((r[0] - 1) if r[2] else -1 for r in rows); flat_b = sum((r[1] - 1) * 0.92 if r[2] else -1 for r in rows)
    st_o = sum(r[3] * ((r[0] - 1) if r[2] else -1) for r in rows); st_t = sum(r[3] for r in rows)
    exp_w = sum(r[4] for r in rows)
    print(f"| {label} | {n} | {w} ({100*w/max(n,1):.1f}%) | {exp_w:.1f} | {100*flat_o/max(n,1):+.1f}% | {100*flat_b/max(n,1):+.1f}% | {st_t:.0f}u / {st_o:+.0f}u ({100*st_o/max(st_t,1):+.1f}%) |")
print("\n| selection price | bets | won (strike) | expected wins by that price | flat ROI at open | flat ROI at BSP (8% comm) | live stakes: staked / P&L |"); print("|---|---|---|---|---|---|---|")
bets(p2, "stage-2 v6 (as live)"); bets(out["win"][0], "blend, winner-fitted"); bets(out["bsp"][0], "blend, BSP-fitted")
np.savez("blend_hold.npz", p2=p2, bl_win=out["win"][0], bl_bsp=out["bsp"][0], m=m, qo=qo)
# ---- by opening-price band, blended (BSP-fitted) selection: where do the winners come from?
pp = out["bsp"][0]
print("\n| open price band (blend selection) | bets | won (strike) | flat ROI at open | flat ROI at BSP (8% comm) | live stakes P&L |"); print("|---|---|---|---|---|---|")
for lo_, hi_, lab in [(1.0, 4.0, "$1.60-$4"), (4.0, 8.0, "$4-$8"), (8.0, 15.0, "$8-$15"), (15.0, 999.0, "$15+")]:
    rows = []
    for i in np.where(m)[0]:
        pr = pp[i]; o = openp[i]
        if not (1.6 <= 1 / pr <= 15) or not (o >= 1.2 / pr and o < 3 / pr) or not (lo_ <= o < hi_): continue
        st = stake_rule.stake(pr, o, False, int(field[ri[i]]))
        if st > 0: rows.append((o, bsp[i], fin[i] == 1, st))
    n = len(rows); w = sum(r[2] for r in rows)
    if n: print(f"| {lab} | {n} | {w} ({100*w/n:.1f}%) | {100*sum((r[0]-1) if r[2] else -1 for r in rows)/n:+.1f}% | {100*sum((r[1]-1)*0.92 if r[2] else -1 for r in rows)/n:+.1f}% | {sum(r[3]*((r[0]-1) if r[2] else -1) for r in rows):+.0f}u on {sum(r[3] for r in rows):.0f}u |")
# the same with the model's own price, for the comparison
pp = p2
print("\n| open price band (model selection, as live) | bets | won (strike) | flat ROI at open | flat ROI at BSP | live stakes P&L |"); print("|---|---|---|---|---|---|")
for lo_, hi_, lab in [(1.0, 4.0, "$1.60-$4"), (4.0, 8.0, "$4-$8"), (8.0, 15.0, "$8-$15"), (15.0, 999.0, "$15+")]:
    rows = []
    for i in np.where(m)[0]:
        pr = pp[i]; o = openp[i]
        if not (1.6 <= 1 / pr <= 15) or not (o >= 1.2 / pr and o < 3 / pr) or not (lo_ <= o < hi_): continue
        st = stake_rule.stake(pr, o, False, int(field[ri[i]]))
        if st > 0: rows.append((o, bsp[i], fin[i] == 1, st))
    n = len(rows); w = sum(r[2] for r in rows)
    if n: print(f"| {lab} | {n} | {w} ({100*w/n:.1f}%) | {100*sum((r[0]-1) if r[2] else -1 for r in rows)/n:+.1f}% | {100*sum((r[1]-1)*0.92 if r[2] else -1 for r in rows)/n:+.1f}% | {sum(r[3]*((r[0]-1) if r[2] else -1) for r in rows):+.0f}u on {sum(r[3] for r in rows):.0f}u |")
