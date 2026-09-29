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

def extras(rd, ri, horse, trainer, jockey, last_jockey, p, jwin, res):
    """stablemates (count, rank by our price, rank by jockey 12-month win %), the jockey's BSP gap against
    the horse's last jockey's, and the horse's second-last gap, run count and trend. Rows see only earlier dates."""
    trainer = np.asarray(trainer).astype(str); jockey = np.asarray(jockey).astype(str); horse = np.asarray(horse).astype(str)
    key = np.char.add(np.asarray(ri).astype(str), np.char.add("|", trainer))
    _, inv, cnts = np.unique(key, return_inverse=True, return_counts=True)
    nstab = cnts[inv].astype(float); rk = np.zeros(len(ri)); jrk = np.zeros(len(ri))
    for k in np.where(cnts > 1)[0]:
        ix = np.where(inv == k)[0]
        rk[ix[np.argsort(-p[ix])]] = np.arange(1, len(ix) + 1); jrk[ix[np.argsort(-jwin[ix])]] = np.arange(1, len(ix) + 1)
    A = np.column_stack([nstab, rk, jrk, (rk == 1) & (nstab > 1), (jrk == 1) & (nstab > 1)]).astype(float)
    known = np.isfinite(res); order = sorted(set(rd.tolist())); byd = [np.where(rd == d)[0] for d in order]
    s, n = {}, {}; tv = np.zeros(len(ri)); lv = np.zeros(len(ri)); hist = {}; second = np.zeros(len(ri)); nruns = np.zeros(len(ri)); last = np.zeros(len(ri))
    for ix in byd:
        for i in ix:
            tv[i] = s.get(jockey[i], 0) / (n.get(jockey[i], 0) + 5); lv[i] = s.get(last_jockey[i], 0) / (n.get(last_jockey[i], 0) + 5)
            h = hist.get(horse[i], []); second[i] = h[-2] if len(h) >= 2 else 0; nruns[i] = len(h); last[i] = h[-1] / 2 if h else 0
        for i in ix:
            if not known[i]: continue
            s[jockey[i]] = s.get(jockey[i], 0) + res[i]; n[jockey[i]] = n.get(jockey[i], 0) + 1; hist.setdefault(horse[i], []).append(res[i])
    chg = (np.asarray(last_jockey) != jockey) & (np.asarray(last_jockey) != "")
    Bk = np.column_stack([tv - lv, chg.astype(float), np.where(chg, tv - lv, 0)])
    C = np.column_stack([second, nruns, last - second])
    return A, Bk, C
