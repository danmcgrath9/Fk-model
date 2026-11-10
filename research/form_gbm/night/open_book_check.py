"""Are the 3x-6x opens real? (night of 10 Nov 2026). A race whose opening prices add up to far under 100% is not a
market anyone could bet into: it is a placeholder (every runner posted at one long price) or a broken record. The
ceiling bets, by the opening book of their race, and what is left of the 3x -> 6x gain when races with an opening book
under 100% (and under 105%, 110%) are thrown out. Walk-forward trees, live sheet rules, 1 Jan - 9 Nov 2026.
    python3.13 open_book_check.py   (night folder)"""
import numpy as np, sys
sys.argv = ["x"]
exec(open("strat3.py").read().split("P_wf = ")[0])
P_wf = np.where(date >= "2026-06-03", np.load("preds/base_A.npy"), np.load("preds/base_B.npy")).astype(float)
oos = date >= "2026-01-01"
book = np.bincount(ri, weights=np.where(np.isfinite(o) & (o > 1), 1 / np.where(o > 1, o, 2), 0), minlength=nR)[ri]
n_same = np.zeros(len(ri))      # how many runners in the race share this runner's opening price
for r in range(nR):
    s, e = D["starts"][r], D["ends"][r]; x = o[s:e]; n_same[s:e] = [(np.abs(x - v) < 1e-9).sum() for v in x]
allb = book[oos & nl.race_ok[ri]]; rb = np.array([book[D["starts"][r]] for r in np.unique(ri[oos & nl.race_ok[ri]])])
print(f"opening book (sum of 1/open) over the OOS races: median {np.median(rb):.3f}, 5th pct {np.percentile(rb, 5):.3f}, 1st pct {np.percentile(rb, 1):.3f}; under 100%: {100*np.mean(rb < 1.0):.1f}% of races, under 105%: {100*np.mean(rb < 1.05):.1f}%")
I3, S3, P3 = sheet(P_wf, oos, ceil=3.0); I6, S6, P6 = sheet(P_wf, oos, ceil=6.0)
ov6 = P6 * P_wf[I6]; big = ov6 >= 3; u6 = pl(I6, S6, P6); u3 = pl(I3, S3, P3)
print(f"\nthe {int(big.sum())} bets the 6x ceiling adds: opening book of their race median {np.median(book[I6[big]]):.3f} (5th pct {np.percentile(book[I6[big]], 5):.3f}); "
      f"share in a race with a book under 100%: {100*np.mean(book[I6[big]] < 1.0):.0f}%, under 105%: {100*np.mean(book[I6[big]] < 1.05):.0f}%, under 110%: {100*np.mean(book[I6[big]] < 1.10):.0f}%")
print(f"  runners in the race sharing the same opening price as the bet: median {np.median(n_same[I6[big]]):.0f}; 4 or more share it: {100*np.mean(n_same[I6[big]] >= 4):.0f}% (all bets: {100*np.mean(n_same[I6] >= 4):.0f}%)")
print("\n| races kept | 3x ceiling | 6x ceiling | gain | extra bets | their winners |\n|---|---|---|---|---|---|")
for lab, keep in (("all", lambda b_: b_ > 0), ("opening book 100%+", lambda b_: b_ >= 1.0), ("105%+", lambda b_: b_ >= 1.05), ("110%+", lambda b_: b_ >= 1.10), ("110-135% (an ordinary book)", lambda b_: (b_ >= 1.10) & (b_ <= 1.35))):
    k3, k6 = keep(book[I3]), keep(book[I6]); kb = k6 & big
    print(f"| {lab} | {u3[k3].sum():+.0f}u on {int(k3.sum())} bets | {u6[k6].sum():+.0f}u on {int(k6.sum())} | {u6[k6].sum()-u3[k3].sum():+.0f}u | {int(kb.sum())} | {int(won[I6[kb]].sum())} |")
print("\nand with the extra bets required to be the ONLY runner at that opening price in the race (no flat placeholder line):")
kb = big & (n_same[I6] <= 2) & (book[I6] >= 1.05)
print(f"  {int(kb.sum())} bets, {int(won[I6[kb]].sum())} won, {u6[kb].sum():+.0f}u on {S6[kb].sum():.0f}u; by period: " + ", ".join(f"{u6[kb & (per[I6] == k)].sum():+.0f}u" for k in range(4)))
