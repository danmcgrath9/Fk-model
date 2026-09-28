import numpy as np, lightgbm as lgb, bench as b

def race_softmax(s, rr, nR):
    mx = np.full(nR, -np.inf); np.maximum.at(mx, rr, s)
    e = np.exp(s - mx[rr]); return e / np.bincount(rr, weights=e, minlength=nR)[rr]

def make_obj(rr, nR, t):
    def obj(preds, ds):
        p = race_softmax(preds, rr, nR)
        return p - t, np.maximum(p * (1 - p), 1e-6)
    return obj

def fit(F, races_train, target, params=None, rounds=2000, valid_share=0.8, verbose=False, early=100):
    """Train on the older part of races_train, early-stop on its newest fifth, then return the model and best iteration."""
    D = b.D
    inner, valid = b.split(valid_share, races_train)
    def part(races):
        m = b.runner_mask(races)
        _, rr = np.unique(D["race_idx"][m], return_inverse=True)
        return m, rr, rr.max() + 1
    mi, rri, nRi = part(inner); mv, rrv, nRv = part(valid)
    P = dict(learning_rate=0.03, num_leaves=15, min_data_in_leaf=100, feature_fraction=0.5, bagging_fraction=0.8,
             bagging_freq=1, lambda_l2=10.0, verbose=-1, objective="none", num_threads=4)
    fobj = make_obj(rri, nRi, target[mi])
    if params: P.update(params)
    dtr = lgb.Dataset(F[mi], free_raw_data=False)
    best, best_it, s_v, it = 1e9, 0, None, 0
    booster = lgb.Booster(params=P, train_set=dtr)
    qv, wv = D["q"][mv], D["won"][mv]
    hist = []
    for it in range(1, rounds + 1):
        booster.update(fobj=fobj)
        if it % 25 == 0:
            pv = race_softmax(booster.predict(F[mv]), rrv, nRv)
            kl = np.sum(np.where(qv > 0, qv * np.log(np.maximum(qv, 1e-300) / np.maximum(pv, 1e-12)), 0)) / nRv
            ll = -np.log(np.maximum(pv[wv == 1], 1e-12)).sum() / nRv
            loss = kl if target is D["q"] else ll
            hist.append((it, kl, ll))
            if loss < best - 1e-5: best, best_it = loss, it
            elif it - best_it >= early: break
    if verbose: print(hist[-5:])
    # refit on all of races_train with the best iteration count
    m, rr, nR = part(races_train)
    fobj = make_obj(rr, nR, target[m])
    full = lgb.Booster(params=P, train_set=lgb.Dataset(F[m]))
    for _ in range(best_it): full.update(fobj=fobj)
    return full, best_it

def predict(model, F):
    return b.softmax_races(model.predict(F))
