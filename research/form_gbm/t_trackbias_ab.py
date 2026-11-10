"""Does a TRACK BIAS input make the model better? (10 Nov 2026, founder: "have a go for every track and see if it makes
our model better"). Same stage-1 trees as t_v10_profit.py (3 seeds, 4000 rounds, blanked copy), trained on races
before 3 Jun 2026, scored on 3 Jun - 9 Nov (split at 9 Oct, the live weeks), with and without eight track-bias inputs.

The inputs come from every stored past run (scripts/track_bias_table.py --rows), counted ONLY from runs before each
race's own date, so nothing leaks: per track and distance band, how much leaders / on-pace / midfield / back-markers and
each barrier group beat their SP, against the same band at every track (the model already learns the average pace and
barrier effect; these are the track's own difference), shrunk toward zero where the track has few runs. Per runner: the
track's figure for its speedmap position today, for where it usually settles, for its barrier; per race: the leader,
back-marker, inside and wide figures, and how many runs stand behind them.
    python3.13 t_trackbias_ab.py DATASET.npz ROWS.md"""
import collections, math, re, sys, time
import numpy as np
import lab, bench as b, price_day as pdm, stage2, stake_rule

D = b.load(sys.argv[1]); ri = D["race_idx"]; nR = D["n_races"]
F, nm = pdm.inputs()
TR = stage2.trials(D["P"], D["past_fields"], ri); SEC = stage2.sections(D["S"], D["sec_fields"], D["P"], D["past_fields"], ri, nR)
F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
nm = list(nm) + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])]
print(f"{len(ri)} runners, {nR} races, {F.shape[1]} inputs", flush=True)

# ---- track bias, counted from runs strictly before each race's date ------------------------------------------------
lines = open(sys.argv[2]).read().split("CSV-BEGIN")[1].split("CSV-END")[0].strip().split("\n")[1:]
R = [x for x in (l.split(",") for l in lines) if len(x) == 7 and x[6] not in ("nan", "inf") and float(x[6]) > 0]; R.sort(key=lambda x: x[0])   # an SP Form King left blank is no run
band = lambda d: "-1100" if d <= 1100 else "1101-1300" if d <= 1300 else "1301-1600" if d <= 1600 else "1601-2000" if d <= 2000 else "2001-"
SG = ("1", "2-3", "4-6", "7+"); BG = ("1-3", "4-6", "7-9", "10+")
cell = collections.defaultdict(lambda: [0.0, 0.0]); glob = collections.defaultdict(lambda: [0.0, 0.0]); ncell = collections.Counter()
K = 8.0


def dev(t, bd, kind, g):
    Wc, Ec = cell[(t, bd, "all", "")]; Wg, Eg = glob[(bd, "all", "")]
    if Eg <= 0: return 0.0
    kg = Wg / Eg; kc = Wc / Ec if Ec > 0 and Wc > 0 else kg
    wg, eg = glob[(bd, kind, g)]
    Rg = wg / (eg * kg) if eg > 0 and wg > 0 else 1.0
    w, e = cell[(t, bd, kind, g)]
    r = (w + K * Rg) / (e * kc + K)
    return math.log(r / Rg)


rtrack = np.array([re.sub(r"[^a-z]", "", str(t).lower()) for t in D["track"]]); rdate = D["date"].astype(str)
rdist = D["distance"].astype(float); order = np.argsort(rdate, kind="stable")
racef = np.full((nR, 8 + 1), np.nan)   # 4 settle devs, 4 barrier devs, log runs
j = 0
for r in order:
    while j < len(R) and R[j][0] < rdate[r]:
        d_, t, bd, sg, bg, w, inv = R[j]; w = float(w); inv = float(inv)
        for key in ((t, bd, "all", ""),) + (((t, bd, "settle", sg),) if sg else ()) + (((t, bd, "barrier", bg),) if bg else ()):
            cell[key][0] += w; cell[key][1] += inv
            gk = (key[1], key[2], key[3]); glob[gk][0] += w; glob[gk][1] += inv
        ncell[(t, bd)] += 1; j += 1
    t, bd = rtrack[r], band(rdist[r])
    racef[r, :4] = [dev(t, bd, "settle", g) for g in SG]
    racef[r, 4:8] = [dev(t, bd, "barrier", g) for g in BG]
    racef[r, 8] = math.log1p(ncell[(t, bd)])
col = lambda n: D["X"][:, list(D["cols"]).index(n)].astype(float)
field = np.bincount(ri, minlength=nR)[ri]
pred, share, bar = col("sm_predicted_position"), col("raw_settle_share"), col("barrier")
sidx = lambda p: np.where(~np.isfinite(p) | (p < 1), -1, np.where(p <= 1, 0, np.where(p <= 3, 1, np.where(p <= 6, 2, 3))))
bidx = lambda x: np.where(~np.isfinite(x) | (x < 1), -1, np.where(x <= 3, 0, np.where(x <= 6, 1, np.where(x <= 9, 2, 3))))
rf = racef[ri]
pick = lambda idx, off: np.where(idx >= 0, rf[np.arange(len(ri)), np.maximum(idx, 0) + off], np.nan)
habit_pos = 1 + np.round(share * (field - 1))
TB = np.column_stack([pick(sidx(pred), 0), pick(sidx(habit_pos), 0), pick(bidx(bar), 4),
                      rf[:, 0], rf[:, 3], rf[:, 4], rf[:, 7], rf[:, 8]]).astype(np.float32)
tbn = ["tb_style_today", "tb_style_habit", "tb_gate", "tb_lead", "tb_back", "tb_inside", "tb_wide", "tb_runs"]
for k, n in enumerate(tbn):
    v = TB[:, k]; print(f"  {n:16} finite {np.isfinite(v).mean():.2f}  mean {np.nanmean(v):+.3f}  sd {np.nanstd(v):.3f}")
lsl = (rtrack == "sandownlakeside") & (rdist == 1200)
if lsl.any():
    print("  Sandown Lakeside 1200m, latest race: settle devs", np.round(racef[np.where(lsl)[0][-1], :4], 2), "barrier devs",
          np.round(racef[np.where(lsl)[0][-1], 4:8], 2))

# ---- train both arms, score the holdout ----------------------------------------------------------------------------
lab.D = D; lab.ri0 = ri
races = np.arange(nR); train = races[rdate < "2026-06-03"]; q = D["q"]
hold = ri_in = None
date = rdate[ri]


def fit(FF, NN, label, seeds=3):
    preds = []
    for s in range(seeds):
        t1 = time.time(); bst, _ = lab.train(FF, NN, train, q, params=dict(feature_fraction=0.2, extra_trees=True), seed=s, fixed_rounds=4000)
        preds.append(np.log(b.softmax_races(bst.predict(FF)))); print(f"{label} seed {s} {time.time()-t1:.0f}s", flush=True)
    return b.softmax_races(np.mean(preds, 0)), bst


P0, _ = fit(F, nm, "base")
F1 = np.hstack([F, TB]); P1, bst1 = fit(F1, nm + tbn, "+track bias")
np.savez("trackbias_ab_preds.npz", p0=P0, p1=P1)
imp = bst1.feature_importance("gain"); tot = imp.sum()
print("track-bias share of the model's gain:", ", ".join(f"{n} {100*imp[len(nm)+k]/tot:.2f}%" for k, n in enumerate(tbn)))

o = np.asarray(D["open"], float); bs = np.asarray(D["bsp"], float); won = np.asarray(D["finish"], float) == 1
okp = np.isfinite(o) & (o > 1); race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0
meet = np.char.add(D["track"][ri].astype(str), np.char.add("|", date)); jk = D["jockey"].astype(str)
cnt = collections.Counter(zip(meet, jk)); only = np.array([cnt[(m, x)] == 1 for m, x in zip(meet, jk)])
DED = 0.16; TIERS = (1.0, 1.25, 1.5)


def run(pm, hm):
    base = hm & race_ok[ri] & np.isfinite(bs) & (pm > 0); qq = 1 / np.maximum(pm, 1e-9)
    mo = 0.95 * (1.2 / np.maximum(pm, 1e-9) ** 0.82) ** (1 / 0.78); n = st = pl = w = 0
    for i in np.where(base & (qq >= 1.6) & (qq <= 15) & (o >= mo) & (o < 3 * qq))[0]:
        ch = lambda t: pm[i] ** 0.82 * t ** -0.22
        ts = [mo[i] * s for s in TIERS if mo[i] * s < 3 * qq[i]]; tot = prev = 0.0
        for k, t in enumerate(ts):
            tp = ts[k + 1] if k + 1 < len(ts) else t
            s_ = stake_rule.stake(ch(tp), tp, only[i], field[i]); add = max(0.0, s_ - prev); prev = max(prev, s_)
            if o[i] >= t: tot += add
        if tot > 0:
            n += 1; st += tot; w += won[i]; pl += tot * (o[i] - 1) * (1 - DED) if won[i] else -tot
    return n, w, st, pl


def kl(p, hm):
    hri = np.unique(ri[hm], return_inverse=True)[1]; nh = hri.max() + 1; qh = q[hm]; ph = p[hm]
    ok = np.bincount(hri, weights=(qh > 0), minlength=nh) == np.bincount(hri, minlength=nh); m = ok[hri]
    return np.sum(np.where(qh[m] > 0, qh[m] * np.log(np.maximum(qh[m], 1e-300) / np.maximum(ph[m], 1e-12)), 0)) / ok.sum()


def ll(p, hm):
    m = hm & won; return -np.mean(np.log(np.maximum(p[m], 1e-12)))


print("\n| period | inputs | KL to BSP | log loss (winners) | bets | winners | staked | profit | ROI |\n|---|---|---|---|---|---|---|---|---|")
for pname, hm in (("3 Jun - 8 Oct", (date >= "2026-06-03") & (date < "2026-10-09")), ("9 Oct - 9 Nov (live weeks)", date >= "2026-10-09"),
                  ("all 3 Jun - 9 Nov", date >= "2026-06-03")):
    for k, p in (("current inputs", P0), ("+ track bias", P1)):
        n, w, st, pl = run(p, hm)
        print(f"| {pname} | {k} | {kl(p, hm):.4f} | {ll(p, hm):.4f} | {n} | {int(w)} | {st:.1f}u | {pl:+.1f}u | {pl/max(st,1e-9):+.1%} |")
