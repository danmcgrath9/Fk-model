"""5 runs or 10 of benchmark data, on Dave's 10BM national sample (25 Oct 2026). 14 days, 20 Aug to 2 Sep, all states:
615 races, 5,838 runners, with the benchmark fields on past runs 6-10 (our own dataset has them on 5 at most).
Three arms of the same quick LightGBM, cross-validated by day (7 folds of two days each, 3 seeds):
  10BM     every past run as exported
  10 basic runs 6-10 keep rating / finish / margin / days only (what 5BM would hold if it kept the basics)
  5 runs   runs 6-10 blanked entirely
Scores: winner log loss, KL to BSP, and the plan (value 20c+ at the open, ours $1.60-$15, open under 3x ours, flat 1u,
16c deduction) at the open and at BSP (8% commission). Paired bootstrap over races on the log-loss gap.
python3.13 t_5v10_sample.py ALL10.npz"""
import numpy as np, bench as b, price_day as pdm, stage2, lightgbm as lgb, sys, warnings
warnings.filterwarnings("ignore")
path = sys.argv[1]
BASIC = ("days_before", "rating", "finish", "runners", "margin", "distance", "going_band", "barrier", "weight", "trial", "same_track", "prize", "prep", "bsp", "sp")
def build(arm):
    D = b.load(path); pf = list(D["past_fields"])
    P = D["P"].astype(float).copy(); S = D["S"].astype(float).copy()
    if arm == "5 runs": P[:, 5:, :] = np.nan; S[:, 5:, :] = np.nan
    if arm == "10 basic":
        keep = [pf.index(n) for n in BASIC if n in pf]
        mask = np.ones(P.shape[2], bool); mask[keep] = False
        P[:, 5:, mask] = np.nan; S[:, 5:, :] = np.nan
    b.D["P"], b.D["S"] = P, S
    F, nm = pdm.inputs()
    TR = stage2.trials(b.D["P"], b.D["past_fields"], b.D["race_idx"])
    SEC = stage2.sections(b.D["S"], b.D["sec_fields"], b.D["P"], b.D["past_fields"], b.D["race_idx"], b.D["n_races"])
    F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
    return F, b.D
res = {}
for arm in ("10BM", "10 basic", "5 runs"):
    F, D = build(arm)
    ri = D["race_idx"]; nR = int(ri.max()) + 1; rd = D["date"].astype(str); d = rd[ri] if len(rd) == nR else rd
    won = (D["finish"] == 1).astype(int); o = D["open"].astype(float); bs = D["bsp"].astype(float)
    days = sorted(set(d)); folds = [days[i::7] for i in range(7)]
    p = np.zeros(len(won))
    for fd in folds:
        te = np.isin(d, fd); tr = ~te
        for seed in range(3):
            m = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=30, subsample=0.8,
                                   subsample_freq=1, colsample_bytree=0.5, reg_lambda=1.0, random_state=seed, verbose=-1)
            m.fit(F[tr], won[tr]); p[te] += m.predict_proba(F[te])[:, 1] / 3
    s = np.bincount(ri, weights=p, minlength=nR); pm = p / np.maximum(s[ri], 1e-12)
    ok = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1)
    rok = (np.bincount(ri, weights=ok.astype(float), minlength=nR) == np.bincount(ri, minlength=nR)) & (np.bincount(ri, weights=won, minlength=nR) >= 1)
    mm = rok[ri]
    qb = np.where(mm, 1 / bs, 0); qb = qb / np.maximum(np.bincount(ri, weights=qb, minlength=nR)[ri], 1e-12)
    llw = -np.log(np.maximum(pm[mm & (won == 1)], 1e-9))  # per race, winner log loss
    kl = np.nansum(np.where(mm, qb * np.log(np.maximum(qb, 1e-12) / np.maximum(pm, 1e-12)), 0)) / len(set(ri[mm]))
    ours = 1 / pm; bet = mm & (pm * o >= 1.2) & (ours >= 1.6) & (ours <= 15) & (o < 3 * ours)
    ro = np.where(won == 1, (o - 1) * 0.84, -1.0)[bet].mean(); rb = np.where(won == 1, (bs - 1) * 0.92, -1.0)[bet].mean()
    res[arm] = dict(ll=llw, kl=kl, n=bet.sum(), ro=ro, rb=rb, rid=ri[mm & (won == 1)])
    print(f"| {arm} | {len(set(ri[mm]))} | {llw.mean():.4f} | {kl:.4f} | {bet.sum()} | {100*ro:+.1f}% | {100*rb:+.1f}% |", flush=True)
rng = np.random.default_rng(0)
for a, c in (("10BM", "5 runs"), ("10BM", "10 basic"), ("10 basic", "5 runs")):
    x, y = res[a]["ll"], res[c]["ll"]; n = len(x)
    gap = x - y; bs_ = [gap[rng.integers(0, n, n)].mean() for _ in range(2000)]
    print(f"log loss {a} minus {c}: {gap.mean():+.4f} (95% {np.percentile(bs_,2.5):+.4f} to {np.percentile(bs_,97.5):+.4f}; negative = {a} better)")
