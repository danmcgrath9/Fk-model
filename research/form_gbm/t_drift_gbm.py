"""Why prices move from the open to BSP, and can we price closer to BSP? (18 Oct 2026, founder: "a backtest with the
data we pulled this weekend, for getting closer to bsp, always keeping the model the sharpest etc and looking for betting
angles / why bsp is moving").

Holdout only (races from 3 Jun 2026, where v10's stage-1 price p10 is out of sample), races where every runner has a
Form King opening price and a BSP. Drift y = log(BSP chance / opening chance), both normalised within the race.
Two date halves, each predicted by a model trained on the other (cross-fitted, so no row is scored by a model that saw it).

  1. How much of the move can be predicted: R2 of y from our model's disagreement with the open alone, from the form
     inputs alone (GBM), and from both.
  2. Sharpness: KL to BSP and winner log loss for the open, our price, the live-style blend, and the predicted BSP
     (open moved by the predicted drift).
  3. What drives it: the GBM's top inputs, with the drift of their top and bottom fifths.
  4. Angles: value-at-open bets (the live rules at the open) split by predicted drift, at the open after the 16c
     deduction and at BSP.

    python3.13 t_drift_gbm.py"""
import numpy as np, lightgbm as lgb, bench as b

import os
if os.environ.get("PRICE") == "stage2":   # the live-style price: stage 2 v6 refitted before 6 May (t_blend_open.py's blend_hold.npz)
    D = b.load(os.environ.get("DS", "../model_v9/model_ds.npz")); z = np.load("blend_hold.npz"); p10 = z["p2"]
    hold = (D["date"][D["race_idx"]] >= "2026-05-06") & np.isfinite(p10) & (p10 > 0); print("price: stage 2 v6 (live-style), holdout from 6 May")
else:
    D = b.load("ds/model_ds_v10.npz")
    P = np.load("v10_profit_preds.npz"); p10 = P["p10"]; hold = P["hold"]
ri = D["race_idx"]; nR = D["n_races"]; cols = [str(c) for c in D["cols"]]
op = np.asarray(D["open"], float); bs = np.asarray(D["bsp"], float); won = np.asarray(D["finish"], float) == 1
okp = lambda x: np.isfinite(x) & (x > 1)
cnt = np.bincount(ri, minlength=nR); full = np.bincount(ri, weights=(okp(op) & okp(bs)).astype(float), minlength=nR) == cnt
racedate = np.asarray(D["date"]); rmask = full & np.isin(np.arange(nR), np.unique(ri[hold]))
m = rmask[ri]
def norm(v, mask):
    s = np.bincount(ri, weights=np.where(mask, v, 0), minlength=nR); return np.where(mask, v / np.where(s[ri] > 0, s[ri], 1), np.nan)
qo = norm(1 / np.where(okp(op), op, 2), m); qb = norm(1 / np.where(okp(bs), bs, 2), m)
pm = norm(p10, m)
y = np.log(qb) - np.log(qo); dis = np.log(pm) - np.log(qo)
idx = np.where(m)[0]
dates = racedate[ri[idx]]; ud = sorted(set(dates)); cut = ud[len(ud) // 2]; half = (dates >= cut).astype(int)
print(f"holdout races with every open and BSP: {rmask.sum()}, runners {len(idx)}, halves split at {cut}")

X = np.asarray(D["X"], np.float32)[idx]
fld = cnt[ri[idx]].astype(np.float32)
Xa = np.column_stack([X, np.log(qo[idx]), fld]); na = cols + ["open_chance_log", "field"]
Xb = np.column_stack([Xa, dis[idx]]); nb = na + ["OUR_MODEL_vs_open"]
Y = y[idx]
params = dict(objective="regression", learning_rate=0.03, num_leaves=15, min_data_in_leaf=80, feature_fraction=0.3,
              bagging_fraction=0.8, bagging_freq=1, lambda_l2=10, verbose=-1)
def crossfit(XX, names, rounds=600):
    pred = np.zeros(len(Y)); gains = np.zeros(XX.shape[1])
    for h in (0, 1):
        tr, te = half != h, half == h
        bst = lgb.train(params, lgb.Dataset(XX[tr], Y[tr], feature_name=[f"c{j}" for j in range(len(names))]), rounds)
        pred[te] = bst.predict(XX[te]); gains += bst.feature_importance("gain")
    return pred, gains
r2 = lambda yh: 1 - np.mean((Y - yh) ** 2) / np.mean((Y - Y.mean()) ** 2)
# 1. linear on our disagreement alone (fit on the other half)
lin = np.zeros(len(Y))
for h in (0, 1):
    tr, te = half != h, half == h
    A = np.column_stack([np.ones(tr.sum()), dis[idx][tr]]); c = np.linalg.lstsq(A, Y[tr], rcond=None)[0]
    lin[te] = c[0] + c[1] * dis[idx][te]
    print(f"half {h}: drift = {c[0]:+.3f} + {c[1]:.3f} x (log ours/open)  (fit on the other half)")
ga, gna = crossfit(Xa, na); gb, gnb = crossfit(Xb, nb)
print(f"\n## 1. How much of the open-to-BSP move is predictable (R2, cross-fitted)\n")
print(f"| predictor | R2 |\n|---|---|\n| our price vs the open, straight line | {r2(lin):.3f} |\n| form inputs + open (GBM) | {r2(ga):.3f} |\n| form inputs + open + our price (GBM) | {r2(gb):.3f} |")
fav = qo[idx]; sd = np.std(Y)
print(f"spread of the move: sd of log(BSP/open chance) {sd:.3f}; median |move| {np.median(np.abs(Y)):.3f}")

# 2. sharpness
R = ri[idx]
def race_norm(logit):
    mx = np.full(nR, -np.inf); np.maximum.at(mx, R, logit); e = np.exp(logit - mx[R]); return e / np.bincount(R, weights=e, minlength=nR)[R]
QB = qb[idx]; W = won[idx]
def kl(q):
    return np.sum(QB * (np.log(QB) - np.log(q))) / rmask.sum()
def ll(q):
    return -np.sum(np.log(q[W])) / W.sum()
QO = qo[idx]; PM = pm[idx]
# blend weights fitted on the other half (a, c on log ours, log open)
def fit_blend(cands):
    out = np.zeros(len(Y)); wts = []
    for h in (0, 1):
        tr, te = half != h, half == h
        best = None
        for a in np.arange(0.0, 1.31, 0.05):
            for c in np.arange(0.0, 1.31, 0.05):
                q = race_norm(a * cands[0] + c * cands[1])
                s = np.sum((QB * (np.log(QB) - np.log(q)))[tr])
                if best is None or s < best[0]: best = (s, a, c)
        out[te] = (best[1] * cands[0] + best[2] * cands[1])[te]; wts.append(best[1:])
    return race_norm(out), wts
BL, wb = fit_blend((np.log(PM), np.log(QO)))
PB = race_norm(np.log(QO) + gb); PA = race_norm(np.log(QO) + ga)
BL2, wb2 = fit_blend((np.log(BL), np.log(PB)))
print(f"\n## 2. Sharpness on {rmask.sum()} holdout races (lower is better)\n")
print("| price | KL to BSP | winner log loss |\n|---|---|---|")
for lab_, q in (("opening market", QO), (os.environ.get("PRICE", "v10 stage 1") + " (our model)", PM), (f"blend ours + open (weights {wb[0][0]:.2f}/{wb[0][1]:.2f}, {wb[1][0]:.2f}/{wb[1][1]:.2f})", BL),
                ("predicted BSP: open moved by the form-only drift model", PA), ("predicted BSP: open moved by the drift model with our price", PB),
                (f"blend of the two above (weights {wb2[0][0]:.2f}/{wb2[0][1]:.2f}, {wb2[1][0]:.2f}/{wb2[1][1]:.2f})", BL2), ("BSP itself", QB)):
    print(f"| {lab_} | {kl(q):.4f} | {ll(q):.4f} |")

# 3. drivers
order = np.argsort(-gnb)[:20]
print("\n## 3. What moves the price (top 20 inputs by gain in the drift model with our price)\n")
print("| input | share of gain | median move, bottom fifth | median move, top fifth | runners with a value |\n|---|---|---|---|---|")
for j in order:
    v = Xb[:, j]; ok = np.isfinite(v)
    if ok.sum() < 200: continue
    lo, hi = np.nanquantile(v, [0.2, 0.8])
    bot = ok & (v <= lo); top = ok & (v >= hi)
    if lo == hi: bot = ok & (v < lo); top = ok & (v > lo)
    f = lambda s: f"x{np.exp(np.median(Y[s])):.2f}" if s.sum() > 30 else "-"
    print(f"| {nb[j]} | {gnb[j] / gnb.sum():.1%} | {f(bot)} | {f(top)} | {ok.sum()} |")
print("(move = BSP chance / opening chance; above 1 = the market firmed, below 1 = it drifted)")

# 4. angles: value-at-open bets under the live rules, split by predicted drift
oo = op[idx]; ours = 1 / BL; ded = 0.16
val = (BL * oo >= 1.2) & (ours >= 1.6) & (ours <= 15) & (oo <= 3 * ours)
ret_open = np.where(W, 1 + (oo - 1) * (1 - ded), 0) - 1; ret_bsp = np.where(W, bs[idx], 0) - 1
pf = PB / QO  # predicted firming of the bet's chance
print(f"\n## 4. Value-at-open bets ({val.sum()}) split by the drift model's forecast\n")
print("| forecast | bets | strike | flat at the open, 16c deduction | flat at BSP | median open/BSP | actually firmed 20%+ |\n|---|---|---|---|---|---|---|")
qs = np.quantile(pf[val], [1 / 3, 2 / 3])
for lab_, s in (("forecast to drift most (bottom third)", val & (pf < qs[0])), ("middle third", val & (pf >= qs[0]) & (pf < qs[1])),
                ("forecast to firm most (top third)", val & (pf >= qs[1])), ("all", val)):
    print(f"| {lab_} | {s.sum()} | {W[s].mean():.0%} | {ret_open[s].mean():+.0%} | {ret_bsp[s].mean():+.0%} | {np.median(oo[s] / bs[idx][s]):.2f} | {(QB[s] / QO[s] >= 1.25).mean():.0%} |")
for h in (0, 1):
    s0 = val & (half == h)
    q2 = np.quantile(pf[s0], [1 / 3, 2 / 3])
    a = [f"{ret_open[s0 & sel].mean():+.0%} ({(s0 & sel).sum()})" for sel in (pf < q2[0], (pf >= q2[0]) & (pf < q2[1]), pf >= q2[1])]
    print(f"half {h}: open ROI by forecast third, drift / middle / firm: {' / '.join(a)}")
# value judged on the predicted BSP instead of our blend
val2 = (PB * oo >= 1.2) & (1 / PB >= 1.6) & (1 / PB <= 15) & (oo <= 3 / PB)
for lab_, s in (("value on our blend (live)", val), ("value on the predicted BSP", val2), ("both", val & val2), ("blend only", val & ~val2), ("predicted BSP only", val2 & ~val)):
    print(f"{lab_}: {s.sum()} bets, strike {W[s].mean():.0%}, open {ret_open[s].mean():+.0%}, BSP {ret_bsp[s].mean():+.0%}")
np.savez(f"drift_gbm_preds_{os.environ.get('PRICE','v10')}.npz", idx=idx, gb=gb, ga=ga, half=half)
# robustness: each half on its own (half 1 is the honest one: its drift model was trained only on earlier races), flat and staked
import stake_rule
print("\n| rule | half | bets | strike | flat at the open | staked at the open | staked P/L units | flat at BSP |\n|---|---|---|---|---|---|---|---|")
for lab_, s, pp in (("value on our blend (live)", val, BL), ("value on the predicted BSP", val2, PB)):
    for h, hn in ((0, f"before {cut} (drift model fitted on later races)"), (1, f"from {cut} (drift model fitted on earlier races only)")):
        t = s & (half == h)
        st = np.array([stake_rule.stake(pp[i], oo[i]) for i in np.where(t)[0]])
        r = ret_open[t]
        print(f"| {lab_} | {hn} | {t.sum()} | {W[t].mean():.0%} | {r.mean():+.0%} | {(st * r).sum() / st.sum():+.0%} | {(st * r).sum():+.0f}u | {ret_bsp[t].mean():+.0%} |")
# is the drift forecast more than the edge again? value-at-open bets, by edge band, forecast-to-firm half vs the other half
edge = BL * oo - 1
print("\n| edge at the open | forecast | bets | flat at the open | flat at BSP |\n|---|---|---|---|---|")
for lo_, hi_ in ((0.2, 0.5), (0.5, 1.0), (1.0, 99)):
    s = val & (edge >= lo_) & (edge < hi_); md = np.median(pf[s])
    for t, ss in (("firm half", s & (pf >= md)), ("drift half", s & (pf < md))):
        print(f"| {lo_:.0%}-{hi_:.0%} | {t} | {ss.sum()} | {ret_open[ss].mean():+.0%} | {ret_bsp[ss].mean():+.0%} |")
# weighting the stake by the forecast (founder, 18 Oct: "if it's certain factors that have a better ROI, why aren't we weighting those more")
print("\n| stake weighting on the live bets | half | staked | P/L units | ROI |\n|---|---|---|---|---|")
base = np.array([stake_rule.stake(BL[i], oo[i]) if val[i] else 0.0 for i in range(len(oo))])
kel2 = np.array([stake_rule.stake(PB[i], oo[i]) if val[i] else 0.0 for i in range(len(oo))])
q3 = np.quantile(pf[val], [1 / 3, 2 / 3]); mult = np.where(pf >= q3[1], 1.5, np.where(pf < q3[0], 0.5, 1.0))
for lab_, st in (("live stakes", base), ("x1.5 forecast to firm, x0.5 forecast to drift", np.minimum(base * mult, 5)),
                 ("x2 / x0.5", np.minimum(base * np.where(pf >= q3[1], 2, np.where(pf < q3[0], 0.5, 1)), 5)),
                 ("live stake rule on the predicted-BSP chance", kel2)):
    for h in (0, 1):
        t = val & (half == h)
        print(f"| {lab_} | {h} | {st[t].sum():.0f}u | {(st * ret_open)[t].sum():+.0f}u | {(st * ret_open)[t].sum() / st[t].sum():+.0%} |")
# founder: "why would we bet on drifters": drop the forecast-to-drift third outright
print("\n| bets kept | half | bets | staked | P/L units | ROI | drift third alone: bets, P/L |\n|---|---|---|---|---|---|---|")
dr = pf < q3[0]
for lab_, keep, st in (("all value bets, live stakes", val, base), ("drop the forecast-to-drift third", val & ~dr, base),
                       ("drop the drift third, x2 on the firm third", val & ~dr, np.minimum(base * np.where(pf >= q3[1], 2, 1), 5))):
    for h in (0, 1):
        t = keep & (half == h); d0 = val & dr & (half == h)
        print(f"| {lab_} | {h} | {t.sum()} | {st[t].sum():.0f}u | {(st * ret_open)[t].sum():+.0f}u | {(st * ret_open)[t].sum() / st[t].sum():+.0%} | {d0.sum()}, {(base * ret_open)[d0].sum():+.0f}u |")
