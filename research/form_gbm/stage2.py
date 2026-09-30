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


SEC_NEED = ["8-4|vsClass", "8-4|vsLeader", "2-F|vsField", "S-8|vsClass", "6-F|vsClass"]


def sections(S, sec_fields, P, past_fields, ri, nR):
    """Form King section splits of the last race runs (13 columns, tested 30 Sep 2026: holdout KL
    0.0848 -> 0.0835): the last race run's 800-400 vs class and vs leader, last 200 vs field,
    start-800 and last 600 vs class, how much better the middle was than the whole run, the
    real-move-then-faded flag, the mean of up to three runs for middle and last 600, three of
    those relative to the race, and whether the horse has any section data at all."""
    SF = {str(n): i for i, n in enumerate(sec_fields)}; f = {str(n): i for i, n in enumerate(past_fields)}
    S = np.asarray(S, float); P = np.asarray(P, float); n = len(ri); ar = np.arange(n)
    tr = P[:, :, f["trial"]] == 1
    has = ~tr & np.isfinite(S[:, :, SF["8-4|vsClass"]])
    j = np.argmax(has, 1); ok = has[ar, j]
    g = lambda k: np.where(ok, S[ar, j, SF[k]], np.nan)
    def mean3(k):
        v = np.where(has, S[:, :, SF[k]], np.nan)
        rank = np.cumsum(np.isfinite(v), 1)
        v = np.where(np.isfinite(v) & (rank <= 3), v, np.nan)
        c = np.isfinite(v).sum(1)
        return np.where(c > 0, np.nansum(v, 1) / np.maximum(c, 1), np.nan)
    mid, midL, l2F, e8, f6 = (g(k) for k in SEC_NEED)
    overall = np.where(ok, P[ar, j, f["vsClass"]], np.nan)
    movefade = np.where(ok, ((midL >= 1.0) & (l2F <= -1.0)).astype(float), np.nan)
    mid3, f63 = mean3("8-4|vsClass"), mean3("6-F|vsClass")
    def rrel(v):
        fin = np.isfinite(v)
        m = np.bincount(ri, weights=np.where(fin, v, 0), minlength=nR) / np.maximum(np.bincount(ri, weights=fin, minlength=nR), 1)
        return np.where(fin, v - m[ri], np.nan)
    return np.column_stack([mid, midL, l2F, e8, f6, mid - overall, movefade, mid3, f63,
                            rrel(mid), rrel(mid3), rrel(f63), ok.astype(float)])
