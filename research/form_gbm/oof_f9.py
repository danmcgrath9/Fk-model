"""Trees OOF on F7 + trial form + section splits (stage2.trials / stage2.sections), same 5 date blocks and settings as oof.py."""
import numpy as np, bench as b, lab, lightgbm as lgb, time, stage2
D = lab.D; ri = lab.ri0; nR = D["n_races"]
F7 = np.load("F7.npy"); names = open("F7_names.txt").read().split("\n")
TR = stage2.trials(D["P"], D["past_fields"], ri)
SEC = stage2.sections(np.load("S_hist.npy"), np.load("S_fields.npy", allow_pickle=True), D["P"], D["past_fields"], ri, nR)
F = np.hstack([F7, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
names = names + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])]
np.save("F9.npy", F); open("F9_names.txt", "w").write("\n".join(names)); print("F9", F.shape, flush=True)
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
old = np.load("p_oof.npy"); allr = np.arange(nR)
print(b.fmt("trees F7 (old)", b.score(old, allr))); print(b.fmt("trees F9 (+trials +sections)", b.score(p, allr)))
nn_, cb_ = np.load("p_oof_nn.npy"), np.load("p_oof_cb.npy")
bl = b.softmax_races(0.5 * np.log(p) + 0.3 * np.log(nn_) + 0.2 * np.log(cb_)); np.save("p_oof_blend3_f9.npy", bl)
print(b.fmt("blend with F9 trees", b.score(bl, allr))); print(b.fmt("blend (old)", b.score(np.load("p_oof_blend3.npy"), allr)))
