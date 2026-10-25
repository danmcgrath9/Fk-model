"""Does the model need 10 recent runs of benchmark data, or are 5 enough? (25 Oct 2026, founder, on Form King's national
archive at 10BM $1,799 or 5BM $989: "does 10 make that big a difference?"). Build the live F9 inputs twice from the v10
dataset: as is (10 past runs) and with past runs 6-10 blanked (past-run fields P and sectional benchmarks S). Train the
same LightGBM on each, races before 3 Jun 2026; score 3 Jun onwards: winner log loss, KL to BSP, and the plan at the open
(value 20c+, ours $1.60-$15, open under 3x ours, flat 1u, 16c deduction) and at BSP (8% commission).
python3.13 t_5v10.py"""
import numpy as np, bench as b, price_day as pdm, stage2, lightgbm as lgb, sys
def build(mask):
    D = b.load("ds/model_ds_v10.npz")
    if mask:
        D["P"] = D["P"].astype(float).copy(); D["P"][:, 5:, :] = np.nan
        D["S"] = D["S"].astype(float).copy(); D["S"][:, 5:, :] = np.nan
        b.D["P"], b.D["S"] = D["P"], D["S"]
    F, nm = pdm.inputs()
    TR = stage2.trials(b.D["P"], b.D["past_fields"], b.D["race_idx"])
    SEC = stage2.sections(b.D["S"], b.D["sec_fields"], b.D["P"], b.D["past_fields"], b.D["race_idx"], b.D["n_races"])
    F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
    return F, b.D
res = {}
for mask in (False, True):
    F, D = build(mask)
    ri = D["race_idx"]; nR = int(ri.max()) + 1; rd = D["date"].astype(str); d = rd[ri] if len(rd) == nR else rd
    won = (D["finish"] == 1).astype(int); o = D["open"].astype(float); bs = D["bsp"].astype(float)
    tr = d < "2026-06-03"; te = ~tr
    p = np.zeros(len(won))
    for seed in range(3):
        m = lgb.LGBMClassifier(n_estimators=600, learning_rate=0.03, num_leaves=31, min_child_samples=40, subsample=0.8,
                               subsample_freq=1, colsample_bytree=0.5, reg_lambda=1.0, random_state=seed, verbose=-1)
        m.fit(F[tr], won[tr]); p += m.predict_proba(F)[:, 1] / 3
    s = np.bincount(ri, weights=p, minlength=nR); pm = p / s[ri]
    ok = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1)
    rok = (np.bincount(ri, weights=ok.astype(float), minlength=nR) == np.bincount(ri, minlength=nR)) & (np.bincount(ri, weights=won, minlength=nR) >= 1)
    mm = te & rok[ri]
    qb = np.where(mm, 1 / bs, 0); qb = qb / np.maximum(np.bincount(ri, weights=qb, minlength=nR)[ri], 1e-12)
    ll = -np.log(pm[mm & (won == 1)]).mean()
    kl = np.nansum(np.where(mm, qb * np.log(np.maximum(qb, 1e-12) / np.maximum(pm, 1e-12)), 0)) / len(set(ri[mm]))
    ours = 1 / pm; bet = mm & (pm * o >= 1.2) & (ours >= 1.6) & (ours <= 15) & (o < 3 * ours)
    ro = np.where(won == 1, (o - 1) * 0.84, -1.0)[bet].mean(); rb = np.where(won == 1, (bs - 1) * 0.92, -1.0)[bet].mean()
    res[mask] = (ll, kl, bet.sum(), ro, rb)
    print(f"{'5 runs' if mask else '10 runs'}: races {len(set(ri[mm]))}, winner log loss {ll:.4f}, KL to BSP {kl:.4f}, plan {bet.sum()} bets, "
          f"ROI open {100*ro:+.1f}%, BSP {100*rb:+.1f}%", flush=True)
