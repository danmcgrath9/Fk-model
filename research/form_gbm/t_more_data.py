"""Does more history move our price closer to BSP? (15 Oct 2026, founder: "did the pull overnight help our model get
closer to bsp"). Same stage-1 tree model (all9 settings: softmax-in-race against BSP, F9 inputs, 80% speed-gap copy,
feature_fraction 0.2, extra trees, 4000 rounds), trained twice and scored on the holdout (races from 3 Jun 2026):
A = the races the live model trains on (8 Oct 2025 to 2 Jun 2026); B = the same plus the 1,033 races backfilled for
1 Jul to 7 Oct 2025. python3.13 t_more_data.py [seeds]"""
import numpy as np, sys, time, lab, gbm, lightgbm as lgb, bench as b
D = b.load("ds/model_ds_new.npz")
import price_day as pdm, stage2
ri = D["race_idx"]; nR = D["n_races"]; t0 = time.time()
F, nm = pdm.inputs()
TR = stage2.trials(D["P"], D["past_fields"], ri); SEC = stage2.sections(D["S"], D["sec_fields"], D["P"], D["past_fields"], ri, nR)
F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
nm = list(nm) + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])]
assert nm == open("F9_names.txt").read().split("\n"), "inputs differ from F9"
print("F9", F.shape, f"{time.time()-t0:.0f}s", flush=True)
lab.D = D; lab.ri0 = ri
rd = D["date"]; races = np.arange(nR)
hold = races[rd >= "2026-06-03"]; A = races[(rd >= "2025-10-08") & (rd < "2026-06-03")]; B = races[rd < "2026-06-03"]
print(f"train A {len(A)} races, train B {len(B)} races, holdout {len(hold)} races", flush=True)
q = D["q"]; won = D["finish"] == 1; mk = D["mkt"]
hm = np.isin(ri, hold); hri = np.unique(ri[hm], return_inverse=True)[1]; nh = hri.max() + 1
ok = (np.bincount(hri, weights=(q[hm] > 0) & (mk[hm] > 0), minlength=nh) == np.bincount(hri, minlength=nh)) & (np.bincount(hri, weights=won[hm], minlength=nh) == 1)
def score(p):
    p = p[hm]; s = np.bincount(hri, weights=p, minlength=nh); p = p / s[hri]; m = ok[hri]
    kl = np.sum(np.where(q[hm][m] > 0, q[hm][m] * np.log(np.maximum(q[hm][m], 1e-300) / np.maximum(p[m], 1e-12)), 0)) / ok.sum()
    ll = -np.mean(np.log(np.maximum(p[m & won[hm]], 1e-12)))
    return kl, ll
seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 1
res = {}
for name, tr in (("A", A), ("B", B)):
    preds = []
    for s in range(seeds):
        t1 = time.time(); bst, _ = lab.train(F, nm, tr, q, params=dict(feature_fraction=0.2, extra_trees=True), seed=s, fixed_rounds=4000)
        preds.append(np.log(b.softmax_races(bst.predict(F)))); print(f"{name} seed {s} {time.time()-t1:.0f}s", flush=True)
    res[name] = score(b.softmax_races(np.mean(preds, 0)))
mkl, mll = score(mk)
print(f"\n| trained on | holdout KL to BSP | log loss vs winners |\n|---|---|---|")
print(f"| A: 8 Oct 2025 to 2 Jun 2026 ({len(A)} races) | {res['A'][0]:.4f} | {res['A'][1]:.4f} |")
print(f"| B: plus 1 Jul to 7 Oct 2025 ({len(B)} races) | {res['B'][0]:.4f} | {res['B'][1]:.4f} |")
print(f"| opening market, for reference | {mkl:.4f} | {mll:.4f} |")
