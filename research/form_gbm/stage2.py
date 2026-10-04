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


def trials(P, past_fields, ri):
    """Trial form (13 columns, tested 30 Sep 2026 after Tatura R1, a first-starter that had won its
    last three trials priced $19.80 against a $2.60 BSP: holdout KL 0.0835 -> 0.0824). Race runs,
    trials (a duplicated trial record, same days before, counted once), trial wins and placings,
    wins in the last three trials, the last trial's finish, relative finish, days ago and field,
    the same for horses with at most one race run, and the trial strike rate."""
    f = {str(n): i for i, n in enumerate(past_fields)}; P = np.asarray(P, float); n = len(ri)
    tr = P[:, :, f["trial"]] == 1; days = P[:, :, f["days_before"]]; fin = P[:, :, f["finish"]]; run = P[:, :, f["runners"]]
    real = ~tr & np.isfinite(fin) & (fin > 0)
    seen = np.zeros_like(tr)
    for s in range(P.shape[1]):
        dup = np.zeros(n, bool)
        for t in range(s):
            dup |= tr[:, t] & (days[:, t] == days[:, s])
        seen[:, s] = tr[:, s] & np.isfinite(fin[:, s]) & (fin[:, s] > 0) & ~dup
    nraces = real.sum(1); ntr = seen.sum(1)
    twins = (seen & (fin == 1)).sum(1); tplace = (seen & (fin <= 3)).sum(1)
    t3wins = (seen & (np.cumsum(seen, 1) <= 3) & (fin == 1)).sum(1)
    j = np.argmax(seen, 1); ar = np.arange(n); has = seen[ar, j]
    lfin = np.where(has, fin[ar, j], np.nan); lrel = np.where(has, (fin[ar, j] - 1) / np.maximum(run[ar, j] - 1, 1), np.nan)
    ldays = np.where(has, days[ar, j], np.nan); lrun = np.where(has, run[ar, j], np.nan)
    few = (nraces <= 1).astype(float)
    return np.column_stack([nraces, ntr, twins, tplace, t3wins, lfin, lrel, ldays, lrun, few * twins, few * t3wins,
                            few * np.nan_to_num(1 - lrel, nan=0.5), twins / np.maximum(ntr, 1)])


# ---- v6 inputs (4 Oct 2026): travel and collateral form. Holdout KL 0.0806 -> 0.0800 together, four seeds, both halves.
LL={"Cranbourne":(-38.10,145.28),"Pakenham":(-38.07,145.48),"Pakenham 3":(-38.07,145.48),"Flemington":(-37.79,144.91),"Ballarat":(-37.56,143.85),
"Mornington":(-38.22,145.04),"Warrnambool":(-38.38,142.48),"Seymour":(-37.03,145.14),"Geelong":(-38.15,144.36),"Wangaratta":(-36.36,146.31),
"Bendigo":(-36.76,144.28),"Sale":(-38.11,147.07),"Kyneton":(-37.24,144.45),"Swan Hill":(-35.34,143.55),"Stawell":(-37.06,142.78),"Plumpton":(-37.68,144.69),
"Horsham":(-36.71,142.20),"Benalla":(-36.55,145.98),"Kilmore":(-37.30,144.95),"Moe":(-38.17,146.26),"Colac":(-38.34,143.59),"Wodonga":(-36.12,146.89),
"Freshwater Creek":(-38.27,144.19),"Euroa":(-36.75,145.57),"Echuca":(-36.13,144.75),"Caulfield":(-37.88,145.04),"Mildura":(-34.19,142.16),
"Ararat":(-37.28,142.93),"Hamilton":(-37.74,142.02),"Bairnsdale":(-37.83,147.61),"Traralgon":(-38.20,146.54),"Werribee":(-37.90,144.66),
"Mornington Peninsula":(-38.3,145.1),"Macedon":(-37.42,144.56),"Yarra Glen":(-37.66,145.37),"Terang":(-38.24,142.92),"Tatura":(-36.44,145.23),
"Casterton":(-37.58,141.40),"Donald":(-36.37,142.98),"Avoca":(-37.09,143.47),"Murtoa":(-36.62,142.47),"Nhill":(-36.33,141.65),"Kerang":(-35.73,143.92),
"Camperdown":(-38.23,143.15),"Coleraine":(-37.60,141.69),"Mortlake":(-38.08,142.81),"Penshurst":(-37.87,142.29),"Dunkeld":(-37.65,142.34),
"Edenhope":(-37.04,141.29),"Great Western":(-37.15,142.86),"Burrumbeet":(-37.49,143.65),"Hanging Rock":(-37.33,144.59),"Stony Creek":(-38.58,146.03),
"Towong":(-36.12,147.97),"Wycheproof":(-36.08,143.23),"Manangatang":(-35.05,142.88),"Warracknabeal":(-36.25,142.39),"St Arnaud":(-36.62,143.26),
"Yarra Valley":(-37.66,145.37),"Moonee Valley":(-37.77,144.93),"Sandown Hillside":(-37.95,145.16),"Sandown Lakeside":(-37.95,145.16),"Caulfield Heath":(-37.88,145.04),
"Pakenham Park":(-38.07,145.48),"Pakenham Synthetic":(-38.07,145.48),"Ballarat Synthetic":(-37.56,143.85),
"Randwick":(-33.90,151.23),"Warwick Farm":(-33.91,150.94),"Rosehill":(-33.82,151.02),"Canberra":(-35.28,149.13),"Albury":(-36.08,146.92),"Wagga":(-35.11,147.37),
"Murray Bridge":(-35.12,139.27),"Morphettville":(-34.98,138.54),"Mount Gambier":(-37.83,140.78),"Gawler":(-34.60,138.74),"Goulburn":(-34.75,149.72),
"Hawkesbury":(-33.61,150.75),"Gosford":(-33.42,151.34),"Newcastle":(-32.93,151.78),"Scone":(-32.05,150.87),"Kembla Grange":(-34.47,150.80),"Nowra":(-34.88,150.60),
"Corowa":(-35.99,146.38),"Wangaratta ":(-36.36,146.31),"Lindsay Park":(-34.47,138.90),"Ballan":(-37.60,144.23),"Lara":(-38.02,144.41),"Tyabb":(-38.26,145.19),
"Balnarring":(-38.37,145.13),"Bacchus Marsh":(-37.67,144.44),"Gisborne":(-37.49,144.59),"Romsey":(-37.35,144.74),"Lancefield":(-37.28,144.73),"Nagambie":(-36.79,145.15),
"Shepparton":(-36.38,145.40),"Yarrawonga":(-36.01,146.00),"Beaumaris":(-37.98,145.04),"Mount Macedon":(-37.42,144.59),"Spring Mount":(-37.5,144.5)}

def _hav(a, b):
    la1, lo1 = np.radians(a); la2, lo2 = np.radians(b)
    d = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(d))

def _rrel(v, ri, nR):
    fin = np.isfinite(v); m = np.bincount(ri, weights=np.where(fin, v, 0), minlength=nR) / np.maximum(np.bincount(ri, weights=fin, minlength=nR), 1)
    return np.where(fin, v - m[ri], np.nan)

TRAVEL_MEDIAN_KM = 79.0

def travel(training_location, track, ri, nR):
    """Great-circle km from the stable's town to today's track (approximate town coordinates), log1p, a 200km+ flag,
    a home (40km) flag, and the km relative to the field. Unknown towns take the history median."""
    tl = np.asarray(training_location).astype(str); tk = np.asarray(track).astype(str)
    km = np.array([_hav(LL[t], LL[k]) if t in LL and k in LL else np.nan for t, k in zip(tl, tk)])
    kmf = np.where(np.isfinite(km), km, TRAVEL_MEDIAN_KM)
    return np.column_stack([np.log1p(kmf), np.isfinite(km).astype(float), (kmf >= 200).astype(float), (kmf <= 40).astype(float), _rrel(kmf, ri, nR)])

def collateral(h_rid, h_date, h_horse, h_fin, h_q, t_last_rid, t_date, t_horse, t_fin_in_last, ri, nR):
    """How the rivals from each target runner's LAST start went at their NEXT start (only runs dated before today):
    how many ran again, their win rate, wins minus the market's expectation of them (the race was stronger than it
    looked), the same for the rivals this horse beat, and a has-data flag. History rows h_*: every stored run."""
    h_rid = np.asarray(h_rid).astype(str); h_date = np.asarray(h_date).astype(str); h_horse = np.asarray(h_horse).astype(str)
    h_fin = np.asarray(h_fin, float); h_q = np.asarray(h_q, float)
    race_rows = {}
    for k, r in enumerate(h_rid): race_rows.setdefault(r, []).append(k)
    horse_rows = {}
    for k in range(len(h_rid)): horse_rows.setdefault(h_horse[k], []).append(k)
    for h in horse_rows: horse_rows[h].sort(key=lambda k: h_date[k])
    race_date = {r: h_date[rows[0]] for r, rows in race_rows.items()}
    n = len(t_last_rid); n_next = np.full(n, np.nan); nxt_win = np.full(n, np.nan); nxt_beat = np.full(n, np.nan); nxt_bq = np.full(n, np.nan)
    for k in range(n):
        r = str(t_last_rid[k]); today = str(t_date[k])
        if r not in race_rows: continue
        rows = [x for x in race_rows[r] if h_horse[x] != str(t_horse[k])]
        if not rows: continue
        rd = race_date[r]; my_fin = t_fin_in_last[k]
        wins = []; qs = []; bw = []; bqs = []
        for x in rows:
            nk = next((y for y in horse_rows.get(h_horse[x], []) if h_date[y] > rd and h_date[y] < today), None)
            if nk is None: continue
            w = float(h_fin[nk] == 1); wins.append(w); qs.append(h_q[nk])
            if np.isfinite(my_fin) and np.isfinite(h_fin[x]) and h_fin[x] > my_fin: bw.append(w); bqs.append(h_q[nk])
        if wins: n_next[k] = len(wins); nxt_win[k] = np.mean(wins); nxt_beat[k] = np.sum(wins) - np.sum(qs)
        if bw: nxt_bq[k] = np.mean(bw) - np.mean(bqs)
    z = lambda v: np.nan_to_num(v, nan=0.0)
    return np.column_stack([z(n_next), z(nxt_win), z(nxt_beat), z(nxt_bq), np.isfinite(n_next).astype(float), _rrel(z(nxt_beat), ri, nR)])

def last_start(P, past_fields, past_race_ids):
    """(last race-start id, this horse's finish in it) per runner; trials skipped."""
    f = {str(n): i for i, n in enumerate(past_fields)}; Pf = np.asarray(P, float)
    tr = Pf[:, :, f["trial"]] == 1; fin = Pf[:, :, f["finish"]]; real = ~tr & np.isfinite(fin) & (fin > 0)
    pr = np.asarray(past_race_ids).astype(str); out_id = np.full(len(pr), "", dtype=object); out_fin = np.full(len(pr), np.nan)
    for k in range(len(pr)):
        idx = np.where(real[k])[0]
        if len(idx): out_id[k] = pr[k, idx[0]]; out_fin[k] = fin[k, idx[0]]
    return out_id, out_fin
