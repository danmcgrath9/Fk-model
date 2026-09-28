import numpy as np, bench as b, gbm, json
D = b.load(); tr, te = b.split()
F = np.load("F2.npy")
pre = D["pre_jump"]
te_pre, te_back = te[pre[te]], te[~pre[te]]
cfg = json.load(open("form_price.json")); Z = np.nan_to_num(np.stack([D["X"][:, D["colidx"][f]] for f in cfg["features"]], 1).astype(float))
lin = b.softmax_races(Z @ b.clogit(Z, tr, D["q"], ridge=10.0))
model, it = gbm.fit(F, tr, D["q"])
g = gbm.predict(model, F)
for label, rs in (("pulled before the jump", te_pre), ("back-filled", te_back)):
    print(f"--- {label}: {len(rs)} races")
    for name, p in (("opening market", D["mkt"]), ("linear, deployed inputs, to BSP", lin), ("GBM + engineered, to BSP", g)):
        print(b.fmt(name, b.score(p, rs)))
