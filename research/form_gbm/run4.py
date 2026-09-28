import numpy as np, bench as b, gbm, json
D = b.load(); tr, te = b.split(); F = np.load("F2.npy"); names = open("F2_names.txt").read().split("\n")
ri = D["race_idx"]; pre = D["pre_jump"]; dt = D["date"][ri]
recent = (dt >= "2026-08-15") & ~pre[ri]
gap = [j for j, n in enumerate(names) if np.isnan(F[pre[ri], j]).mean() - np.isnan(F[recent, j]).mean() > 0.4]
xz = [j for j, n in enumerate(names) if n in ("speed_rel", "speed_best_rel", "finish_speed_rel", "last600_rel", "to600_rel")]
# augment: a copy of the training races with the speed figures blanked on a random 80% of runners
rng = np.random.default_rng(1)
Fa = F.copy(); drop = rng.random(len(ri)) < 0.8
for j in gap: Fa[drop, j] = np.nan
for j in xz: Fa[drop, j] = 0.0
# stack: original races + blanked copy as extra races (renumber)
Dsave = {k: D[k] for k in ("race_idx", "starts", "ends", "n_races", "q", "won", "date")}
n = len(ri); nR = D["n_races"]
F_all = np.vstack([F, Fa])
b.D["race_idx"] = np.concatenate([ri, ri + nR]); b.D["n_races"] = 2 * nR
b.D["q"] = np.concatenate([D["q"], D["q"]]); b.D["won"] = np.concatenate([D["won"], D["won"]])
b.D["date"] = np.concatenate([D["date"], D["date"]])
tr_all = np.concatenate([tr, tr + nR])
model, it = gbm.fit(F_all, tr_all, b.D["q"], params=dict(learning_rate=0.06), rounds=4000)
for k, v in Dsave.items(): b.D[k] = v
g = gbm.predict(model, F); np.save("g_aug.npy", g)
cfg = json.load(open("form_price.json")); Z = np.nan_to_num(np.stack([D["X"][:, D["colidx"][f]] for f in cfg["features"]], 1).astype(float))
lin = b.softmax_races(Z @ b.clogit(Z, tr, D["q"], ridge=10.0)); np.save("lin_bsp.npy", lin)
g0 = np.load("g_F2.npy")
for label, rs in (("all test", te), ("live-pulled", te[pre[te]]), ("back-filled", te[~pre[te]])):
    print(f"--- {label} ({len(rs)})")
    for nm, p in (("market", D["mkt"]), ("linear to BSP", lin), ("GBM", g0), ("GBM trained with speed gaps", g)):
        print(b.fmt(nm, b.score(p, rs)))
    for wgt in (0.5, 0.7):
        bl = b.softmax_races(wgt * np.log(g) + (1 - wgt) * np.log(lin))
        print(b.fmt(f"blend {wgt:.0%} GBM(gaps) + linear", b.score(bl, rs)))
