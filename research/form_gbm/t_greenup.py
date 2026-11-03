"""Back at the open, lay the same horse at Betfair SP to lock the gap (3 Nov 2026, founder: "ways at BSP to make money
other than lays"). Every live-rule bet on the v10 holdout from 3 Jun, the live stake at the open less 7%; the lay leg
is a lay of (stake x open / BSP) at BSP, 8% commission on a winning lay, so the position returns about stake x
(open/BSP - 1) whether the horse wins or loses. Variants: lay every bet; lay only when BSP is under the open; only when
BSP is under 0.8x the open; keep the rest as plain bets."""
import numpy as np, collections, datetime as dt
src = open("t_all_rules.py").read().split('summ(plan(pm0), "all rules')[0]
exec(src)
b = plan(pmS); idx = np.array([i for i, _ in b]); st = np.array([s for _, s in b]); od = np.argsort(dd[idx], kind="stable"); idx, st = idx[od], st[od]
e = pmS[idx] * o[idx]; ours = 1 / pmS[idx]; big = (e >= 2.2) & (ours < 8); st = np.minimum(10, np.where(big, st * 2, st))   # the live staking
O, B, W = o[idx], bs[idx], won[idx]
hold = np.where(W, st * (O - 1) * 0.93, -st)
def green(mask):
    L = np.where(mask, st * O / B, 0.0)
    win = st * (O - 1) * 0.93 - L * (B - 1)
    lose = -st + L * 0.92
    return np.where(W, win, lose)
def rep(name, pl):
    wk = collections.defaultdict(float)
    for j, i in enumerate(idx): wk[dt.date.fromisoformat(dd[i]).isocalendar()[:2]] += pl[j]
    Wk = np.array(list(wk.values())); c = np.cumsum(pl); ddn = np.max(np.maximum.accumulate(c) - c)
    print(f"{name:<46} {pl.sum():+8.0f}u  {100*pl.sum()/st.sum():+6.1f}%  worst drawdown {ddn:5.0f}u  weeks up {np.sum(Wk>0)}/{len(Wk)}  worst week {Wk.min():+6.1f}u  best week {Wk.max():+6.1f}u  sd/week {Wk.std():5.1f}u")
print(f"{len(idx)} bets, {st.sum():.0f}u staked; BSP under the open on {np.mean(B < O):.0%}, under 0.8x on {np.mean(B < 0.8*O):.0%}; median open/BSP {np.median(O/B):.2f}")
rep("hold every bet (the book)", hold)
rep("green up every bet at BSP", green(np.ones_like(W, bool)))
rep("green up only where BSP < open, hold the rest", green(B < O))
rep("green up only where BSP < 0.8x open, hold the rest", green(B < 0.8 * O))
rep("green up only where BSP < 0.6x open, hold the rest", green(B < 0.6 * O))
m = B < O; L = st * O / B
print(f"\nlay leg where BSP < open: {m.sum()} lays, mean lay stake {L[m].mean():.1f}u, mean liability {(L*(B-1))[m].mean():.1f}u (about stake x open), biggest {(L*(B-1))[m].max():.0f}u")
print(f"locked profit per bet where BSP < open: mean {(st*(O/B-1))[m].mean():.2f}u on a mean stake of {st[m].mean():.2f}u")
