"""BetMatic-style orders, tested (13 Oct 2026, founder: "why haven't we done a test on this method?").

The sheet judges value at the open with the EXACT blend: every runner's model chance blended with every runner's open
(0.82 ours, 0.22 open), renormalised per race, bet if open >= 1.2 / blended chance. An order sent to BetMatic before the
market exists cannot see the other runners' opens, so it carries a MINIMUM ODDS worked out from our chance alone,
    min odds = (1.2 / p_model^0.82)^(1/0.78)            (the blend with the per-race rescale left out)
optionally shaded down by a slack, and ONE fixed stake (the stake at the minimum odds). It fires when the open is at or
over the minimum. Same filters both ways: our price $1.60-$15, open under 3x our price.

Compared on two samples, HOLD (live stage-2 model, the holdout) and OLD (stage-1 out-of-fold, the races before it):
bets, strike, flat ROI at the open after the measured 16c scratching deduction, staked ROI and profit at $100 a unit,
and how many of the sheet's bets the orders miss and how many bets the orders add that the sheet would not take."""
import numpy as np, bench as b, collections, stake_rule
D = b.load(); ri = D["race_idx"]; nR = D["n_races"]; z = np.load("blend_hold.npz")
o = np.asarray(D["open"], float); bs = np.asarray(D["bsp"], float); won = np.asarray(D["finish"], float) == 1
okp = np.isfinite(o) & (o > 1); fld = np.bincount(ri, minlength=nR)[ri]
track = D["track"][ri].astype(str); meet = np.char.add(track, np.char.add("|", D["date"][ri].astype(str))); jk = D["jockey"].astype(str)
cnt = collections.Counter(zip(meet, jk)); only = np.array([cnt[(m, x)] == 1 for m, x in zip(meet, jk)])
DED = 0.16
race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0


def norm(v):
    s = np.bincount(ri, weights=v, minlength=nR); return v / np.where(s[ri] > 0, s[ri], 1)


def blend(p):
    v = np.where(okp, np.exp(0.82 * np.log(np.maximum(p, 1e-9)) + 0.22 * np.log(1 / np.where(okp, o, 2))), 0)
    return np.where(race_ok[ri], norm(v), 0)


old, new = b.split(0.7)
hold_r = np.zeros(nR, bool); hold_r[np.where(new)[0] if new.dtype == bool else list(new)] = True
samples = {"HOLD": (z["p2"], hold_r[ri]), "OLD": (norm(np.load("p_oof_blend9.npy")), ~hold_r[ri])}


def settle(ix, stakes):
    w = won[ix]; n = len(ix)
    flat = np.mean(np.where(w, (o[ix] - 1) * (1 - DED), -1)) if n else 0
    pl = np.where(w, stakes * (o[ix] - 1) * (1 - DED), -stakes)
    return n, (w.mean() if n else 0), flat, (pl.sum() / stakes.sum() if n else 0), pl.sum()


print("| sample | method | bets | strike | flat ROI (16c ded) | staked ROI | profit (u) | sheet bets missed | extra bets |")
print("|---|---|---|---|---|---|---|---|---|")
for name, (pm, insample) in samples.items():
    base = insample & race_ok[ri] & np.isfinite(bs) & (pm > 0)
    pb = blend(pm)
    sheet = base & (pb > 0) & (1 / np.maximum(pb, 1e-9) >= 1.6) & (1 / np.maximum(pb, 1e-9) <= 15) & (o >= 1.2 / np.maximum(pb, 1e-9)) & (o < 3 / np.maximum(pb, 1e-9))
    six = np.where(sheet)[0]
    st = np.array([stake_rule.stake(pb[i], o[i], only[i], fld[i]) for i in six])
    n, s, f, sr, pr = settle(six, st)
    print(f"| {name} | sheet (exact blend at the open) | {n} | {100*s:.0f}% | {100*f:+.1f}% | {100*sr:+.1f}% | {pr:+.0f} | - | - |")
    mo0 = (1.2 / np.maximum(pm, 1e-9) ** 0.82) ** (1 / 0.78)
    for slack in (0.0, 0.03, 0.05, 0.10):
        mo = mo0 * (1 - slack)
        order = base & (1 / pm >= 1.6) & (1 / pm <= 15) & (mo < 3 / pm)
        fire = order & (o >= mo) & (o < 3 / pm)
        fix = np.where(fire)[0]
        fixed = np.array([stake_rule.stake(1.2 / mo0[i], mo0[i], only[i], fld[i]) for i in fix])    # one stake, set at the unshaded minimum
        ladder = np.array([stake_rule.stake(pb[i], o[i], only[i], fld[i]) for i in fix])           # what the sheet would stake at that open
        miss = int((sheet & ~fire).sum()); extra = int((fire & ~sheet).sum())
        for lab, stk in (("fixed stake", fixed), ("stake ladder", ladder)):
            n, s, f, sr, pr = settle(fix, stk)
            print(f"| {name} | orders, min odds -{int(slack*100)}%, {lab} | {n} | {100*s:.0f}% | {100*f:+.1f}% | {100*sr:+.1f}% | {pr:+.0f} | {miss} | {extra} |")
