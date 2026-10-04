"""day stage-1 v5 (F9 = F7 + trial form + section splits): trees 0.5 + network 0.3 + CatBoost 0.2 (log space), weights fitted out of fold. python price_day3.py UP_NPZ OUT_JSON"""
import numpy as np, bench as b, price_day as pdm, lightgbm as lgb, json, sys
up, out = sys.argv[1:3]
D, nR, U, _ = pdm.combined(day=up); pdm.install(D)
F, nm = pdm.inputs()
import stage2
S_all = np.concatenate([np.load("S_hist.npy"), U["S"]]); SF = U["sec_fields"]
TR = stage2.trials(D["P"], D["past_fields"], D["race_idx"]); SEC = stage2.sections(S_all, SF, D["P"], D["past_fields"], D["race_idx"], int(D["race_idx"].max()) + 1)
F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
nm = list(nm) + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])]
assert nm == open("F9_names.txt").read().split("\n"), "day inputs do not match the F9 training inputs"
# Guard (4 Oct 2026, t_resid.py): September's live-pulled races had 80% of raced runners with no last-start speed rating,
# sectionals or vsClass, and priced at KL 0.145 against 0.076 with full data. Refuse to price a day that looks like that.
_n0 = len(D["race_idx"]) - len(U["race_idx"]); _ci = {n: j for j, n in enumerate(nm)}
_raced = np.nan_to_num(F[_n0:, _ci["f_careerForm_s"]], nan=0) >= 1
_miss = np.isnan(F[_n0:, _ci["e_speedRating_last"]])[_raced].mean() if _raced.any() else 0.0
print(f"raced runners missing a last-start speed rating: {_miss*100:.0f}%")
if _miss > 0.10 and "--allow-gaps" not in sys.argv:
    sys.exit(f"STOP: {_miss*100:.0f}% of raced runners have no last-start speed rating (Form King benchmarks missing from the pull). "
             "Re-pull with benchmarks (daily pull at numBenchmarks 5) before pricing, or pass --allow-gaps to price anyway.")
import lab, nn
b.D = D; lab.D = D; lab.ri0 = D["race_idx"]; nn.D = D; nn.ri = D["race_idx"]; nn.nR = D["n_races"]
sm = [np.log(b.softmax_races(lgb.Booster(model_file=f"all9_sm{s}.txt").predict(F))) for s in range(5)]
rg = [np.log(b.softmax_races(lgb.Booster(model_file=f"all9_rg{s}.txt").predict(F))) for s in range(5)]
pt = b.softmax_races(0.7 * np.log(b.softmax_races(np.mean(sm, 0))) + 0.3 * np.log(b.softmax_races(np.mean(rg, 0))))
hist = np.arange(nR)
nets = [np.log(np.maximum(nn.fit(F, nm, hist, None, seed=s, fixed_epochs=14)[0], 1e-12)) for s in range(5)]
pn = b.softmax_races(np.mean(nets, 0))
from catboost import CatBoost
cb = CatBoost(); cb.load_model("cb_all9.cbm"); pc = b.softmax_races(cb.predict(F))
p = b.softmax_races(0.5 * np.log(pt) + 0.3 * np.log(pn) + 0.2 * np.log(pc))
n0 = len(D["race_idx"]) - len(U["race_idx"]); ci = {n: j for j, n in enumerate(nm)}
rows = []
for i in range(n0, len(D["race_idx"])):
    st = F[i, ci["f_careerForm_s"]]; solid = bool((np.nan_to_num(st, nan=-1) >= 1) and not np.isnan(F[i, ci["e_speedRating_last"]]) and F[i, ci["age"]] != 2)
    r = D["race_idx"][i] - nR; bar = D["X"][i, D["colidx"]["barrier"]]
    rows.append(dict(race=int(U["race_number"][r]), race_id=str(U["race_id"][r]), horse=str(D["name"][i]), horse_id=str(D["horse_id"][i]),
                     barrier=None if np.isnan(bar) else int(bar), jockey=str(D["jockey"][i]), p=float(p[i]), solid=solid,
                     p_trees=float(pt[i]), p_net=float(pn[i]), p_cb=float(pc[i])))
json.dump(rows, open(out, "w"), indent=1); print("rows", len(rows))
