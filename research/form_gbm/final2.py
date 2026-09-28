import numpy as np, bench as b, lab, lightgbm as lgb, json, time
D = lab.D; F = np.load("F7.npy"); names = open("F7_names.txt").read().split("\n"); ri = lab.ri0; nR = D["n_races"]
prm = dict(feature_fraction=0.2, extra_trees=True)
sm_logs = []
for seed in range(5):
    _, it, _ = lab.valid_score(F, names, params=prm, rounds=8000, seed=seed)
    bst, _ = lab.train(F, names, lab.TR, D["q"], params=prm, seed=seed, fixed_rounds=int(it * 1.2)); bst.save_model(f"f2_sm{seed}.txt")
    sm_logs.append(np.log(b.softmax_races(bst.predict(F)))); print("softmax", seed, int(it * 1.2), flush=True)
lq = np.log(D["q"]); mean = np.bincount(ri, weights=lq, minlength=nR) / np.bincount(ri, minlength=nR); y = lq - mean[ri]
rg_logs = []
for seed in range(5):
    Fa = lab.augmented(F, names, seed=seed + 10)
    rp = dict(objective="l2", learning_rate=0.05, num_leaves=31, min_data_in_leaf=100, feature_fraction=0.2, extra_trees=True,
              bagging_fraction=0.8, bagging_freq=1, lambda_l2=10, verbose=-1, num_threads=4, seed=seed)
    mi, mv = np.isin(ri, lab.INNER), np.isin(ri, lab.VALID)
    v = lgb.train(rp, lgb.Dataset(np.vstack([F[mi], Fa[mi]]), np.concatenate([y[mi], y[mi]])), 6000,
                  valid_sets=[lgb.Dataset(F[mv], y[mv])], callbacks=[lgb.early_stopping(200, verbose=False)])
    mt = np.isin(ri, lab.TR)
    full = lgb.train(rp, lgb.Dataset(np.vstack([F[mt], Fa[mt]]), np.concatenate([y[mt], y[mt]])), int(v.best_iteration * 1.2))
    full.save_model(f"f2_rg{seed}.txt"); rg_logs.append(np.log(b.softmax_races(full.predict(F)))); print("regression", seed, int(v.best_iteration * 1.2), flush=True)
p_sm = b.softmax_races(np.mean(sm_logs, 0)); p_rg = b.softmax_races(np.mean(rg_logs, 0))
p = b.softmax_races(0.7 * np.log(p_sm) + 0.3 * np.log(p_rg)); np.save("p_final2.npy", p)
te, pre = lab.TE, D["pre_jump"]; prev = np.load("p_final.npy")
for label, rs in (("all 1,093 unseen", te), ("78 live-pulled", te[pre[te]]), ("1,015 back-filled", te[~pre[te]])):
    print(f"--- {label}")
    for n, q in (("opening market", D["mkt"]), ("previous final", prev), ("softmax average", p_sm), ("regression average", p_rg), ("blend 70/30", p)):
        print(b.fmt(n, b.score(q, rs)))
