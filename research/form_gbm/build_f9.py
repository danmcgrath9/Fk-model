"""F9 inputs for the full training set (same builder as the day pricer). python build_f9.py"""
import numpy as np, bench as b, price_day as pdm, stage2, time
t=time.time(); D=b.load("ds/model_ds.npz")
F, nm = pdm.inputs()
TR = stage2.trials(D["P"], D["past_fields"], D["race_idx"])
SEC = stage2.sections(np.load("S_hist.npy"), np.load("S_fields.npy", allow_pickle=True), D["P"], D["past_fields"], D["race_idx"], D["n_races"])
F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
nm = list(nm) + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])]
old = open("F9_names.txt").read().split("\n")
assert nm == old, f"names differ: {len(nm)} vs {len(old)}"
np.save("F9.npy", F); n7 = open("F7_names.txt").read().split("\n"); assert nm[:len(n7)] == n7
np.save("F7.npy", F[:, :len(n7)])   # the holdout check (t_b9_s2 via t_s2feat) reads F7
print("F9", F.shape, f"{time.time()-t:.0f}s")
