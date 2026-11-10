"""The sheet as it is against the two changes put to the founder (night of 10 Nov 2026), with every live rule this
backtest can apply: first starters out, the first-up blocks, the bounce block, the second-up $15 cap, the metro $12 cap
(without the metro lean), edge 1.15 under $4 else 1.20, three steps, the 2.2x doubling, deduction fitted by race.
  A  the sheet today (3x ceiling, bounce block on)
  B  ceiling 6x
  C  ceiling 6x and no bounce block
    python3.13 strat6.py   (night folder)"""
import numpy as np, sys
sys.argv = ["x"]
src = open("strat5.py").read(); exec(src.split("I, S_, Pr = sheet(P_wf, oos, ceil=3.0)")[0].replace('print(f"flags over', 'pass #'))
P_cf = np.load("p_oof_chal.npy").astype(float)


def sheet_live(pm, oos, ceil=3.0, bounce_block=True):
    blk = fu_short | fu_trial | (bounce if bounce_block else False)
    I, S_, Pr = sheet(pm, oos & ~blk, ceil=ceil)
    keep = ~((early[I] & (Pr > 15)) | (metro[I] & (Pr >= 12)))
    return I[keep], S_[keep], Pr[keep]


def report(title, pm, PERS):
    pr_all = np.select([(date >= lo) & (date < hi) for _, lo, hi in PERS], list(range(len(PERS))), -1); oos = pr_all >= 0
    print(f"\n{title}\n| sheet | " + " | ".join(p[0] for p in PERS) + " | all: bets, staked, profit, ROI | worst drawdown | bets a month |\n|" + "---|" * (len(PERS) + 4))
    months = len({d[:7] for d in date[oos]}); base = None
    for lab, kw in (("A today: 3x ceiling, bounce block", dict()), ("B ceiling 6x", dict(ceil=6.0)), ("C ceiling 6x, no bounce block", dict(ceil=6.0, bounce_block=False)), ("(3x ceiling, no bounce block)", dict(bounce_block=False))):
        I, S_, Pr = sheet_live(pm, oos, **kw); u = np.where(won[I], S_ * (Pr - 1) * (1 - ded[I]), -S_)
        order = np.lexsort((I, date[I])); cum = np.cumsum(u[order]); dd = float(np.max(np.maximum.accumulate(np.maximum(cum, 0)) - cum))
        base = base or u.sum()
        print(f"| {lab} | " + " | ".join(f"{u[pr_all[I] == k].sum():+.0f}u" for k in range(len(PERS))) + f" | {len(I)}, {S_.sum():.0f}u, {u.sum():+.0f}u ({100*(u.sum()/base-1):+.0f}% v today), {100*u.sum()/S_.sum():+.0f}% | {dd:.0f}u | {len(I)/months:.0f} |")


report("WALK-FORWARD TREES, 1 Jan - 9 Nov 2026", P_wf, (("Jan-17Mar", "2026-01-01", "2026-03-18"), ("18Mar-2Jun", "2026-03-18", "2026-06-03"), ("3Jun-8Oct", "2026-06-03", "2026-10-09"), ("9Oct-9Nov", "2026-10-09", "2027-01-01")))
report("CROSS-FITTED THREE-MODEL BLEND, 1 Jul 2025 - 9 Nov 2026", P_cf, (("Jul-Sep25", "2025-07-01", "2025-10-01"), ("Oct-Dec25", "2025-10-01", "2026-01-01"), ("Jan-Mar26", "2026-01-01", "2026-04-01"), ("Apr-Jun26", "2026-04-01", "2026-07-01"), ("Jul-Sep26", "2026-07-01", "2026-10-01"), ("Oct-9Nov26", "2026-10-01", "2027-01-01")))
