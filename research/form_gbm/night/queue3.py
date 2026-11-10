"""Queue 3: the stage-1 blend's members and weights, walk-forward (night of 10 Nov 2026).
The live stage 1 is trees 0.5 (softmax trees 0.7 + regression trees 0.3), network 0.3, CatBoost 0.2, weights fitted on
out-of-fold prices in September. Here each member is trained per fold exactly as live trains it, then: every member
alone, the live blend, the no-network blend the cloud session used in October, and the best weights on each fold scored
on the other. Also how much the network moves between seeds (it is re-trained on the history every time a day is priced).
    python3.13 queue3.py   (night folder; after queue1's base arm)"""
import itertools, os, time
import numpy as np, lightgbm as lgb
import nl, lab, nn
from catboost import CatBoost, Pool

F, NM, ri, nR, q = nl.F, nl.NM, nl.ri, nl.nR, nl.q; sm_ = nl.b.softmax_races
lq = np.log(np.maximum(q, 1e-12)); y = lq - (np.bincount(ri, weights=lq, minlength=nR) / np.bincount(ri, minlength=nR))[ri]
M = {}
for fold in ("A", "B"):
    train_races = np.arange(nR)[nl.rdate < nl.FOLDS[fold][0]]; mt = np.isin(ri, train_races)
    f = f"preds/m_rg_{fold}.npy"
    if not os.path.exists(f):
        t0 = time.time(); logs = []
        for s in range(3):
            Fa = lab.augmented(F, NM, seed=s + 30)
            rp = dict(objective="l2", learning_rate=0.05, num_leaves=31, min_data_in_leaf=100, feature_fraction=0.2, extra_trees=True,
                      bagging_fraction=0.8, bagging_freq=1, lambda_l2=10, verbose=-1, num_threads=4, seed=s)
            m = lgb.train(rp, lgb.Dataset(np.vstack([F[mt], Fa[mt]]), np.concatenate([y[mt], y[mt]])), 3400); logs.append(np.log(sm_(m.predict(F))))
        np.save(f, sm_(np.mean(logs, 0))); print(f"rg {fold} {time.time()-t0:.0f}s", flush=True)
    f = f"preds/m_nn_{fold}.npy"
    if not os.path.exists(f):
        t0 = time.time(); ps = [nn.fit(F, NM, train_races, None, seed=s, fixed_epochs=14)[0] for s in range(3)]
        np.save(f"preds/m_nn_seeds_{fold}.npy", np.array(ps)); np.save(f, sm_(np.mean([np.log(np.maximum(p, 1e-12)) for p in ps], 0))); print(f"nn {fold} {time.time()-t0:.0f}s", flush=True)
    f = f"preds/m_cb_{fold}.npy"
    if not os.path.exists(f):
        t0 = time.time(); Fa = lab.augmented(F, NM, seed=30)
        X = np.vstack([F[mt], Fa[mt]]); yy = np.concatenate([q[mt]] * 2); g = np.concatenate([ri[mt], ri[mt] + nR]); o_ = np.argsort(g, kind="stable")
        m = CatBoost(dict(loss_function="QuerySoftMax", iterations=2900, learning_rate=0.08, depth=6, l2_leaf_reg=10, rsm=0.2, thread_count=4, random_seed=0, verbose=0))
        m.fit(Pool(X[o_], yy[o_], group_id=g[o_])); np.save(f, sm_(m.predict(F))); print(f"cb {fold} {time.time()-t0:.0f}s", flush=True)
    M[fold] = {k: np.load(f"preds/{n}_{fold}.npy").astype(float) for k, n in (("sm", "base"), ("rg", "m_rg"), ("nn", "m_nn"), ("cb", "m_cb"))}

L_ = lambda p: np.log(np.maximum(p, 1e-12))
def blend(fold, wt, wn, wc, rgw=0.3):
    m = M[fold]; trees = sm_((1 - rgw) * L_(m["sm"]) + rgw * L_(m["rg"]))
    return sm_(wt * L_(trees) + wn * L_(m["nn"]) + wc * L_(m["cb"]))
hm = {f: (nl.date >= nl.FOLDS[f][1]) & (nl.date < nl.FOLDS[f][2]) for f in "AB"}
print("\n| price | fold A: KL / log loss / profit | fold B: KL / log loss / profit |\n|---|---|---|")
def row(lab_, fn):
    cells = []
    for f in "AB":
        p = fn(f); n, w, st, pl = nl.run(p, hm[f]); cells.append(f"{nl.kl(p, hm[f]):.4f} / {nl.ll(p, hm[f]):.4f} / {pl:+.0f}u")
    print(f"| {lab_} | " + " | ".join(cells) + " |", flush=True)
row("softmax trees alone (the queue's base arm)", lambda f: M[f]["sm"]); row("regression trees alone", lambda f: M[f]["rg"])
row("network alone (3 seeds)", lambda f: M[f]["nn"]); row("CatBoost alone", lambda f: M[f]["cb"])
row("trees: 0.7 softmax + 0.3 regression", lambda f: blend(f, 1, 0, 0)); row("no-network blend: trees 0.7 + CatBoost 0.3", lambda f: blend(f, 0.7, 0, 0.3))
row("LIVE blend: trees 0.5, network 0.3, CatBoost 0.2", lambda f: blend(f, 0.5, 0.3, 0.2))
grid = [(a, b_, c) for a, b_, c in itertools.product(np.arange(0, 1.01, 0.1), repeat=3) if abs(a + b_ + c - 1) < 1e-9]
best = {f: min(grid, key=lambda w: nl.kl(blend(f, *w), hm[f])) for f in "AB"}
for f, g_ in (("A", "B"), ("B", "A")):
    w = best[g_]; print(f"best weights on fold {g_}: trees {w[0]:.1f} / network {w[1]:.1f} / CatBoost {w[2]:.1f} -> scored on fold {f}: KL {nl.kl(blend(f, *w), hm[f]):.4f} (live weights {nl.kl(blend(f, 0.5, 0.3, 0.2), hm[f]):.4f})")
for rgw in (0.0, 0.15, 0.3, 0.5): print(f"regression share of the trees {rgw:.2f}: KL A {nl.kl(blend('A', 0.5, 0.3, 0.2, rgw), hm['A']):.4f}  B {nl.kl(blend('B', 0.5, 0.3, 0.2, rgw), hm['B']):.4f}")
for f in "AB":
    ps = np.load(f"preds/m_nn_seeds_{f}.npy"); d = np.abs(np.log(ps[0][hm[f]] / ps[1][hm[f]])); d3 = np.abs(np.log(M[f]["nn"][hm[f]] / M[f]["sm"][hm[f]]))
    print(f"fold {f}: two network seeds are a median {100*np.median(d):.1f}% apart runner by runner (90th pct {100*np.percentile(d, 90):.0f}%); the 3-seed network v the trees {100*np.median(d3):.1f}%")
for f in "AB": nl.record("m_live_blend", f, blend(f, 0.5, 0.3, 0.2), "trees 0.5 / network 0.3 / CatBoost 0.2, every member trained in the fold")
print("queue 3 done")
