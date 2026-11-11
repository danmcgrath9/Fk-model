"""One model per state, never mixed (11 Nov 2026, founder: "they're all separate and train on their own states ... because
different states might have different rules", then "can't mix the states up"). For each state: a dataset of that
state's races only, its inputs built over that dataset alone (rolling jockey and trainer figures, head-to-heads, track
bias: all from that state), the same stage-1 trees as the other trials (3 seeds, 4000 rounds, blanked copy), trained
before the fold's cut and scored on that state's races after it. Victoria is in the table as the reference: its model
is the live recipe on its own races, which is what it already is.

    python3.13 t_ownstate.py DS_ALL.npz [A|B] [STATE,STATE...]
DS_ALL is fk export with state ALL (the races of every state in one file, used only as a container: each state is cut
out of it on its own before anything is built). A trains before 3 Jun 2026 and scores 3 Jun on; B trains before
1 Jan 2026 and scores 1 Jan - 2 Jun. Profit is the Victorian open-price rule on every state, a common yardstick only:
each state's own betting rules come from its own results, on paper first.
QUICK=1 is a smoke test of the plumbing (1 seed, 150 rounds)."""
import collections, os, sys, time
import numpy as np
import lab, bench as b, price_day as pdm, stage2, stake_rule

FOLD = sys.argv[2] if len(sys.argv) > 2 else "A"
WANT = [s.strip().upper() for s in sys.argv[3].split(",")] if len(sys.argv) > 3 else None
CUT = {"A": "2026-06-03", "B": "2026-01-01"}[FOLD]
PERIODS = {"A": (("3 Jun - 8 Oct", "2026-06-03", "2026-10-09"), ("9 Oct on", "2026-10-09", "2027-01-01"),
                 ("all 3 Jun on", "2026-06-03", "2027-01-01")),
           "B": (("1 Jan - 17 Mar", "2026-01-01", "2026-03-18"), ("18 Mar - 2 Jun", "2026-03-18", "2026-06-03"),
                 ("all 1 Jan - 2 Jun", "2026-01-01", "2026-06-03"))}[FOLD]
DED, TIERS = 0.16, (1.0, 1.25, 1.5)
SEEDS, ROUNDS = (1, 150) if os.environ.get("QUICK") else (3, 4000)
MIN_TRAIN = 300


def cut_state(RAW, s):
    """The races of one state, as a dataset of their own (runner and race arrays cut, race_idx renumbered)."""
    nRun, nRace = len(RAW["race_idx"]), len(RAW["race_id"])
    keep_r = np.asarray(RAW["state"]).astype(str) == s; keep_u = keep_r[RAW["race_idx"]]
    new_idx = np.cumsum(keep_r) - 1
    sub = {}
    for k, v in RAW.items():
        v = np.asarray(v)
        if k == "race_idx": sub[k] = new_idx[v[keep_u]].astype(np.int32)
        elif v.ndim and v.shape[0] == nRun: sub[k] = v[keep_u]
        elif v.ndim and v.shape[0] == nRace: sub[k] = v[keep_r]
        else: sub[k] = v
    return sub


def build(path):
    D = b.load(path); ri = D["race_idx"]; nR = D["n_races"]
    pdm.install(D)
    F, nm = pdm.inputs()
    TR = stage2.trials(D["P"], D["past_fields"], ri); SEC = stage2.sections(D["S"], D["sec_fields"], D["P"], D["past_fields"], ri, nR)
    F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
    nm = list(nm) + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])]
    return D, F, nm


def fit(D, F, NN, label):
    lab.D = D; lab.ri0 = D["race_idx"]
    train = np.arange(D["n_races"])[np.asarray(D["date"]).astype(str) < CUT]
    preds = []
    for s in range(SEEDS):
        t1 = time.time()
        bst, _ = lab.train(F, NN, train, D["q"], params=dict(feature_fraction=0.2, extra_trees=True), seed=s, fixed_rounds=ROUNDS)
        preds.append(np.log(b.softmax_races(bst.predict(F)))); print(f"{label} seed {s} {time.time()-t1:.0f}s", flush=True)
    return b.softmax_races(np.mean(preds, 0))


def score(D, p, hm):
    ri = D["race_idx"]; nR = D["n_races"]; date = np.asarray(D["date"]).astype(str)[ri]
    won = np.asarray(D["finish"], float) == 1; q = D["q"]
    o = np.asarray(D["open"], float); bs = np.asarray(D["bsp"], float)
    okp = np.isfinite(o) & (o > 1); race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0
    field = np.bincount(ri, minlength=nR)[ri]
    meet = np.char.add(np.asarray(D["track"]).astype(str)[ri], np.char.add("|", date)); jk = np.asarray(D["jockey"]).astype(str)
    cnt = collections.Counter(zip(meet, jk)); only = np.array([cnt[(m, x)] == 1 for m, x in zip(meet, jk)])
    base = hm & race_ok[ri] & np.isfinite(bs) & (p > 0); qq = 1 / np.maximum(p, 1e-9)
    mo = 0.95 * (1.2 / np.maximum(p, 1e-9) ** 0.82) ** (1 / 0.78); n = st = pl = w = 0
    for i in np.where(base & (qq >= 1.6) & (qq <= 15) & (o >= mo) & (o < 3 * qq))[0]:
        ch = lambda t: p[i] ** 0.82 * t ** -0.22
        ts = [mo[i] * s for s in TIERS if mo[i] * s < 3 * qq[i]]; tot = prev = 0.0
        for k, t in enumerate(ts):
            tp = ts[k + 1] if k + 1 < len(ts) else t
            s_ = stake_rule.stake(ch(tp), tp, only[i], field[i]); add = max(0.0, s_ - prev); prev = max(prev, s_)
            if o[i] >= t: tot += add
        if tot > 0:
            n += 1; st += tot; w += won[i]; pl += tot * (o[i] - 1) * (1 - DED) if won[i] else -tot
    hri = np.unique(ri[hm], return_inverse=True)[1]; nh = hri.max() + 1; qh = q[hm]; ph = p[hm]
    ok = np.bincount(hri, weights=(qh > 0), minlength=nh) == np.bincount(hri, minlength=nh); m = ok[hri]
    kl = np.sum(np.where(qh[m] > 0, qh[m] * np.log(np.maximum(qh[m], 1e-300) / np.maximum(ph[m], 1e-12)), 0)) / max(ok.sum(), 1)
    mw = hm & won; ll = -np.mean(np.log(np.maximum(p[mw], 1e-12))) if mw.any() else float("nan")
    return len(np.unique(ri[hm])), kl, ll, n, int(w), st, pl


RAW = dict(np.load(sys.argv[1]))
states = collections.Counter(np.asarray(RAW["state"]).astype(str).tolist())
print("races by state: " + ", ".join(f"{s} {n}" for s, n in states.most_common()), flush=True)
rows = []
for s, _ in states.most_common():
    if WANT and s not in WANT: continue
    sub = cut_state(RAW, s)
    ntrain = int((np.asarray(sub["date"]).astype(str) < CUT).sum())
    if ntrain < MIN_TRAIN:
        print(f"{s}: {ntrain} races before {CUT}, too few for a model of its own (needs {MIN_TRAIN})", flush=True); continue
    path = f"_own_{s}.npz"; np.savez(path, **sub)
    D, F, nm = build(path); os.remove(path)
    print(f"{s}: {len(D['race_idx'])} runners, {D['n_races']} races ({ntrain} to train on), {F.shape[1]} inputs", flush=True)
    p = fit(D, F, nm, s)
    date = np.asarray(D["date"]).astype(str)[D["race_idx"]]
    for pname, lo, hi in PERIODS:
        hm = (date >= lo) & (date < hi)
        if hm.any(): rows.append((s, pname) + score(D, p, hm))
    np.save(f"ownstate_{s}_{FOLD}.npy", p)

print(f"\n## Fold {FOLD}: each state's own model, trained before {CUT}\n")
print("| state | period | races | KL to BSP | log loss (winners) | bets | winners | staked | profit (VIC open rule) | ROI |\n|---|---|---|---|---|---|---|---|---|---|")
for s, pname, nr, kl, ll, n, w, st, pl in rows:
    print(f"| {s} | {pname} | {nr} | {kl:.4f} | {ll:.4f} | {n} | {w} | {st:.1f}u | {pl:+.1f}u | {pl/max(st,1e-9):+.1%} |")
