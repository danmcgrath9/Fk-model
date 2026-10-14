"""Rail x track x run style as a model input (15 Oct 2026). Built the way bias.py builds the live track-bias inputs:
for each runner, how runners in the same cell won against BSP at EARLIER meetings only (rolling.roll, strictly before
the race date), shrunk, with the number of earlier runners beside it. Cells: track x rail band x predicted style,
rail band x predicted style (all tracks), track x rail band x barrier third. Then the same stage-1 test as the others.
python3.13 t_rail_feat.py RACE_RAILS.tsv [seeds]"""
import numpy as np, sys, time, lab, bench as b, rolling
from datetime import date
D = b.load("ds/model_ds_new.npz")
import price_day as pdm, stage2
ri = D["race_idx"]; nR = D["n_races"]; n = len(ri)
rid = D["race_id"].astype(str); trk = D["track"].astype(str)[ri]
rail = {}
for line in open(sys.argv[1]):
    p = line.rstrip("\n").split("\t")
    if p[0] == "R": rail[p[1]] = float(p[2])
rm = np.array([rail.get(x, np.nan) for x in rid])[ri]
band = np.where(np.isnan(rm), "", np.where(rm <= 0, "t", np.where(rm <= 4, "a", np.where(rm <= 8, "b", "c"))))
c = D["colidx"]; X = D["X"]; fld = np.bincount(ri, minlength=nR)[ri].astype(float)
pos = X[:, c["sm_predicted_position"]].astype(float); sh = (pos - 1) / np.maximum(fld - 1, 1)
sty = np.where(np.isnan(pos), "", np.where(pos <= 1, "lead", np.where(sh < 0.34, "on", np.where(sh < 0.67, "mid", "back"))))
bar = X[:, c["barrier"]].astype(float); bsh = (bar - 1) / np.maximum(fld - 1, 1)
bb = np.where(np.isnan(bar), "", np.where(bsh < 0.34, "in", np.where(bsh < 0.67, "mid", "out")))
day = np.array([(date.fromisoformat(d) - date(2020, 1, 1)).days for d in D["date"]])[ri]
win = (D["finish"] == 1).astype(float); exp = D["q"]; ok = D["finish"] > 0
def key(*parts):
    k = parts[0].astype("U40")
    for p in parts[1:]: k = np.char.add(np.char.add(k, "|"), p.astype("U40"))
    return np.where(np.any([p == "" for p in parts], 0), "", k)
R = {}
for name, k in (("rb_trk_rail_sty", key(trk, band, sty)), ("rb_rail_sty", key(band, sty)), ("rb_trk_rail_bar", key(trk, band, bb))):
    kk = np.where(ok, k, "")
    r, w, x = rolling.roll(kk, day, win, exp, k, day)
    R[f"{name}_ae"] = np.where(r >= 10, (w + 2) / (x + 2), np.nan).astype(np.float32); R[f"{name}_n"] = np.log1p(r).astype(np.float32)
R["rail_m"] = rm.astype(np.float32)
print("rail inputs", len(R), "coverage", f"{np.isfinite(R['rb_trk_rail_sty_ae']).mean():.0%}", flush=True)
F, nm = pdm.inputs()
TR = stage2.trials(D["P"], D["past_fields"], ri); SEC = stage2.sections(D["S"], D["sec_fields"], D["P"], D["past_fields"], ri, nR)
F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
nm = list(nm) + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])]
assert nm == open("F9_names.txt").read().split("\n")
lab.D = D; lab.ri0 = ri
races = np.arange(nR); hold = races[D["date"] >= "2026-06-03"]; train = races[D["date"] < "2026-06-03"]
q = D["q"]; won = D["finish"] == 1; mk = D["mkt"]
hm = np.isin(ri, hold); hri = np.unique(ri[hm], return_inverse=True)[1]; nh = hri.max() + 1
okh = (np.bincount(hri, weights=(q[hm] > 0) & (mk[hm] > 0), minlength=nh) == np.bincount(hri, minlength=nh)) & (np.bincount(hri, weights=won[hm], minlength=nh) == 1)
def score(p):
    p = p[hm]; s = np.bincount(hri, weights=p, minlength=nh); p = p / s[hri]; m = okh[hri]
    kl = np.sum(np.where(q[hm][m] > 0, q[hm][m] * np.log(np.maximum(q[hm][m], 1e-300) / np.maximum(p[m], 1e-12)), 0)) / okh.sum()
    return kl, -np.mean(np.log(np.maximum(p[m & won[hm]], 1e-12)))
seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 3
def fit(FF, NN, label):
    preds = []
    for s in range(seeds):
        t1 = time.time(); bst, _ = lab.train(FF, NN, train, q, params=dict(feature_fraction=0.2, extra_trees=True), seed=s, fixed_rounds=4000)
        preds.append(np.log(b.softmax_races(bst.predict(FF)))); print(f"{label} seed {s} {time.time()-t1:.0f}s", flush=True)
    return score(b.softmax_races(np.mean(preds, 0)))
res = {"F9 (current inputs)": fit(F, nm, "F9"), "+ rail x track x style": fit(np.hstack([F, np.column_stack(list(R.values()))]), nm + list(R), "rail")}
print(f"\n| inputs | holdout KL to BSP | log loss vs winners |\n|---|---|---|")
for k, (kl, ll) in res.items(): print(f"| {k} | {kl:.4f} | {ll:.4f} |")
