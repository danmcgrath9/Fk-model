"""Does training on every state make the Victorian price better, and how good is it elsewhere? (11 Nov 2026, founder:
"I want the training for other states as well ... I want the same model", with the national archive the source of
the other states; queued since 25 Oct as "Retrain on all states, score Jun-Oct Victoria against v10, both halves;
live only if closer to BSP in both".)

Same stage-1 trees as t_formlines_ab.py (3 seeds, 4000 rounds, blanked copy), three ways:
  VIC       trained on Victorian races only, inputs built over the Victorian dataset (today's live situation)
  ALL       trained on every state's races, inputs built over the all-states dataset
  ALL+ST    ALL, plus the race's state as inputs (one 0/1 column a state), so the trees can tell the states apart
Scored on the races after the fold's cut that none of them saw: Victoria (KL to BSP, winners' log loss, and the live
open-price rule's profit) and each other state on its own, where the VIC arm's trees also price the other states'
runners (inputs built over the all-states dataset, columns matched by name), which is what pricing another state with
a Victorian model would look like.

    python3.13 t_allstates.py DS_VIC.npz DS_ALL.npz [A|B]
A trains before 3 Jun 2026 and scores 3 Jun on; B trains before 1 Jan 2026 and scores 1 Jan - 2 Jun (the night's folds).
DS_ALL is fk export with state ALL and the history-states release (the archive); DS_VIC is the live Victorian export."""
import collections, os, sys, time
import numpy as np
import lab, bench as b, price_day as pdm, stage2, stake_rule

FOLD = sys.argv[3] if len(sys.argv) > 3 else "A"
CUT = {"A": "2026-06-03", "B": "2026-01-01"}[FOLD]
END = {"A": "2027-01-01", "B": "2026-06-03"}[FOLD]
PERIODS = {"A": (("3 Jun - 8 Oct", "2026-06-03", "2026-10-09"), ("9 Oct on (live weeks)", "2026-10-09", "2027-01-01"),
                 ("all 3 Jun on", "2026-06-03", "2027-01-01")),
           "B": (("1 Jan - 17 Mar", "2026-01-01", "2026-03-18"), ("18 Mar - 2 Jun", "2026-03-18", "2026-06-03"),
                 ("all 1 Jan - 2 Jun", "2026-01-01", "2026-06-03"))}[FOLD]
DED, TIERS = 0.16, (1.0, 1.25, 1.5)
SEEDS, ROUNDS = (1, 150) if os.environ.get("QUICK") else (3, 4000)   # QUICK=1: a smoke test of the plumbing only


def build(path):
    """Load a dataset and its stage-1 inputs (trials and section splits included), as the live pricer builds them."""
    D = b.load(path); ri = D["race_idx"]; nR = D["n_races"]
    pdm.install(D)
    F, nm = pdm.inputs()
    TR = stage2.trials(D["P"], D["past_fields"], ri); SEC = stage2.sections(D["S"], D["sec_fields"], D["P"], D["past_fields"], ri, nR)
    F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
    nm = list(nm) + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])]
    st = np.asarray(D["state"]).astype(str) if "state" in D else np.full(nR, "VIC")
    return D, F, nm, st


def fit(D, F, NN, label, seeds=None):
    seeds = seeds or SEEDS
    lab.D = D; lab.ri0 = D["race_idx"]
    rdate = np.asarray(D["date"]).astype(str); train = np.arange(D["n_races"])[rdate < CUT]
    preds, bsts = [], []
    for s in range(seeds):
        t1 = time.time()
        bst, _ = lab.train(F, NN, train, D["q"], params=dict(feature_fraction=0.2, extra_trees=True), seed=s, fixed_rounds=ROUNDS)
        preds.append(np.log(b.softmax_races(bst.predict(F)))); bsts.append(bst); print(f"{label} seed {s} {time.time()-t1:.0f}s", flush=True)
    return b.softmax_races(np.mean(preds, 0)), bsts


def scorer(D):
    ri = D["race_idx"]; nR = D["n_races"]; date = np.asarray(D["date"]).astype(str)[ri]
    won = np.asarray(D["finish"], float) == 1; q = D["q"]
    o = np.asarray(D["open"], float); bs = np.asarray(D["bsp"], float)
    okp = np.isfinite(o) & (o > 1); race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0
    field = np.bincount(ri, minlength=nR)[ri]
    meet = np.char.add(np.asarray(D["track"]).astype(str)[ri], np.char.add("|", date)); jk = np.asarray(D["jockey"]).astype(str)
    cnt = collections.Counter(zip(meet, jk)); only = np.array([cnt[(m, x)] == 1 for m, x in zip(meet, jk)])

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
        if not hm.any(): return float("nan")
        hri = np.unique(ri[hm], return_inverse=True)[1]; nh = hri.max() + 1; qh = q[hm]; ph = p[hm]
        ok = np.bincount(hri, weights=(qh > 0), minlength=nh) == np.bincount(hri, minlength=nh); m = ok[hri]
        return np.sum(np.where(qh[m] > 0, qh[m] * np.log(np.maximum(qh[m], 1e-300) / np.maximum(ph[m], 1e-12)), 0)) / max(ok.sum(), 1)

    def ll(p, hm):
        m = hm & won; return -np.mean(np.log(np.maximum(p[m], 1e-12))) if m.any() else float("nan")
    return date, run, kl, ll


# ---- Victoria alone ----------------------------------------------------------------------------------------------
DV, FV, nmV, stV = build(sys.argv[1])
print(f"VIC dataset: {len(DV['race_idx'])} runners, {DV['n_races']} races, {FV.shape[1]} inputs", flush=True)
PV, bstsV = fit(DV, FV, nmV, "VIC")
key = lambda D: np.char.add(np.asarray(D["race_id"]).astype(str)[D["race_idx"]], np.char.add("|", np.asarray(D["horse_id"]).astype(str)))
kV = key(DV)
dateV, runV, klV, llV = scorer(DV)

# ---- every state -------------------------------------------------------------------------------------------------
DA, FA, nmA, stA = build(sys.argv[2])
rstA = stA[DA["race_idx"]]
print(f"ALL dataset: {len(DA['race_idx'])} runners, {DA['n_races']} races; by state: "
      + ", ".join(f"{s} {n}" for s, n in collections.Counter(stA.tolist()).most_common()), flush=True)
PA, _ = fit(DA, FA, nmA, "ALL")
STATES = sorted(set(stA.tolist()))
FS = np.hstack([FA] + [(rstA == s).astype(np.float32)[:, None] for s in STATES])
PS, bstsS = fit(DA, FS, nmA + [f"state_{s}" for s in STATES], "ALL+ST")
imp = bstsS[-1].feature_importance("gain"); tot = imp.sum()
print("state inputs' share of the gain: " + ", ".join(f"{s} {100*imp[FA.shape[1]+k]/tot:.2f}%" for k, s in enumerate(STATES)))
dateA, runA, klA, llA = scorer(DA)

# The Victorian arm's prices on the all-states rows, matched by race and horse, so all three are scored on the
# same Victorian runners (a VIC race is in both datasets; its runners must line up exactly or the row is left out).
pos = {k: i for i, k in enumerate(kV)}; kA = key(DA)
idx = np.array([pos.get(k, -1) for k in kA]); have = idx >= 0
PVA = np.where(have, PV[np.maximum(idx, 0)], np.nan)
vic_rows = (rstA == "VIC") & have
# ... and the Victorian trees on every all-states row (the other states priced by a Victorian model)
colA = {n: j for j, n in enumerate(nmA)}
FVA = np.full((FA.shape[0], len(nmV)), np.nan, np.float32)
for j, n in enumerate(nmV):
    if n in colA: FVA[:, j] = FA[:, colA[n]]
print(f"VIC model inputs found in the all-states inputs: {sum(n in colA for n in nmV)} of {len(nmV)}", flush=True)
PVX = b.softmax_races(np.mean([np.log(b.softmax_races(t.predict(FVA))) for t in bstsV], 0))   # b.D is the all-states set
vic_races_ok = np.bincount(DA["race_idx"], weights=~vic_rows & (rstA == "VIC"), minlength=DA["n_races"]) == 0
print(f"Victorian runners matched between the two datasets: {vic_rows.sum()} of {(rstA == 'VIC').sum()}", flush=True)

print(f"\n## Fold {FOLD}: trained before {CUT}\n\n### Victoria\n| period | model | KL to BSP | log loss (winners) | bets | winners | staked | profit | ROI |\n|---|---|---|---|---|---|---|---|---|")
for pname, lo, hi in PERIODS:
    hm = (dateA >= lo) & (dateA < hi) & vic_rows & vic_races_ok[DA["race_idx"]]
    for lab_, p in (("VIC", PVA), ("ALL", PA), ("ALL+ST", PS)):
        pp = np.nan_to_num(p, nan=1e-9)
        n, w, st, pl = runA(pp, hm)
        print(f"| {pname} | {lab_} | {klA(pp, hm):.4f} | {llA(pp, hm):.4f} | {n} | {int(w)} | {st:.1f}u | {pl:+.1f}u | {pl/max(st,1e-9):+.1%} |")

print(f"\n### Other states, {CUT} to {END} (races none of the models trained on)\n| state | races | model | KL to BSP | log loss (winners) | bets | profit at open | ROI |\n|---|---|---|---|---|---|---|---|")
for s in STATES:
    if s == "VIC": continue
    hm = (dateA >= CUT) & (dateA < END) & (rstA == s)
    if not hm.any(): continue
    nr = len(np.unique(DA["race_idx"][hm]))
    for lab_, p in (("VIC trees", PVX), ("ALL", PA), ("ALL+ST", PS)):
        n, w, st, pl = runA(p, hm)
        print(f"| {s} | {nr} | {lab_} | {klA(p, hm):.4f} | {llA(p, hm):.4f} | {n} | {pl:+.1f}u on {st:.0f}u | {pl/max(st,1e-9):+.1%} |")
np.savez(f"allstates_preds_{FOLD}.npz", pv=PVA, pvx=PVX, pa=PA, ps=PS)
