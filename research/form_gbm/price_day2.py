"""day stage-1: trees 0.5 + network 0.3 + CatBoost 0.2 (log space), weights fitted out of fold. python price_day2.py UP_NPZ OUT_JSON"""
import numpy as np, bench as b, price_day as pdm, lightgbm as lgb, json, sys
up, out = sys.argv[1:3]
D, nR, U, _ = pdm.combined(day=up); pdm.install(D)
F, nm = pdm.inputs()
import lab, nn
b.D = D; lab.D = D; lab.ri0 = D["race_idx"]; nn.D = D; nn.ri = D["race_idx"]; nn.nR = D["n_races"]
sm = [np.log(b.softmax_races(lgb.Booster(model_file=f"all_sm{s}.txt").predict(F))) for s in range(5)]
rg = [np.log(b.softmax_races(lgb.Booster(model_file=f"all_rg{s}.txt").predict(F))) for s in range(5)]
pt = b.softmax_races(0.7 * np.log(b.softmax_races(np.mean(sm, 0))) + 0.3 * np.log(b.softmax_races(np.mean(rg, 0))))
hist = np.arange(nR)
nets = [np.log(np.maximum(nn.fit(F, nm, hist, None, seed=s, fixed_epochs=14)[0], 1e-12)) for s in range(5)]
pn = b.softmax_races(np.mean(nets, 0))
from catboost import CatBoost
cb = CatBoost(); cb.load_model("cb_all.cbm"); pc = b.softmax_races(cb.predict(F))
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
