"""How to stake BetMatic orders so they invest closer to the sheet (14 Oct 2026, founder: "we wanted to be 8.6 invested
but on the BetMatic theory we have less, is there a way to get more?"). Same holdout and filters as t_betmatic.py, orders
at the 5%-shaded minimum; the stake is a ladder of orders at rising prices, each adding what the stake rule gives at its
price (our chance at that open from the pre-open blend p_model^0.82 x open^-0.22, no rescale). Variants: the steps
(3 coarse vs 8 fine) and sizing each step at the price it starts (bottom) or the next step's price (top).
Also: the price band ($1.60-$15) checked on the blended price at the order's own price, not on the model price alone."""
import numpy as np, bench as b, collections, stake_rule
D = b.load(); ri = D["race_idx"]; nR = D["n_races"]; z = np.load("blend_hold.npz")
o = np.asarray(D["open"], float); bs = np.asarray(D["bsp"], float); won = np.asarray(D["finish"], float) == 1
okp = np.isfinite(o) & (o > 1); fld = np.bincount(ri, minlength=nR)[ri]; race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0
track = D["track"][ri].astype(str); meet = np.char.add(track, np.char.add("|", D["date"][ri].astype(str))); jk = D["jockey"].astype(str)
cnt = collections.Counter(zip(meet, jk)); only = np.array([cnt[(m, x)] == 1 for m, x in zip(meet, jk)])
def norm(v):
    s = np.bincount(ri, weights=v, minlength=nR); return v / np.where(s[ri] > 0, s[ri], 1)
def blend(p):
    v = np.where(okp, np.exp(0.82 * np.log(np.maximum(p, 1e-9)) + 0.22 * np.log(1 / np.where(okp, o, 2))), 0); return np.where(race_ok[ri], norm(v), 0)
old, new = b.split(0.7); hold_r = np.zeros(nR, bool); hold_r[np.where(new)[0] if new.dtype == bool else list(new)] = True
samples = {"HOLD": (z["p2"], hold_r[ri]), "OLD": (norm(np.load("p_oof_blend9.npy")), ~hold_r[ri])}
DED = 0.16
def res(ix, st):
    pl = np.where(won[ix], st * (o[ix] - 1) * (1 - DED), -st); return st.sum(), pl.sum(), pl.sum() / st.sum()
print("| sample | method | bets | staked (u) | profit (u) | staked ROI |\n|---|---|---|---|---|---|")
for name, (pm, ins) in samples.items():
    base = ins & race_ok[ri] & np.isfinite(bs) & (pm > 0); pb = blend(pm); q = lambda x: 1 / np.maximum(x, 1e-9)
    sheet = base & (pb > 0) & (q(pb) >= 1.6) & (q(pb) <= 15) & (o >= 1.2 * q(pb)) & (o < 3 * q(pb)); six = np.where(sheet)[0]
    st = np.array([stake_rule.stake(pb[i], o[i], only[i], fld[i]) for i in six]); a, p_, r = res(six, st)
    print(f"| {name} | sheet | {len(six)} | {a:.0f} | {p_:+.0f} | {100*r:+.1f}% |")
    mo = 0.95 * (1.2 / np.maximum(pm, 1e-9) ** 0.82) ** (1 / 0.78)
    for steps_name, steps in (("3 steps x1/1.25/1.5", (1, 1.25, 1.5)), ("8 steps x1 to x2", (1, 1.1, 1.2, 1.3, 1.45, 1.6, 1.8, 2.0))):
        for size in ("bottom", "top"):
            for band in ("model", "blend"):
                ix, stk = [], []
                for i in np.where(base & (q(pm) >= 1.6) & (q(pm) <= 15) & (o >= mo) & (o < 3 * q(pm)))[0]:
                    ch = lambda t: pm[i] ** 0.82 * t ** -0.22
                    tiers = [mo[i] * s for s in steps if mo[i] * s < 3 * q(pm[i])]
                    if band == "blend": tiers = [t for t in tiers if 1.6 <= 1 / ch(t) <= 15]
                    tot, prev = 0.0, 0.0
                    for k, t in enumerate(tiers):
                        tp = tiers[k + 1] if (size == "top" and k + 1 < len(tiers)) else t
                        s_ = stake_rule.stake(ch(tp), tp, only[i], fld[i]); add = max(0.0, s_ - prev); prev = max(prev, s_)
                        if o[i] >= t: tot += add
                    if tot > 0: ix.append(i); stk.append(tot)
                ix = np.array(ix); stk = np.array(stk); a, p_, r = res(ix, stk)
                print(f"| {name} | orders, {steps_name}, sized at {size}, band on {band} | {len(ix)} | {a:.0f} | {p_:+.0f} | {100*r:+.1f}% |")
