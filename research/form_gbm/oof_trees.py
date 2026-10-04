"""Trees OOF on F7 + trial form + section splits (stage2.trials / stage2.sections), same 5 date blocks and settings as oof.py."""
import numpy as np, bench as b, lab, lightgbm as lgb, time, stage2
D = lab.D; ri = lab.ri0; nR = D["n_races"]
F = np.load("F9.npy"); names = open("F9_names.txt").read().split("\n")
order = np.argsort(D["date"], kind="stable"); blocks = np.array_split(order, 5)
lq = np.log(D["q"]); mean = np.bincount(ri, weights=lq, minlength=nR) / np.bincount(ri, minlength=nR); y = lq - mean[ri]
oof = np.zeros(len(ri)); prm = dict(feature_fraction=0.2, extra_trees=True)
for k, blk in enumerate(blocks):
    t0 = time.time(); train = np.sort(np.concatenate([bb for j, bb in enumerate(blocks) if j != k]))
    sm, _ = lab.train(F, names, train, D["q"], params=prm, seed=k, fixed_rounds=4000)
    Fa = lab.augmented(F, names, seed=k + 20); mt = np.isin(ri, train)
    rp = dict(objective="l2", learning_rate=0.05, num_leaves=31, min_data_in_leaf=100, feature_fraction=0.2, extra_trees=True,
              bagging_fraction=0.8, bagging_freq=1, lambda_l2=10, verbose=-1, num_threads=4, seed=k)
    rg = lgb.train(rp, lgb.Dataset(np.vstack([F[mt], Fa[mt]]), np.concatenate([y[mt], y[mt]])), 3000)
    mb = np.isin(ri, blk)
    oof[mb] = (0.7 * np.log(b.softmax_races(sm.predict(F))) + 0.3 * np.log(b.softmax_races(rg.predict(F))))[mb]
    print(f"block {k} {time.time()-t0:.0f}s", flush=True)
p = b.softmax_races(oof); np.save("p_oof_f9.npy", p)
print(b.fmt("trees F9 OOF", b.score(p, np.arange(nR))))
