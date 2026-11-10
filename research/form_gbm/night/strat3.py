"""The ceiling with the live sheet's own rules on top (night of 10 Nov 2026): edge 1.15 under $4, the 2 Nov doubling
(stake x2 when the open is 2.2x+ our price and we rate it under $8, 10u cap), first starters out. Ceilings 3x (live), 4x,
6x. Profit, worst drawdown (in units, bets in date order) and profit / drawdown, by period, on both prices:
walk-forward trees (11 months, four periods) and the cross-fitted three-model blend (16 months, six periods).
    python3.13 strat3.py   (night folder)"""
import numpy as np, sys
sys.argv = ["x"]
exec(open("strat1.py").read().split("HDR = ")[0])
fsr = D["X"][:, list(D["cols"]).index("firstStarter")] == 1


def sheet(pm, oos, ceil=3.0, double_to=None, big=2.2):
    """the live sheet: edge 1.15 under $4 else 1.2, three steps, doubling from `big` x our price up to double_to x (None = to the ceiling)"""
    base = oos & nl.race_ok[ri] & np.isfinite(bs) & (pm > 0) & ~fsr; qq = 1 / np.maximum(pm, 1e-9)
    e = np.where(qq < 4, 1.15, 1.2); mo = 0.95 * (e / np.maximum(pm, 1e-9) ** 0.82) ** (1 / 0.78); out = []
    for i in np.where(base & (qq >= 1.6) & (qq <= 15) & (o >= mo) & (o < ceil * qq))[0]:
        ch = lambda t: pm[i] ** 0.82 * t ** -0.22
        ts = [mo[i] * s for s in (1.0, 1.25, 1.5) if mo[i] * s < ceil * qq[i]]; tot = prev = 0.0
        for k, t in enumerate(ts):
            tp = ts[k + 1] if k + 1 < len(ts) else t
            s_ = stake_rule.stake(ch(tp), tp); add = max(0.0, s_ - prev); prev = max(prev, s_)
            if o[i] >= t: tot += add
        if tot > 0 and qq[i] < 8 and o[i] >= big * qq[i] and (double_to is None or o[i] < double_to * qq[i]): tot = min(10.0, 2 * tot)
        if tot > 0: out.append((i, tot, o[i]))
    a = np.array(out); return a[:, 0].astype(int), a[:, 1], a[:, 2]


def report(title, pm, PERS):
    pr_ = np.select([(date >= lo) & (date < hi) for _, lo, hi in PERS], list(range(len(PERS))), -1); oos = pr_ >= 0
    print(f"\n{title}\n| ceiling | " + " | ".join(p[0] for p in PERS) + " | all: bets, staked, profit, ROI | worst drawdown | profit / drawdown |\n|" + "---|" * (len(PERS) + 4))
    for lab, kw in (("3x (live)", dict(ceil=3.0)), ("4x", dict(ceil=4.0)), ("6x", dict(ceil=6.0)), ("6x, doubling stops at 3x", dict(ceil=6.0, double_to=3.0)), ("no ceiling", dict(ceil=99))):
        I, S_, Pr = sheet(pm, oos, **kw); u = pl(I, S_, Pr); order = np.lexsort((I, date[I])); cum = np.cumsum(u[order]); dd = float(np.max(np.maximum.accumulate(np.maximum(cum, 0)) - cum))
        cells = [f"{u[pr_[I] == k].sum():+.0f}u" for k in range(len(PERS))]
        print(f"| {lab} | " + " | ".join(cells) + f" | {len(I)} bets, {S_.sum():.0f}u, {u.sum():+.0f}u, {100*u.sum()/S_.sum():+.0f}% | {dd:.0f}u | {u.sum()/dd:.1f} |")


P_wf = np.where(date >= "2026-06-03", np.load("preds/base_A.npy"), np.load("preds/base_B.npy")).astype(float)
report("WALK-FORWARD TREES, 1 Jan - 9 Nov 2026", P_wf, (("Jan-17Mar", "2026-01-01", "2026-03-18"), ("18Mar-2Jun", "2026-03-18", "2026-06-03"), ("3Jun-8Oct", "2026-06-03", "2026-10-09"), ("9Oct-9Nov", "2026-10-09", "2027-01-01")))
report("CROSS-FITTED THREE-MODEL BLEND, 1 Jul 2025 - 9 Nov 2026", np.load("p_oof_chal.npy").astype(float),
       (("Jul-Sep25", "2025-07-01", "2025-10-01"), ("Oct-Dec25", "2025-10-01", "2026-01-01"), ("Jan-Mar26", "2026-01-01", "2026-04-01"), ("Apr-Jun26", "2026-04-01", "2026-07-01"), ("Jul-Sep26", "2026-07-01", "2026-10-01"), ("Oct-9Nov26", "2026-10-01", "2027-01-01")))
