"""v9 inputs vs v10 inputs (gear detail + past price moves) on PROFIT, not just closeness to BSP (15 Oct 2026, founder:
"how much better is our model now with the updates we made this morning"). Stage-1 trees, 3 seeds each, trained before
3 Jun 2026, scored on the races from 3 Jun under the live BetMatic rules (3 steps sized at the next step, 5%-shaded
minimum, 3x ceiling, $1.60-$15, 16c deduction) at Form King's opening price. python3.13 t_v10_profit.py"""
import numpy as np, time, collections, lab, bench as b, stake_rule
D = b.load("ds/model_ds_v10.npz")
import price_day as pdm, stage2
ri = D["race_idx"]; nR = D["n_races"]
F, nm = pdm.inputs()
TR = stage2.trials(D["P"], D["past_fields"], ri); SEC = stage2.sections(D["S"], D["sec_fields"], D["P"], D["past_fields"], ri, nR)
F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
nm = list(nm) + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])]
old = open("F9_names.txt").read().split("\n")
lab.D = D; lab.ri0 = ri
races = np.arange(nR); hold = races[D["date"] >= "2026-06-03"]; train = races[D["date"] < "2026-06-03"]
q = D["q"]; hm = np.isin(ri, hold)
def fit(cols, label, seeds=3):
    FF = F[:, cols]; NN = [nm[j] for j in cols]; preds = []
    for s in range(seeds):
        t1 = time.time(); bst, _ = lab.train(FF, NN, train, q, params=dict(feature_fraction=0.2, extra_trees=True), seed=s, fixed_rounds=4000)
        preds.append(np.log(b.softmax_races(bst.predict(FF)))); print(f"{label} seed {s} {time.time()-t1:.0f}s", flush=True)
    return b.softmax_races(np.mean(preds, 0))
P9 = fit([j for j, x in enumerate(nm) if x in old], "v9"); P10 = fit(list(range(len(nm))), "v10")
np.savez("v10_profit_preds.npz", p9=P9, p10=P10, hold=hm)
o = np.asarray(D["open"], float); bs = np.asarray(D["bsp"], float); won = np.asarray(D["finish"], float) == 1
okp = np.isfinite(o) & (o > 1); fld = np.bincount(ri, minlength=nR)[ri]; race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0
meet = np.char.add(D["track"][ri].astype(str), np.char.add("|", D["date"][ri].astype(str))); jk = D["jockey"].astype(str)
cnt = collections.Counter(zip(meet, jk)); only = np.array([cnt[(m, x)] == 1 for m, x in zip(meet, jk)])
DED = 0.16; TIERS = (1.0, 1.25, 1.5)
def run(pm):
    base = hm & race_ok[ri] & np.isfinite(bs) & (pm > 0); qq = 1 / np.maximum(pm, 1e-9)
    mo = 0.95 * (1.2 / np.maximum(pm, 1e-9) ** 0.82) ** (1 / 0.78); n = st = pl = w = 0
    for i in np.where(base & (qq >= 1.6) & (qq <= 15) & (o >= mo) & (o < 3 * qq))[0]:
        ch = lambda t: pm[i] ** 0.82 * t ** -0.22
        ts = [mo[i] * s for s in TIERS if mo[i] * s < 3 * qq[i]]; tot = prev = 0.0
        for k, t in enumerate(ts):
            tp = ts[k + 1] if k + 1 < len(ts) else t
            s_ = stake_rule.stake(ch(tp), tp, only[i], fld[i]); add = max(0.0, s_ - prev); prev = max(prev, s_)
            if o[i] >= t: tot += add
        if tot > 0:
            n += 1; st += tot; w += won[i]; pl += tot * (o[i] - 1) * (1 - DED) if won[i] else -tot
    return n, w, st, pl
def kl(p):
    hri = np.unique(ri[hm], return_inverse=True)[1]; nh = hri.max() + 1; qh = q[hm]; ph = p[hm]
    ok = np.bincount(hri, weights=(qh > 0), minlength=nh) == np.bincount(hri, minlength=nh); m = ok[hri]
    return np.sum(np.where(qh[m] > 0, qh[m] * np.log(np.maximum(qh[m], 1e-300) / np.maximum(ph[m], 1e-12)), 0)) / ok.sum()
print("\n| inputs | KL to BSP | bets | winners | staked | profit | ROI |\n|---|---|---|---|---|---|---|")
for k, p in (("v9 (live inputs)", P9), ("v10 (+ gear detail, price moves)", P10)):
    n, w, st, pl = run(p); print(f"| {k} | {kl(p):.4f} | {n} | {int(w)} | {st:.1f}u | {pl:+.1f}u | {pl/st:+.1%} |")
