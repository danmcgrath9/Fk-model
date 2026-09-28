import numpy as np, bench as b, lab, json, time
D = lab.D; F4 = np.load("F4.npy"); nm = open("F4_names.txt").read().split("\n")
prm = dict(feature_fraction=0.2, extra_trees=True)
logs = []
for seed in range(5):
    t0 = time.time()
    _, it, _ = lab.valid_score(F4, nm, params=prm, rounds=8000, seed=seed)           # rounds from validation
    bst, _ = lab.train(F4, nm, lab.TR, D["q"], params=prm, seed=seed, fixed_rounds=int(it * 1.2))
    bst.save_model(f"final_seed{seed}.txt")
    logs.append(np.log(b.softmax_races(bst.predict(F4))))
    print(f"seed {seed}: {int(it*1.2)} trees, {time.time()-t0:.0f}s", flush=True)
p = b.softmax_races(np.mean(logs, 0)); np.save("p_final.npy", p)
pre = D["pre_jump"]; te = lab.TE
cfg = json.load(open("form_price.json")); Z = np.nan_to_num(np.stack([D["X"][:, D["colidx"][f]] for f in cfg["features"]], 1).astype(float))
old = b.softmax_races(Z @ b.clogit(Z, lab.TR, D["won"], ridge=30.0))
first = np.load("g_aug.npy")
for label, rs in (("all 1,093 unseen", te), ("78 live-pulled", te[pre[te]]), ("1,015 back-filled", te[~pre[te]])):
    print(f"--- {label}")
    for n, q in (("opening market", D["mkt"]), ("deployed form price", old), ("first model (this afternoon)", first), ("final: 5-model average", p)):
        print(b.fmt(n, b.score(q, rs)))
