"""Do FORM LINES make the model better? (10 Nov 2026, founder: "Yes but no columns", testing Phil M's "subsequent runs
from each race" from the Form King Slack). How did the horses from a runner's recent races go at their NEXT start? A
race whose horses went on and won more than their SP said was a stronger race than its ratings showed.

Same stage-1 trees as t_trackbias_ab.py (3 seeds, 4000 rounds, blanked copy), trained on races before 3 Jun 2026,
scored on 3 Jun - 9 Nov (split at 9 Oct, the live weeks), with and without seven form-line inputs.

The inputs come from every stored past run (scripts/form_lines_rows.py): each run with the horse's next run beside it.
For a runner on race day D, only race-mates whose next run was BEFORE D count, so nothing leaks. Per runner:
  fl1_n, fl1_ae        last start: race-mates with a known next run; log((winners+1)/(winners SP expected+1))
  fl1_behind_ae        the same, only the horses it BEAT (beaten horses that went on and won: it beat good horses)
  fl1_ahead_ae         the same, only the horses that beat it (it lost to good horses)
  fl1_wins             race-mates that won next time
  fl3_n, fl3_ae        the last three races pooled
    python3.13 t_formlines_ab.py DATASET.npz FLROWS.md"""
import collections, hashlib, math, sys, time
import numpy as np
import lab, bench as b, price_day as pdm, stage2, stake_rule

D = b.load(sys.argv[1]); ri = D["race_idx"]; nR = D["n_races"]
F, nm = pdm.inputs()
TR = stage2.trials(D["P"], D["past_fields"], ri); SEC = stage2.sections(D["S"], D["sec_fields"], D["P"], D["past_fields"], ri, nR)
F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
nm = list(nm) + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])]
print(f"{len(ri)} runners, {nR} races, {F.shape[1]} inputs", flush=True)

# ---- form lines: each stored run with the horse's next run ---------------------------------------------------------
lines = open(sys.argv[2]).read().split("CSV-BEGIN")[1].split("CSV-END")[0].strip().split("\n")[1:]
byrace = collections.defaultdict(list)    # race_id -> [(horse tag, finish, next_date, next_won, next_inv_sp)]
for x in (l.split(",") for l in lines):
    if len(x) != 8: continue
    rid, d, tag, fin, mar, nd, nw, inv = x
    byrace[rid].append((tag, int(fin), nd, int(nw) if nw else 0, float(inv) if inv else 0.0))
print(f"{len(lines)} stored runs in {len(byrace)} races")

rdate = D["date"].astype(str); date = rdate[ri]
tag = np.array([hashlib.sha1(h.encode()).hexdigest()[:10] for h in D["horse_id"]])
P, pf = D["P"], list(D["past_fields"]); PR = D["past_race_ids"]
trial = np.nan_to_num(P[:, :, pf.index("trial")]) > 0; pfin = P[:, :, pf.index("finish")]


def tally(rid, me, my_fin, day):
    """race-mates of `me` in race `rid` whose next run came before `day`: (n, wins, expected) for all / behind / ahead."""
    out = np.zeros((3, 3))
    for t, f, nd, nw, inv in byrace.get(rid, ()):
        if t == me or not nd or nd >= day or inv <= 0: continue
        for g, ok in enumerate((True, my_fin is not None and f > my_fin, my_fin is not None and f < my_fin)):
            if ok: out[g] += (1, nw, inv)
    return out


ae = lambda w, e: math.log((w + 1) / (e + 1))
FL = np.full((len(ri), 7), np.nan, np.float32)
for i in range(len(ri)):
    real = [k for k in range(PR.shape[1]) if PR[i, k] and not trial[i, k]]
    if not real: continue
    k0 = real[0]; mf = int(pfin[i, k0]) if np.isfinite(pfin[i, k0]) else None
    t1 = tally(PR[i, k0], tag[i], mf, date[i])
    FL[i, 0] = t1[0, 0]
    if t1[0, 0] > 0: FL[i, 1] = ae(t1[0, 1], t1[0, 2]); FL[i, 4] = t1[0, 1]
    if t1[1, 0] > 0: FL[i, 2] = ae(t1[1, 1], t1[1, 2])
    if t1[2, 0] > 0: FL[i, 3] = ae(t1[2, 1], t1[2, 2])
    t3 = sum(tally(PR[i, k], tag[i], None, date[i]) for k in real[:3])
    FL[i, 5] = t3[0, 0]
    if t3[0, 0] > 0: FL[i, 6] = ae(t3[0, 1], t3[0, 2])
fln = ["fl1_n", "fl1_ae", "fl1_behind_ae", "fl1_ahead_ae", "fl1_wins", "fl3_n", "fl3_ae"]
for k, n in enumerate(fln):
    v = FL[:, k]; print(f"  {n:14} finite {np.isfinite(v).mean():.2f}  mean {np.nanmean(v):+.3f}  sd {np.nanstd(v):.3f}")
for lo, hi in (("2025-07-01", "2026-01-01"), ("2026-01-01", "2026-06-03"), ("2026-06-03", "2026-10-09"), ("2026-10-09", "2027-01-01")):
    m = (date >= lo) & (date < hi)
    print(f"  {lo}..{hi}: runners {m.sum()}, with 1+ race-mate known {np.mean(FL[m, 0] > 0):.2f}, "
          f"mean race-mates {np.nanmean(FL[m, 0]):.2f}, last-3 pooled {np.nanmean(FL[m, 5]):.2f}")

# does the raw figure say anything on its own? win rate against SP in the training races, by fl1_ae band
won = np.asarray(D["finish"], float) == 1; sp = np.asarray(D["sp"], float)
okm = np.isfinite(sp) & (sp > 1) & (date < "2026-06-03") & (FL[:, 0] >= 3)
print("\nTraining races, runners with 3+ race-mates known: winners against SP expected, by last-start form line")
for lo, hi in ((-9, -0.3), (-0.3, -0.1), (-0.1, 0.1), (0.1, 0.3), (0.3, 9)):
    m = okm & (FL[:, 1] >= lo) & (FL[:, 1] < hi)
    print(f"  fl1_ae {lo:+.1f}..{hi:+.1f}: {m.sum():5d} runners, {int(won[m].sum()):4d} won, expected {np.sum(1/sp[m]):6.1f}, "
          f"A/E {won[m].sum()/max(np.sum(1/sp[m]),1e-9):.2f}")

# ---- train both arms, score the holdout ----------------------------------------------------------------------------
lab.D = D; lab.ri0 = ri
races = np.arange(nR); train = races[rdate < "2026-06-03"]; q = D["q"]


def fit(FF, NN, label, seeds=3):
    preds = []
    for s in range(seeds):
        t1 = time.time(); bst, _ = lab.train(FF, NN, train, q, params=dict(feature_fraction=0.2, extra_trees=True), seed=s, fixed_rounds=4000)
        preds.append(np.log(b.softmax_races(bst.predict(FF)))); print(f"{label} seed {s} {time.time()-t1:.0f}s", flush=True)
    return b.softmax_races(np.mean(preds, 0)), bst


P0, _ = fit(F, nm, "base")
F1 = np.hstack([F, FL]); P1, bst1 = fit(F1, nm + fln, "+form lines")
np.savez("formlines_ab_preds.npz", p0=P0, p1=P1)
imp = bst1.feature_importance("gain"); tot = imp.sum()
print("form-line share of the model's gain:", ", ".join(f"{n} {100*imp[len(nm)+k]/tot:.2f}%" for k, n in enumerate(fln)))

o = np.asarray(D["open"], float); bs = np.asarray(D["bsp"], float)
okp = np.isfinite(o) & (o > 1); race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0
field = np.bincount(ri, minlength=nR)[ri]
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
    for k, p in (("current inputs", P0), ("+ form lines", P1)):
        n, w, st, pl = run(p, hm)
        print(f"| {pname} | {k} | {kl(p, hm):.4f} | {ll(p, hm):.4f} | {n} | {int(w)} | {st:.1f}u | {pl:+.1f}u | {pl/max(st,1e-9):+.1%} |")
