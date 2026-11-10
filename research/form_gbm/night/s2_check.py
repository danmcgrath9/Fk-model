"""The second stage on two folds: is it at its ceiling too? (night of 10 Nov 2026)
Stage 2 v6 (stage2f_train.py: 400 rounds, 7 leaves, learning rate 0.03, 3 seeds, the stage-1 price as the starting
score) rebuilt on the 9 Nov dataset from the 10 Nov challenger's out-of-fold three-model stage-1 price, then trained
inside each fold exactly as live trains it and scored on the fold's unseen races (A: fitted before 3 Jun 2026, scored
3 Jun - 9 Nov; B: fitted before 1 Jan 2026, scored 1 Jan - 2 Jun). The stage-1 price is cross-fitted, the same for every
arm, so arms compare cleanly. Arms: the live settings on three seed sets (noise floor), more seeds, rounds, learning
rate, tree size, each input block removed, and the first version's inputs alone.
    python3.13 s2_check.py   (night folder)"""
import json, time
import numpy as np, lightgbm as lgb
import nl, gbm, stage2

D = nl.D; ri, nR, q = nl.ri, nl.nR, nl.q; sm_ = nl.b.softmax_races; Z = np.load("ds/model_ds.npz", allow_pickle=True)
p = np.load("p_oof_chal.npy").astype(float); rd = nl.date
res = np.clip(np.log(np.maximum(q, 1e-4)) - np.log(np.maximum(p, 1e-4)), -3, 3)
jw = np.nan_to_num(D["X"][:, D["colidx"]["jockeyForm_lastTwelveMonthWinPercentage"]].astype(float), nan=0)
lastj = np.array([next((x for x in row if x), "") for row in D["past_jockeys"].astype(str)])
t0 = time.time()
E = stage2.encodings(rd, D["horse_id"], D["trainer"], D["jockey"], D["sire"], D["track"][ri], res)
A, Bk, C = stage2.extras(rd, ri, D["horse_id"], D["trainer"], D["jockey"], lastj, p, jw, res)
X0, L = stage2.design(E, p, ri, nR); SEC = stage2.sections(Z["S"], Z["sec_fields"], D["P"], D["past_fields"], ri, nR)
TV = stage2.travel(D["training_location"], D["track"][ri], ri, nR); lid, lf = stage2.last_start(D["P"], D["past_fields"], D["past_race_ids"])
CO = stage2.collateral(D["race_id"][ri], D["date"][ri], D["horse_id"], D["finish"], q, lid, D["date"][ri], D["horse_id"], lf, ri, nR)
TR = stage2.trials(D["P"], D["past_fields"], ri)
BLK = {"market-gap encodings (horse, trainer, jockey, sire, trainer at track)": X0, "stablemates": A, "jockey switch": Bk, "horse's earlier gaps": C,
       "sections": SEC, "trials": TR, "travel": TV, "collateral form": CO}
print(f"inputs built in {time.time()-t0:.0f}s: " + ", ".join(f"{k.split(' (')[0]} {v.shape[1]}" for k, v in BLK.items()), flush=True)
hm = {f: (nl.date >= nl.FOLDS[f][1]) & (nl.date < nl.FOLDS[f][2]) for f in "AB"}
BASE = dict(learning_rate=0.03, num_leaves=7, min_data_in_leaf=200, feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10, verbose=-1, objective="none", num_threads=4)


def fit(X, fold, seeds=(0, 1, 2), rounds=400, **kw):
    m = rd < nl.FOLDS[fold][0]; _, rr = np.unique(ri[m], return_inverse=True); f = gbm.make_obj(rr, rr.max() + 1, q[m]); out = []
    for s in seeds:
        P = dict(BASE); P.update(kw); P["seed"] = s; bst = lgb.Booster(params=P, train_set=lgb.Dataset(X[m], init_score=L[m]))
        for _ in range(rounds): bst.update(fobj=f)
        out.append(bst.predict(X))
    return sm_(L + np.mean(out, 0))


def sc(pp, f): return nl.kl(pp, hm[f]), nl.ll(pp, hm[f]), nl.run(pp, hm[f])[3]
ALL = np.column_stack(list(BLK.values())); RES = {}; OUT = open("s2_results.jsonl", "a")
def arm(name, X=None, **kw):
    X = ALL if X is None else X; cells = []
    for f in "AB":
        pp = fit(X, f, **kw); RES[(name, f)] = sc(pp, f); np.save(f"preds/s2_{name.split(':')[0].replace(' ', '_')}_{f}.npy", pp.astype(np.float32))
        OUT.write(json.dumps(dict(name=name, fold=f, kl=RES[(name, f)][0], ll=RES[(name, f)][1], profit=RES[(name, f)][2])) + "\n"); OUT.flush()
    b0 = RES.get(("base", "A")), RES.get(("base", "B"))
    d = "" if name == "base" else " | " + " | ".join(f"{RES[(name, f)][0]-b0[i][0]:+.4f} / {RES[(name, f)][1]-b0[i][1]:+.4f} / {RES[(name, f)][2]-b0[i][2]:+.0f}u" for i, f in enumerate("AB"))
    print(f"| {name} | " + " | ".join(f"{RES[(name, f)][0]:.4f} / {RES[(name, f)][1]:.4f} / {RES[(name, f)][2]:+.0f}u" for f in "AB") + d + " |", flush=True)


print("\n| arm | fold A: KL / log loss / profit | fold B | change A | change B |\n|---|---|---|---|---|")
s1 = [sc(p, f) for f in "AB"]; print("| stage 1 alone (the cross-fitted three-model price) | " + " | ".join(f"{a:.4f} / {b_:.4f} / {c:+.0f}u" for a, b_, c in s1) + " |", flush=True)
arm("base"); arm("base_s10: live settings, seeds 10-12", seeds=(10, 11, 12)); arm("base_s20: live settings, seeds 20-22", seeds=(20, 21, 22))
arm("seeds10: 10 seeds", seeds=tuple(range(10)))
arm("r200: 200 rounds", rounds=200); arm("r800: 800 rounds", rounds=800); arm("r1600: 1600 rounds", rounds=1600)
arm("slow: learning rate 0.015, 800 rounds", rounds=800, learning_rate=0.015); arm("fast: learning rate 0.06, 200 rounds", rounds=200, learning_rate=0.06)
arm("nl3: 3 leaves", num_leaves=3); arm("nl15: 15 leaves", num_leaves=15); arm("nl31: 31 leaves, min leaf 100", num_leaves=31, min_data_in_leaf=100)
arm("md100: min leaf 100", min_data_in_leaf=100); arm("md400: min leaf 400", min_data_in_leaf=400)
arm("ff40: feature share 0.4", feature_fraction=0.4); arm("ff100: feature share 1.0", feature_fraction=1.0)
arm("l2_1: lambda 1", lambda_l2=1.0); arm("l2_50: lambda 50", lambda_l2=50.0)
arm("nl15_r800: 15 leaves, 800 rounds", num_leaves=15, rounds=800)
for k in BLK: arm(f"drop_{list(BLK).index(k)}: without {k.split(' (')[0]}", X=np.column_stack([v for kk, v in BLK.items() if kk != k]))
arm("v1: the market-gap encodings alone", X=X0)
print("s2 check done")
