"""PREP-PATTERN inputs (prep_feats.py) through the same harness as the straight test. Was: Straight-course input (1 Nov 2026, founder: "add a straight course input, the 1000m Flemington is completely different to
Caulfield 1000m"). Flemington runs up to 1200m on the straight six. New inputs: straight (Flemington, 1200m or less), and its
products with the predicted settling position share, the barrier share and the usual settle share, so the trees can find
how run style and draw behave on the straight with few examples. Same LightGBM as t_fs_feats.py, three seeds, trained on
races before 3 Jun 2026, scored from 3 Jun: winner log loss and KL to BSP on all races and on straight races, plus a
cross-fit over the WHOLE history in four date folds (each fold priced by trees trained on the other three), because the
holdout holds only 14 straight races."""
import numpy as np, bench as b, price_day as pdm, stage2, lightgbm as lgb
D = b.load("ds/model_ds_v10.npz"); b.D = D
F0, nm = pdm.inputs()
TR = stage2.trials(D["P"], D["past_fields"], D["race_idx"])
SEC = stage2.sections(D["S"], D["sec_fields"], D["P"], D["past_fields"], D["race_idx"], D["n_races"])
F0 = np.hstack([F0, TR, SEC]).astype(np.float32); F0[~np.isfinite(F0)] = np.nan
ri = D["race_idx"]; nR = int(ri.max()) + 1; c = D["colidx"]; X = D["X"]; n = len(ri)
import prep_feats
straight = np.zeros(n, bool); possh = X[:, c["sm_predicted_position"]].astype(float); fld = np.bincount(ri, minlength=nR)[ri].astype(float); possh = (possh - 1) / np.maximum(fld - 1, 1)
new = prep_feats.build(D["P"], list(D["past_fields"]), X[:, c["raw_run_in_prep"]].astype(float))
F1 = np.hstack([F0] + [v[:, None] for v in new.values()]).astype(np.float32); F1[~np.isfinite(F1)] = np.nan
won = (D["finish"] == 1).astype(float); d = D["date"].astype(str)[ri]; o = D["open"].astype(float); bs = D["bsp"].astype(float)
okr = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1)
rok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == np.bincount(ri, minlength=nR)) & (np.bincount(ri, weights=won, minlength=nR) >= 1)
qb = np.where(rok[ri], 1 / bs, 0); qb = qb / np.maximum(np.bincount(ri, weights=qb, minlength=nR)[ri], 1e-12)
print("prep inputs set for", {k: round(float(np.isfinite(v).mean()), 3) for k, v in new.items()})
def fit(F, tr, seeds=3):
    p = np.zeros(n)
    for seed in range(seeds):
        m = lgb.LGBMClassifier(n_estimators=600, learning_rate=0.03, num_leaves=31, min_child_samples=40, subsample=0.8,
                               subsample_freq=1, colsample_bytree=0.5, reg_lambda=1.0, random_state=seed, verbose=-1)
        m.fit(F[tr], won[tr]); p += m.predict_proba(F)[:, 1] / seeds
        if F is F1 and seed == 0:
            g = m.booster_.feature_importance("gain"); g = g / g.sum(); k0 = F0.shape[1]
            print("   gain share of the new inputs: " + ", ".join(f"{k} {100*g[k0+i]:.2f}%" for i, k in enumerate(new)))
    s = np.bincount(ri, weights=p, minlength=nR); return p / s[ri]
def score(pm, sel, lab):
    rs = np.zeros(nR, bool); rs[np.unique(ri[sel])] = True
    ll = -np.log(pm[sel & (won == 1)]).mean()
    v = np.bincount(ri, weights=np.where(sel, qb * np.log(np.maximum(qb, 1e-12) / np.maximum(pm, 1e-12)), 0), minlength=nR)
    fw = sel & (np.nan_to_num(possh, nan=9) < 1/3); bk = sel & (np.nan_to_num(possh, nan=-9) >= 2/3)
    return f"{lab:22s} races {rs.sum():4d}  log loss {ll:.4f}  KL {v[rs].mean():.4f}  forward won {won[fw].sum():3.0f}/{pm[fw].sum():5.1f}  back won {won[bk].sum():3.0f}/{pm[bk].sum():5.1f}"
print("\nHOLDOUT (trained before 3 Jun)")
trn = d < "2026-06-03"; te = ~trn & rok[ri]
for lab, F in (("live inputs", F0), ("plus prep inputs", F1)):
    pm = fit(F, trn); print(" " + lab); print("   " + score(pm, te, "all races")); print("   " + score(pm, te & np.isfinite(new["fu_gain"]), "races w/ fu_gain set"))
print("\nCROSS-FIT, whole history, 4 date folds")
days = np.array(sorted(set(d))); folds = np.array_split(days, 4)
for lab, F in (("live inputs", F0), ("plus prep inputs", F1)):
    pm = np.zeros(n)
    for f in folds:
        tf = np.isin(d, f); pm[tf] = fit(F, ~tf, seeds=2)[tf]
    s = np.bincount(ri, weights=pm, minlength=nR); pm = pm / s[ri]
    print(" " + lab); print("   " + score(pm, rok[ri], "all races")); print("   " + score(pm, rok[ri] & np.isfinite(new["fu_gain"]), "runners w/ fu_gain"))
    np.save(f"cf_prep_{'base' if F is F0 else 'new'}.npy", pm)
