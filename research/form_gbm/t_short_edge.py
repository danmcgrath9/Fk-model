"""A smaller edge on short-priced horses (16 Oct 2026, founder: "why do we never bet sub $4 horses ... backtest a small
value on those horses and see if its a positive ROI"). Same holdout, model (v10 stage-1 trees, v10_profit_preds.npz from
t_v10_profit.py) and BetMatic rules as t_v10_profit.py (3 steps sized at the next step, 5%-shaded minimum, 3x ceiling,
$1.60-$15, 16c deduction, filled at Form King's opening price); the only change is the edge in the minimum odds for
runners we price under $4: 0.95 x (EDGE / p^0.82)^(1/0.78), live EDGE 1.2.
python3.13 t_short_edge.py MODEL_DIR   (the folder holding ds/model_ds_v10.npz and v10_profit_preds.npz)"""
import numpy as np, collections, os, sys
M = sys.argv[1]; sys.path.insert(0, M); os.chdir(M)
import bench as b, stake_rule
D = b.load("ds/model_ds_v10.npz"); R = np.load("v10_profit_preds.npz"); P = R["p10"]; hm = R["hold"]
ri = D["race_idx"]; nR = D["n_races"]
o = np.asarray(D["open"], float); bs = np.asarray(D["bsp"], float); won = np.asarray(D["finish"], float) == 1
okp = np.isfinite(o) & (o > 1); fld = np.bincount(ri, minlength=nR)[ri]; race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0
meet = np.char.add(D["track"][ri].astype(str), np.char.add("|", D["date"][ri].astype(str))); jk = D["jockey"].astype(str)
cnt = collections.Counter(zip(meet, jk)); only = np.array([cnt[(m, x)] == 1 for m, x in zip(meet, jk)])
DED = 0.16; TIERS = (1.0, 1.25, 1.5)
def run(pm, short_edge, cut=4.0):
    base = hm & race_ok[ri] & np.isfinite(bs) & (pm > 0); qq = 1 / np.maximum(pm, 1e-9)
    edge = np.where(qq < cut, short_edge, 1.2)
    mo = 0.95 * (edge / np.maximum(pm, 1e-9) ** 0.82) ** (1 / 0.78)
    out = collections.defaultdict(lambda: [0, 0, 0.0, 0.0])
    for i in np.where(base & (qq >= 1.6) & (qq <= 15) & (o >= mo) & (o < 3 * qq))[0]:
        ch = lambda t: pm[i] ** 0.82 * t ** -0.22
        ts = [mo[i] * s for s in TIERS if mo[i] * s < 3 * qq[i]]; tot = prev = 0.0
        for k, t in enumerate(ts):
            tp = ts[k + 1] if k + 1 < len(ts) else t
            s_ = stake_rule.stake(ch(tp), tp, only[i], fld[i]); add = max(0.0, s_ - prev); prev = max(prev, s_)
            if o[i] >= t: tot += add
        if tot > 0:
            band = "under $3" if qq[i] < 3 else ("$3-$4" if qq[i] < 4 else "$4 and over")
            pl = tot * (o[i] - 1) * (1 - DED) if won[i] else -tot
            for key in (band, "all"):
                r = out[key]; r[0] += 1; r[1] += won[i]; r[2] += tot; r[3] += pl
    return out
print(f"holdout races: {len(np.unique(ri[hm]))} (from {sorted(set(D['date'][ri[hm]].tolist()))[0]})\n")
print("| edge for horses we price under $4 | band | bets | winners | staked | profit | ROI |\n|---|---|---|---|---|---|---|")
for e in (1.2, 1.15, 1.10, 1.05, 1.0):
    out = run(P, e)
    for band in ("under $3", "$3-$4", "$4 and over", "all"):
        n, w, st, pl = out.get(band, [0, 0, 0.0, 0.0])
        lab_ = f"{e:.2f}" + (" (live)" if e == 1.2 else "")
        print(f"| {lab_} | {band} | {n} | {int(w)} | {st:.1f}u | {pl:+.1f}u | {(pl/st if st else 0):+.1%} |")
