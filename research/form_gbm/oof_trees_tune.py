"""Stage-1 tree tuning: out-of-fold KL for a parameter variant (the live setting is feature_fraction 0.2, extra_trees,
num_leaves 31 (rg) / lab default (sm), 4000 rounds). python oof_trees_tune.py LABEL key=val ..."""
import numpy as np, bench as b, lab, sys, lightgbm as lgb, gbm
label=sys.argv[1]; over={k:(float(v) if "." in v else int(v)) for k,v in (a.split("=") for a in sys.argv[2:])}
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; F=np.load("F9.npy"); names=open("F9_names.txt").read().split("\n")
folds=lab.folds if hasattr(lab,"folds") else None
src=open("oof_trees.py").read()
# reuse oof_trees' fold loop but with the overrides merged into both param dicts
src=src.replace('prm = dict(feature_fraction=0.2, extra_trees=True)','prm = dict(feature_fraction=0.2, extra_trees=True); prm.update(over)')
src=src.replace('np.save("p_oof_f9.npy", p)','np.save(f"p_oof_tune_{label}.npy", p)')
src=src.replace('bagging_fraction=0.8, bagging_freq=1, lambda_l2=10, verbose=-1, num_threads=4, seed=k)','bagging_fraction=0.8, bagging_freq=1, lambda_l2=10, verbose=-1, num_threads=4, seed=k); rp.update(over)')
exec(src)
print(label, b.fmt("trees OOF", b.score(p, np.arange(nR))), flush=True)
