"""One set of live-style trees trained on races BEFORE the v10 holdout (3 Jun 2026), so the Why-line attributions on the
holdout are out of sample (3 Nov 2026; t_allpositive.py used the all9 trees, which saw every race)."""
import numpy as np, lab, time, sys
D = lab.D; F = np.load("F9.npy"); names = open("F9_names.txt").read().split("\n")
pre = np.where(D["date"].astype(str) < "2026-06-03")[0]
print(f"training races before 3 Jun: {len(pre)} of {D['n_races']}", flush=True)
for seed in range(int(sys.argv[1]) if len(sys.argv) > 1 else 1):
    t0 = time.time(); bst, _ = lab.train(F, names, pre, D["q"], params=dict(feature_fraction=0.2, extra_trees=True), seed=seed, fixed_rounds=4400)
    bst.save_model(f"pre6_sm{seed}.txt"); print(f"pre6_sm{seed}.txt {time.time()-t0:.0f}s", flush=True)
print("done")
