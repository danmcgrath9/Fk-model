"""Validation lab: decisions on the newest fifth of the training races; test only at the end."""
import numpy as np, lightgbm as lgb, bench as b, gbm
D = b.load(); TR, TE = b.split(); INNER, VALID = b.split(0.8, TR)
names0 = open("F2_names.txt").read().split("\n")
ri0 = D["race_idx"]; pre = D["pre_jump"]; dt0 = D["date"][ri0]
_recent = (dt0 >= "2026-08-15") & ~pre[ri0]

def gap_cols(F, names):
    base = np.load("F2.npy")
    g = [j for j, n in enumerate(names0) if np.isnan(base[pre[ri0], j]).mean() - np.isnan(base[_recent, j]).mean() > 0.4]
    gn = {names0[j] for j in g}
    return [j for j, n in enumerate(names) if n in gn or any(n.startswith(x + "__") for x in gn)]

XZ = ("speed_rel", "speed_best_rel", "finish_speed_rel", "last600_rel", "to600_rel")

def augmented(F, names, share=0.8, seed=1):
    rng = np.random.default_rng(seed)
    Fa = F.copy(); drop = rng.random(len(ri0)) < share
    for j in gap_cols(F, names): Fa[drop, j] = np.nan
    for j, n in enumerate(names):
        if n in XZ: Fa[drop, j] = 0.0
    return Fa

def _part(races, ri):
    m = np.isin(ri, races); _, rr = np.unique(ri[m], return_inverse=True); return m, rr, rr.max() + 1

def train(F, names, train_races, target, params=None, rounds=5000, valid_races=None, aug=True, seed=0, fixed_rounds=None):
    """Fit on train_races (+ blanked copy). Early-stop on valid_races when given. Returns booster, rounds."""
    nR = D["n_races"]
    if aug:
        Fall = np.vstack([F, augmented(F, names, seed=seed + 1)]); ri = np.concatenate([ri0, ri0 + nR])
        tr = np.concatenate([train_races, train_races + nR]); t = np.concatenate([target, target])
    else:
        Fall, ri, tr, t = F, ri0, train_races, target
    m, rr, n = _part(tr, ri)
    P = dict(learning_rate=0.06, num_leaves=15, min_data_in_leaf=100, feature_fraction=0.5, bagging_fraction=0.8,
             bagging_freq=1, lambda_l2=10.0, verbose=-1, objective="none", num_threads=4, seed=seed)
    if params: P.update(params)
    fobj = gbm.make_obj(rr, n, t[m])
    bst = lgb.Booster(params=P, train_set=lgb.Dataset(Fall[m]))
    if fixed_rounds:
        for _ in range(fixed_rounds): bst.update(fobj=fobj)
        return bst, fixed_rounds
    mv, rrv, nv = _part(valid_races, ri0); qv = D["q"][mv]
    best, best_it, it = 1e9, 0, 0
    for it in range(1, rounds + 1):
        bst.update(fobj=fobj)
        if it % 25 == 0:
            pv = gbm.race_softmax(bst.predict(F[mv]), rrv, nv)
            kl = np.sum(np.where(qv > 0, qv * np.log(np.maximum(qv, 1e-300) / np.maximum(pv, 1e-12)), 0)) / nv
            if kl < best - 1e-5: best, best_it = kl, it
            elif it - best_it >= 150: break
    return bst, best_it

def valid_score(F, names, target=None, **kw):
    target = D["q"] if target is None else target
    bst, it = train(F, names, INNER, target, valid_races=VALID, **kw)
    p = b.softmax_races(bst.predict(F, num_iteration=it))
    return b.score(p, VALID), it, bst
