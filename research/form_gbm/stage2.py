"""Second stage: the 3-way price, adjusted by how BSP rated each horse / trainer / jockey / sire against our price in earlier races."""
import numpy as np, lightgbm as lgb, datetime as dt, json

def _days(d): return np.array([(dt.date.fromisoformat(str(x)[:10]) - dt.date(2025, 1, 1)).days for x in d])

def encodings(rd, horse, trainer, jockey, sire, track, res):
    """rows in any order; each row sees only rows on EARLIER dates. res = clipped log(BSP chance / our chance), 0 where unknown."""
    dn = _days(rd); order = sorted(set(rd.tolist())); byd = {d: np.where(rd == d)[0] for d in order}
    def enc(key, k=10, half=None, last=False):
        s, n, t = {}, {}, {}; out = np.zeros(len(rd))
        for d in order:
            ix = byd[d]
            for i in ix:
                kk = key[i]
                if kk in s:
                    f = 0.5 ** ((dn[i] - t[kk]) / half) if half else 1.0
                    out[i] = s[kk] * f / (n[kk] * f + k)
            for i in ix:
                if not known[i]: continue
                kk = key[i]
                if half and kk in s: f = 0.5 ** ((dn[i] - t[kk]) / half); s[kk] *= f; n[kk] *= f
                if last: s[kk] = res[i]; n[kk] = 1.0
                else: s[kk] = s.get(kk, 0.0) + res[i]; n[kk] = n.get(kk, 0.0) + 1
                t[kk] = dn[i]
        return out
    known = np.isfinite(res)
    H, T, J, S = (np.asarray(a).astype(str) for a in (horse, trainer, jockey, sire))
    TT = np.char.add(T, np.asarray(track).astype(str))
    return np.stack([enc(H, 1, last=True), enc(H, 5, half=120), enc(T, 5), enc(J, 5), enc(S, 20), enc(TT, 10)], 1)

def design(E, p, ri, nR):
    cnt = np.bincount(ri, minlength=nR).astype(float)
    cen = lambda v: v - (np.bincount(ri, weights=v, minlength=nR) / np.maximum(cnt, 1))[ri]
    L = np.log(np.maximum(p, 1e-12))
    return np.column_stack([E, np.stack([cen(E[:, j]) for j in range(E.shape[1])], 1), cen(L), np.log(cnt[ri]), p]), L
