"""What a month looks like (night of 10 Nov 2026): the live sheet's bets on the walk-forward prices, 1 Jan - 9 Nov 2026
(strat3.sheet: first starters out, 1.15 under $4, the doubling, 16c deduction), re-drawn by whole race days.
10,000 thirty-day months: the spread of the month's profit, the chance of a losing month, the worst run inside it.
Shown at the backtest's full volume and at 70% of it (the live book has fired about 60-80% of the backtest's bets),
for the 3x ceiling and for 6x. $50 a unit.
    python3.13 risk_months.py   (night folder)"""
import numpy as np, sys
sys.argv = ["x"]
exec(open("strat3.py").read().split("P_wf = ")[0])
P_wf = np.where(date >= "2026-06-03", np.load("preds/base_A.npy"), np.load("preds/base_B.npy")).astype(float)
oos = date >= "2026-01-01"; rng = np.random.default_rng(3); days_all = np.array(sorted(set(date[oos])))
print(f"{len(days_all)} race days, 1 Jan - 9 Nov 2026 ({len(days_all)/313*30:.1f} race days a 30-day month)\n")
print("| ceiling | volume | bets a month | median month | 1 month in 20 is worse than | 1 in 20 better than | losing months | median worst run in a month | $ median at $50 |\n|---|---|---|---|---|---|---|---|---|")
for lab, kw in (("3x (live)", dict(ceil=3.0)), ("6x", dict(ceil=6.0))):
    I, S_, Pr = sheet(P_wf, oos, **kw); u = pl(I, S_, Pr)
    by = {d: u[date[I] == d] for d in days_all}; nd = int(round(len(days_all) / 313 * 30))
    for vol in (1.0, 0.7):
        tot, dd, nb = [], [], []
        for _ in range(10000):
            seq = np.concatenate([by[d] for d in rng.choice(days_all, nd)])
            if vol < 1: seq = seq[rng.random(len(seq)) < vol]
            c = np.cumsum(seq) if len(seq) else np.zeros(1); tot.append(c[-1]); dd.append(np.max(np.maximum.accumulate(np.maximum(c, 0)) - c)); nb.append(len(seq))
        tot, dd = np.array(tot), np.array(dd)
        print(f"| {lab} | {int(vol*100)}% | {np.mean(nb):.0f} | {np.median(tot):+.0f}u | {np.percentile(tot, 5):+.0f}u | {np.percentile(tot, 95):+.0f}u | {100*np.mean(tot < 0):.1f}% | {np.median(dd):.0f}u | ${50*np.median(tot):,.0f} |")
