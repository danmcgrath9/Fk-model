import numpy as np, gbm
def make_obj_mix(rr, nR, q, finish, w=0.3, depth=3):
    """KL to BSP plus w x Plackett-Luce over the first `depth` finishers."""
    fin = np.where(finish > 0, finish, 999)
    def obj(preds, ds):
        p = gbm.race_softmax(preds, rr, nR)
        g = p - q; h = p * (1 - p)
        e = np.exp(preds - preds.max())
        for k in range(1, depth + 1):
            remain = fin >= k                       # still unplaced at stage k
            has = np.bincount(rr, weights=(fin == k), minlength=nR) > 0
            ok = remain & has[rr]
            ek = np.where(ok, e, 0.0); tot = np.bincount(rr, weights=ek, minlength=nR)[rr]
            pk = np.where(ok, ek / np.maximum(tot, 1e-300), 0.0)
            g += w * (pk - (fin == k) * ok)
            h += w * pk * (1 - pk)
        return g, np.maximum(h, 1e-6)
    return obj
