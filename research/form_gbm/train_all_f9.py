import numpy as np, bench as b, lab, lightgbm as lgb, time
D = lab.D; F = np.load("F9.npy"); names = open("F9_names.txt").read().split("\n"); ri = lab.ri0; nR = D["n_races"]
allr = np.arange(nR); prm = dict(feature_fraction=0.2, extra_trees=True, learning_rate=0.03, min_data_in_leaf=50)   # 1 Nov 2026 campaign: lr 0.06 -> 0.03, min leaf 100 -> 50 (lab TE KL 0.0987 -> 0.0973 / 0.0979; combined 0.0955); rounds scaled with the slower rate
for seed in range(5):
    t0 = time.time(); bst, _ = lab.train(F, names, allr, D["q"], params=prm, seed=seed, fixed_rounds=6500); bst.save_model(f"all9_sm{seed}.txt"); print("sm", seed, f"{time.time()-t0:.0f}s", flush=True)
lq = np.log(D["q"]); mean = np.bincount(ri, weights=lq, minlength=nR) / np.bincount(ri, minlength=nR); y = lq - mean[ri]
for seed in range(5):
    t0 = time.time(); Fa = lab.augmented(F, names, seed=seed + 30)
    rp = dict(objective="l2", learning_rate=0.05, num_leaves=31, min_data_in_leaf=100, feature_fraction=0.2, extra_trees=True,
              bagging_fraction=0.8, bagging_freq=1, lambda_l2=10, verbose=-1, num_threads=4, seed=seed)
    lgb.train(rp, lgb.Dataset(np.vstack([F, Fa]), np.concatenate([y, y])), 3400).save_model(f"all9_rg{seed}.txt"); print("rg", seed, f"{time.time()-t0:.0f}s", flush=True)
print("done")
