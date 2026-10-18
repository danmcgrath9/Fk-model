"""Stake rules head to head (18 Oct 2026, founder: "what's the go with this max bet situation? Surely there can be max
bets without stupid rules, can we test everything?"). Same bets as live (v10 stage-1 preds from t_v10_profit.py, BetMatic
rules at the open: 5%-shaded minimum at edge 1.2, 3 steps sized at the next step's price, 3x ceiling, $1.60-$15, 16c
deduction, filled at Form King's opening price); only the stake function changes. Holdout = races from 3 Jun.
python3.13 t_stakes.py MODEL_DIR   (folder holding ds/model_ds_v10.npz and v10_profit_preds.npz)"""
import numpy as np, collections, os, sys
M = sys.argv[1]; sys.path.insert(0, M); os.chdir(M)
import bench as b
D = b.load("ds/model_ds_v10.npz"); R = np.load("v10_profit_preds.npz"); P = R["p10"]; hm = R["hold"]
ri = D["race_idx"]; nR = D["n_races"]
o = np.asarray(D["open"], float); bs = np.asarray(D["bsp"], float); won = np.asarray(D["finish"], float) == 1
okp = np.isfinite(o) & (o > 1); fld = np.bincount(ri, minlength=nR)[ri]; race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0
dates = D["date"][ri].astype(str)
meet = np.char.add(D["track"][ri].astype(str), np.char.add("|", dates)); jk = D["jockey"].astype(str)
cnt = collections.Counter(zip(meet, jk)); only = np.array([cnt[(m, x)] == 1 for m, x in zip(meet, jk)])
DED = 0.16; TIERS = (1.0, 1.25, 1.5); SCALE = 5 / 8

def kelly(pp, price, mult):            # Kelly x mult on the blend sqrt(chance x price), in units before the 5/8 scale
    return mult * max(0.0, ((pp * price) ** 0.5 - 1) / (price - 1))

def rule_live(pp, price, ride, field):  # stake_rule.py today
    s = min(4.0, kelly(pp, price, 75)) * (2.0 if ride else 1.0) * (1.5 if field <= 8 else 1.0)
    return min(s, 8.0) * SCALE
def rule_plain(cap, mult=75):           # no only-ride / small-field multipliers: edge alone sets the size, up to cap units
    return lambda pp, price, ride, field: min(cap, kelly(pp, price, mult) * SCALE)
def rule_edge_bands(pp, price, ride, field):  # flat units by edge (chance x price): simple bands, no Kelly
    ev = pp * price
    return 5.0 if ev >= 1.6 else 4.0 if ev >= 1.45 else 3.0 if ev >= 1.35 else 2.0 if ev >= 1.25 else 1.0
def rule_live_cap(cap):                 # live multipliers kept, ceiling lifted
    return lambda pp, price, ride, field: min(min(cap / SCALE, kelly(pp, price, 75)) * (2.0 if ride else 1.0) * (1.5 if field <= 8 else 1.0), 8.0) * SCALE

def rule_live_mult(mult, cap=4.0):      # live multipliers on a bigger Kelly base, still max 5u after the 5/8 scale
    return lambda pp, price, ride, field: min(min(cap, kelly(pp, price, mult)) * (2.0 if ride else 1.0) * (1.5 if field <= 8 else 1.0), 8.0) * SCALE

RULES = [
    ("live (cap 4, x2 only ride, x1.5 field<=8, ceiling 8, x5/8)", rule_live),
    ("plain Kelly x75, max 2.5u (live with no multipliers)", rule_plain(2.5)),
    ("plain Kelly x75, max 5u", rule_plain(5.0)),
    ("plain Kelly x100, max 5u", rule_plain(5.0, 100)),
    ("plain Kelly x125, max 5u", rule_plain(5.0, 125)),
    ("plain Kelly x150, max 5u", rule_plain(5.0, 150)),
    ("edge bands 1-5u (chance x price)", rule_edge_bands),
    ("live multipliers on Kelly x100", rule_live_mult(100)),
    ("live multipliers on Kelly x125", rule_live_mult(125)),
    ("live multipliers on Kelly x125, base cap 8 (max 5u)", rule_live_mult(125, 8.0)),
]

def run(mask, rule):
    mo_edge = 1.2; qq = 1 / np.maximum(P, 1e-9)
    mo = 0.95 * (mo_edge / np.maximum(P, 1e-9) ** 0.82) ** (1 / 0.78)
    base = mask & race_ok[ri] & np.isfinite(bs) & (P > 0)
    rows = []
    for i in np.where(base & (qq >= 1.6) & (qq <= 15) & (o >= mo) & (o < 3 * qq))[0]:
        ch = lambda t: P[i] ** 0.82 * t ** -0.22
        ts = [mo[i] * s for s in TIERS if mo[i] * s < 3 * qq[i]]; tot = prev = 0.0
        for k, t in enumerate(ts):
            tp = ts[k + 1] if k + 1 < len(ts) else t
            s_ = rule(ch(tp), tp, only[i], fld[i]); add = max(0.0, s_ - prev); prev = max(prev, s_)
            if o[i] >= t: tot += add
        if tot > 0:
            pl = tot * (o[i] - 1) * (1 - DED) if won[i] else -tot
            rows.append((dates[i], ri[i], tot, pl, won[i]))
    rows.sort()
    st = np.array([r[2] for r in rows]); pl = np.array([r[3] for r in rows])
    cum = np.cumsum(pl); dd = float(np.max(np.maximum.accumulate(np.concatenate([[0], cum]))[1:] - cum)) if len(cum) else 0
    big = st >= 4.5
    return dict(n=len(rows), w=int(sum(r[4] for r in rows)), st=st.sum(), pl=pl.sum(), dd=dd, nbig=int(big.sum()),
                bigpl=pl[big].sum(), bigst=st[big].sum(), avg=st.mean() if len(st) else 0)

for name, mask in (("holdout (from 3 Jun)", hm), ("before the holdout", ~hm)):
    print(f"\n### {name}\n\n| stake rule | bets | avg stake | staked | profit | ROI | worst drawdown | bets 4.5u+ | their profit |\n|---|---|---|---|---|---|---|---|---|")
    for lab, rule in RULES:
        r = run(mask, rule)
        print(f"| {lab} | {r['n']} | {r['avg']:.2f}u | {r['st']:.0f}u | {r['pl']:+.0f}u | {r['pl']/r['st']:+.1%} | {r['dd']:.0f}u | {r['nbig']} | {r['bigpl']:+.0f}u ({(r['bigpl']/r['bigst'] if r['bigst'] else 0):+.0%}) |")
