"""Check the new export before it feeds the retrain (15 Oct 2026): build the inputs exactly as build_f9.py does on the
new dataset, write the new name lists, and confirm the gear-detail and price-move columns give the gain the trials
found (t_combo.py: 0.0929 -> 0.0912), training once without them and once with them. python3.13 t_v10_check.py NPZ"""
import numpy as np, sys, time, lab, bench as b
D = b.load(sys.argv[1])
import price_day as pdm, stage2
ri = D["race_idx"]; nR = D["n_races"]
new_cols = [c for c in D["cols"] if c.startswith("gd_") or c.startswith("fl_")]
print("new columns in the export:", len(new_cols), new_cols[:6], "...", flush=True)
for c in new_cols: print(f"  {c}: filled {np.isfinite(D['X'][:, D['colidx'][c]]).mean():.0%}, non-zero {np.nanmean(D['X'][:, D['colidx'][c]] != 0):.1%}")
F, nm = pdm.inputs(); n7 = len(nm)
TR = stage2.trials(D["P"], D["past_fields"], ri); SEC = stage2.sections(D["S"], D["sec_fields"], D["P"], D["past_fields"], ri, nR)
F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
nm = list(nm) + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])]
old = open("F9_names.txt").read().split("\n")
added = [x for x in nm if x not in old]; gone = [x for x in old if x not in nm]
print(f"inputs: {len(old)} before, {len(nm)} now; added {len(added)}, gone {len(gone)} {gone[:5]}", flush=True)
open("F9_names_v10.txt", "w").write("\n".join(nm)); open("F7_names_v10.txt", "w").write("\n".join(nm[:n7]))
lab.D = D; lab.ri0 = ri
races = np.arange(nR); hold = races[D["date"] >= "2026-06-03"]; train = races[D["date"] < "2026-06-03"]
q = D["q"]; won = D["finish"] == 1; mk = D["mkt"]
hm = np.isin(ri, hold); hri = np.unique(ri[hm], return_inverse=True)[1]; nh = hri.max() + 1
okh = (np.bincount(hri, weights=(q[hm] > 0) & (mk[hm] > 0), minlength=nh) == np.bincount(hri, minlength=nh)) & (np.bincount(hri, weights=won[hm], minlength=nh) == 1)
def score(p):
    p = p[hm]; s = np.bincount(hri, weights=p, minlength=nh); p = p / s[hri]; m = okh[hri]
    kl = np.sum(np.where(q[hm][m] > 0, q[hm][m] * np.log(np.maximum(q[hm][m], 1e-300) / np.maximum(p[m], 1e-12)), 0)) / okh.sum()
    return kl, -np.mean(np.log(np.maximum(p[m & won[hm]], 1e-12)))
def fit(cols, label, seeds=3):
    FF = F[:, cols]; NN = [nm[j] for j in cols]; preds = []
    for s in range(seeds):
        t1 = time.time(); bst, _ = lab.train(FF, NN, train, q, params=dict(feature_fraction=0.2, extra_trees=True), seed=s, fixed_rounds=4000)
        preds.append(np.log(b.softmax_races(bst.predict(FF)))); print(f"{label} seed {s} {time.time()-t1:.0f}s", flush=True)
    return score(b.softmax_races(np.mean(preds, 0)))
without = [j for j, x in enumerate(nm) if x in old]; full = list(range(len(nm)))
res = {"without the new columns": fit(without, "old"), "with them (the challenger's inputs)": fit(full, "new")}
print(f"\n| inputs | holdout KL to BSP | log loss vs winners |\n|---|---|---|")
for k, (kl, ll) in res.items(): print(f"| {k} | {kl:.4f} | {ll:.4f} |")
