"""Queue 5: seeds for the other two blend members, and do the trees' small gains survive inside the full blend?
(night of 10 Nov 2026)
Queue 3 found two network seeds a median 13.6% apart runner by runner. Live averages 5 network seeds and 1 CatBoost
model. Here: 20 network seeds and 3 CatBoost seeds per fold, then
  the network alone and the live blend with 1 / 3 / 5 / 10 / 20 network seeds (mean over disjoint seed groups),
  CatBoost alone and the blend with 1 v 3 CatBoost seeds,
  the full blend with each trees recipe from queue 4 (3 seeds, 5 seeds, slow 5, 10 seeds),
  and everything together against the live recipe.
    python3.13 queue5.py   (night folder; after queues 3 and 4)"""
import os, time
import numpy as np
import nl, lab, nn
from catboost import CatBoost, Pool

F, NM, ri, nR, q = nl.F, nl.NM, nl.ri, nl.nR, nl.q; sm_ = nl.b.softmax_races; NS = 20
L_ = lambda p: np.log(np.maximum(p, 1e-12)); avg = lambda ps: sm_(np.mean([L_(p) for p in ps], 0))
hm = {f: (nl.date >= nl.FOLDS[f][1]) & (nl.date < nl.FOLDS[f][2]) for f in "AB"}
NN, CB, T = {}, {}, {}
for fold in "AB":
    train_races = np.arange(nR)[nl.rdate < nl.FOLDS[fold][0]]; mt = np.isin(ri, train_races)
    f = f"preds/m_nn20_{fold}.npy"
    if not os.path.exists(f):
        t0 = time.time(); ps = list(np.load(f"preds/m_nn_seeds_{fold}.npy"))
        ps += [nn.fit(F, NM, train_races, None, seed=s, fixed_epochs=14)[0] for s in range(len(ps), NS)]
        np.save(f, np.array(ps, dtype=np.float32)); print(f"nn x{NS} {fold} {time.time()-t0:.0f}s", flush=True)
    NN[fold] = np.load(f).astype(float)
    cbs = [np.load(f"preds/m_cb_{fold}.npy").astype(float)]
    for s in (1, 2):
        f = f"preds/m_cb_s{s}_{fold}.npy"
        if not os.path.exists(f):
            t0 = time.time(); Fa = lab.augmented(F, NM, seed=30 + s)
            X = np.vstack([F[mt], Fa[mt]]); yy = np.concatenate([q[mt]] * 2); g = np.concatenate([ri[mt], ri[mt] + nR]); o_ = np.argsort(g, kind="stable")
            m = CatBoost(dict(loss_function="QuerySoftMax", iterations=2900, learning_rate=0.08, depth=6, l2_leaf_reg=10, rsm=0.2, thread_count=4, random_seed=s, verbose=0))
            m.fit(Pool(X[o_], yy[o_], group_id=g[o_])); np.save(f, sm_(m.predict(F)).astype(np.float32)); print(f"cb seed {s} {fold} {time.time()-t0:.0f}s", flush=True)
        cbs.append(np.load(f).astype(float))
    CB[fold] = cbs; rg = np.load(f"preds/m_rg_{fold}.npy").astype(float)
    T[fold] = {k: sm_(0.7 * L_(np.load(f"preds/{n}_{fold}.npy").astype(float)) + 0.3 * L_(rg)) for k, n in (("3 seeds", "base"), ("5 seeds", "base5"), ("slow, 5 seeds", "slow5"), ("10 seeds", "seeds10"))}

blend = lambda t, n, c: sm_(0.5 * L_(t) + 0.3 * L_(n) + 0.2 * L_(c))
def cell(ps, f):
    """mean KL / log loss / profit over a list of prices"""
    k = np.mean([nl.kl(p, hm[f]) for p in ps]); l = np.mean([nl.ll(p, hm[f]) for p in ps]); pl = np.mean([nl.run(p, hm[f])[3] for p in ps])
    return f"{k:.4f} / {l:.4f} / {pl:+.0f}u"
def row(lab_, fn): print(f"| {lab_} | " + " | ".join(cell(fn(f), f) for f in "AB") + " |", flush=True)
groups = lambda n: [list(range(i, i + n)) for i in range(0, NS - n + 1, n)]

print("\nNETWORK SEEDS (mean over disjoint groups of seeds; trees 5 seeds, CatBoost 1)\n| network seeds | alone, fold A: KL / log loss / profit | alone, fold B |\n|---|---|---|")
for n in (1, 3, 5, 10, 20): row(f"{n}", lambda f: [avg(NN[f][g]) for g in groups(n)])
print("\n| network seeds | LIVE blend, fold A: KL / log loss / profit | LIVE blend, fold B |\n|---|---|---|")
for n in (1, 3, 5, 10, 20): row(f"{n}", lambda f: [blend(T[f]["5 seeds"], avg(NN[f][g]), CB[f][0]) for g in groups(n)])
for f in "AB":
    ks = [nl.kl(blend(T[f]["5 seeds"], avg(NN[f][g]), CB[f][0]), hm[f]) for g in groups(5)]; pls = [nl.run(blend(T[f]["5 seeds"], avg(NN[f][g]), CB[f][0]), hm[f])[3] for g in groups(5)]
    print(f"fold {f}: the blend's spread across four 5-seed network draws: KL {min(ks):.4f} to {max(ks):.4f}, profit {min(pls):+.0f}u to {max(pls):+.0f}u")
    a, b_ = avg(NN[f][:5]), avg(NN[f][5:10]); d = np.abs(np.log(a[hm[f]] / b_[hm[f]])); a, b_ = avg(NN[f][:10]), avg(NN[f][10:]); d2 = np.abs(np.log(a[hm[f]] / b_[hm[f]]))
    x, y = blend(T[f]["5 seeds"], avg(NN[f][:5]), CB[f][0]), blend(T[f]["5 seeds"], avg(NN[f][5:10]), CB[f][0]); d3 = np.abs(np.log(x[hm[f]] / y[hm[f]]))
    print(f"fold {f}: two 5-seed networks are a median {100*np.median(d):.1f}% apart runner by runner, two 10-seed networks {100*np.median(d2):.1f}%; "
          f"the BLENDED price on two 5-seed draws {100*np.median(d3):.1f}% (90th pct {100*np.percentile(d3, 90):.1f}%)")

print("\nCATBOOST SEEDS (trees 5 seeds, network 5 seeds)\n| CatBoost | fold A: KL / log loss / profit | fold B |\n|---|---|---|")
row("alone, 1 seed (mean of 3)", lambda f: CB[f]); row("alone, 3 seeds", lambda f: [avg(CB[f])])
row("live blend, 1 seed (mean of 3)", lambda f: [blend(T[f]["5 seeds"], avg(NN[f][:5]), c) for c in CB[f]]); row("live blend, 3 seeds", lambda f: [blend(T[f]["5 seeds"], avg(NN[f][:5]), avg(CB[f]))])

print("\nTHE TREES RECIPE INSIDE THE FULL BLEND (network 5 seeds, CatBoost 1; the regression trees are 3 seeds throughout)\n| softmax trees | fold A: KL / log loss / profit | fold B |\n|---|---|---|")
for k in T["A"]: row(k, lambda f: [blend(T[f][k], avg(NN[f][:5]), CB[f][0])])

print("\nTOGETHER\n| blend | fold A: KL / log loss / profit | fold B |\n|---|---|---|")
row("the live recipe: trees 5 seeds, network 5, CatBoost 1", lambda f: [blend(T[f]["5 seeds"], avg(NN[f][:5]), CB[f][0])])
row("trees 10 seeds, network 20, CatBoost 3", lambda f: [blend(T[f]["10 seeds"], avg(NN[f]), avg(CB[f]))])
row("slow trees 5 seeds, network 20, CatBoost 3", lambda f: [blend(T[f]["slow, 5 seeds"], avg(NN[f]), avg(CB[f]))])
for f in "AB":
    nl.record("blend_live_recipe", f, blend(T[f]["5 seeds"], avg(NN[f][:5]), CB[f][0]), "trees 5 seeds, network 5 seeds, CatBoost 1 seed, live weights")
    nl.record("blend_more_seeds", f, blend(T[f]["10 seeds"], avg(NN[f]), avg(CB[f])), "trees 10 seeds, network 20 seeds, CatBoost 3 seeds, live weights")
print("queue 5 done")
