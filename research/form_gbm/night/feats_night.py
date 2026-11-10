"""New input families tried on the night of 10 Nov 2026 (queue2.py).

gap2: every rating reaches the trees as "value minus the best in the race" (0 for the top horse), "minus the race mean"
      and a rank. The top-rated horse's MARGIN OVER THE SECOND is invisible: a horse 10 points clear and one half a
      point clear both read 0 and rank 1. gap2 = value minus the best OTHER runner (the top horse's margin, positive;
      for everyone else the same as the existing figure). z = (value - race mean) / race sd. close = how many rivals sit
      within half a race sd of this runner.
apt:  rolling records counted only from races before each race's date, winners against BSP's expected winners, shrunk:
      sire and dam sire on today's going class (wet or dry) and in today's distance band, jockey at today's track,
      trainer in today's distance band."""
import collections, math
import numpy as np


def _top2(v, ri, nR):
    """per race: the largest and second largest finite value (second = largest when tied or alone -> nan if alone)"""
    ok = np.isfinite(v); vv = np.where(ok, v, -np.inf)
    order = np.lexsort((-vv, ri)); first = np.searchsorted(ri[order], np.arange(nR)); n = np.bincount(ri, minlength=nR)
    t1 = vv[order[np.minimum(first, len(v) - 1)]]; has2 = n >= 2
    t2 = np.where(has2, vv[order[np.minimum(first + 1, len(v) - 1)]], -np.inf)
    t1 = np.where(np.isfinite(t1), t1, np.nan); t2 = np.where(np.isfinite(t2), t2, np.nan)
    top_row = np.zeros(len(v), bool); top_row[order[first[n > 0]]] = True
    return t1, t2, top_row


def gap2(F, NM, ri, nR, with_z=False):
    """margin over the best other runner for every input that already has a __vmax twin"""
    cols, names = [], []
    idx = {n: j for j, n in enumerate(NM)}
    for n in NM:
        if not n.endswith("__vmax") or n[:-6] not in idx: continue
        v = F[:, idx[n[:-6]]].astype(float); t1, t2, top = _top2(v, ri, nR)
        g = np.where(top, v - t2[ri], v - t1[ri]); g[~np.isfinite(v)] = np.nan
        cols.append(g); names.append(n[:-6] + "__gap2")
        if with_z:
            ok = np.isfinite(v); c = np.bincount(ri, weights=ok, minlength=nR); s = np.bincount(ri, weights=np.where(ok, v, 0), minlength=nR)
            mean = s / np.maximum(c, 1); var = np.bincount(ri, weights=np.where(ok, (v - mean[ri]) ** 2, 0), minlength=nR) / np.maximum(c - 1, 1)
            sd = np.sqrt(np.maximum(var, 1e-12)); z = np.where(ok & (c[ri] >= 3), (v - mean[ri]) / sd[ri], np.nan)
            cols.append(z); names.append(n[:-6] + "__z")
    return np.column_stack(cols).astype(np.float32), names


def close_counts(F, NM, ri, nR, keys=("rating_neural", "e_rat_rw", "e_wfaRat_rw", "e_speedRating_rw", "rating_peak12m", "e_rat_last", "x_pastp_rw")):
    """rivals within half a race sd of this runner, above and below, for a handful of headline ratings"""
    cols, names = [], []; idx = {n: j for j, n in enumerate(NM)}; starts = np.searchsorted(ri, np.arange(nR)); ends = np.append(starts[1:], len(ri))
    for k in keys:
        if k not in idx: continue
        v = F[:, idx[k]].astype(float); up = np.full(len(v), np.nan); dn = np.full(len(v), np.nan)
        for r in range(nR):
            x = v[starts[r]:ends[r]]; ok = np.isfinite(x)
            if ok.sum() < 3: continue
            sd = np.std(x[ok]);
            if sd <= 0: continue
            d = x[:, None] - x[None, :]; a = np.where(ok[:, None] & ok[None, :], d, np.nan)
            up[starts[r]:ends[r]] = np.where(ok, np.nansum((a < 0) & (a > -0.5 * sd), 1), np.nan)      # rivals just above
            dn[starts[r]:ends[r]] = np.where(ok, np.nansum((a > 0) & (a < 0.5 * sd), 1), np.nan)       # rivals just below
        cols += [up, dn]; names += [k + "__close_above", k + "__close_below"]
    return np.column_stack(cols).astype(np.float32), names


def aptitude(D, K=4.0):
    ri = D["race_idx"]; nR = D["n_races"]; rdate = D["date"].astype(str); q = D["q"]; won = D["won"]
    going = D["going"].astype(float); dist = D["distance"].astype(float); track = D["track"].astype(str)
    wet = (going >= 3).astype(int); band = np.where(dist <= 1200, 0, np.where(dist <= 1600, 1, 2))
    sire, dam, jk, tr = (D[k].astype(str) for k in ("sire", "dam_sire", "jockey", "trainer"))
    keysets = [("sire_going", lambda i, r: (sire[i], wet[r])), ("sire_dband", lambda i, r: (sire[i], band[r])),
               ("damsire_going", lambda i, r: (dam[i], wet[r])), ("damsire_dband", lambda i, r: (dam[i], band[r])),
               ("jockey_track", lambda i, r: (jk[i], track[r])), ("trainer_dband", lambda i, r: (tr[i], band[r]))]
    stats = [collections.defaultdict(lambda: [0.0, 0.0, 0]) for _ in keysets]
    out = np.full((len(ri), 2 * len(keysets)), np.nan, np.float32)
    order = np.argsort(rdate, kind="stable"); starts = np.searchsorted(ri, np.arange(nR)); ends = np.append(starts[1:], len(ri))
    j = 0
    while j < len(order):
        d = rdate[order[j]]; day = []
        while j < len(order) and rdate[order[j]] == d: day.append(order[j]); j += 1
        for r in day:                                   # features first, from races before today
            for i in range(starts[r], ends[r]):
                for s, (name, kf) in enumerate(keysets):
                    k = kf(i, r)
                    if not k[0]: continue
                    W, E, n = stats[s].get(k, (0.0, 0.0, 0))
                    out[i, 2 * s] = math.log((W + K) / (E + K)); out[i, 2 * s + 1] = math.log1p(n)
        for r in day:                                   # then add today's results
            if not np.isfinite(q[starts[r]:ends[r]]).all(): continue
            for i in range(starts[r], ends[r]):
                for s, (name, kf) in enumerate(keysets):
                    k = kf(i, r)
                    if not k[0]: continue
                    st = stats[s][k]; st[0] += won[i]; st[1] += q[i]; st[2] += 1
    names = [x for name, _ in keysets for x in (name + "_ae", name + "_n")]
    return out, names
