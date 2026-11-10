"""The opening book, month by month (night of 10 Nov 2026). Form King's open for a race is one price per runner; a real
bookmaker's opening market adds up to 115-130%. A race whose opens add up to under 100% could not have been bet as
recorded. How common is that by month, in the races pulled live before the jump, and where does the backtest's profit sit?
Walk-forward trees (1 Jan - 9 Nov 2026) for the profit split; the book itself for every month from Jul 2025.
    python3.13 open_book_months.py   (night folder)"""
import numpy as np, sys
sys.argv = ["x"]
exec(open("strat3.py").read().split("P_wf = ")[0])
P_wf = np.where(date >= "2026-06-03", np.load("preds/base_A.npy"), np.load("preds/base_B.npy")).astype(float)
okop = np.isfinite(o) & (o > 1); book_r = np.bincount(ri, weights=np.where(okop, 1 / np.where(okop, o, 2), 0), minlength=nR); book = book_r[ri]
full = nl.race_ok; rd = nl.rdate; pj = D["pre_jump"].astype(bool)
bsb = np.bincount(ri, weights=np.where(np.isfinite(bs) & (bs > 1), 1 / np.where(bs > 1, bs, 2), 0), minlength=nR)
spv = D["sp"].astype(float); spb = np.bincount(ri, weights=np.where(np.isfinite(spv) & (spv > 1), 1 / np.where(spv > 1, spv, 2), 0), minlength=nR)
print("| month | races with every open | median opening book | under 100% | under 110% | over 140% | median SP book | median BSP book |\n|---|---|---|---|---|---|---|---|")
months = sorted({d[:7] for d in rd})
for mth in months:
    m = full & np.array([d[:7] == mth for d in rd])
    if m.sum() < 20: continue
    print(f"| {mth} | {int(m.sum())} | {np.median(book_r[m]):.3f} | {100*np.mean(book_r[m] < 1.0):.0f}% | {100*np.mean(book_r[m] < 1.1):.0f}% | {100*np.mean(book_r[m] > 1.4):.0f}% | {np.median(spb[m]):.3f} | {np.median(bsb[m]):.3f} |")
m = full & pj; print(f"\nraces pulled before the jump (the point-in-time rows): {int(m.sum())}; median opening book {np.median(book_r[m]):.3f}, under 100%: {100*np.mean(book_r[m] < 1.0):.0f}%, under 110%: {100*np.mean(book_r[m] < 1.1):.0f}%")
m = full & ~pj; print(f"back-filled races: {int(m.sum())}; median {np.median(book_r[m]):.3f}, under 100%: {100*np.mean(book_r[m] < 1.0):.0f}%, under 110%: {100*np.mean(book_r[m] < 1.1):.0f}%")
oos = date >= "2026-01-01"; I, S_, Pr = sheet(P_wf, oos, ceil=3.0); u = pl(I, S_, Pr); bk = book[I]
print("\nTHE LIVE SHEET'S BACKTEST BY THE OPENING BOOK OF THE RACE (walk-forward trees, 1 Jan - 9 Nov 2026):")
print("| opening book | races | bets | bets a race | won | staked | profit | ROI | beat BSP | median open/BSP |\n|---|---|---|---|---|---|---|---|---|---|")
rr = np.unique(ri[oos & full[ri]])
for lab, lo, hi in (("under 90%", 0, 0.9), ("90-100%", 0.9, 1.0), ("100-110%", 1.0, 1.1), ("110-120%", 1.1, 1.2), ("120-130%", 1.2, 1.3), ("130%+", 1.3, 99), ("ALL", 0, 99), ("110%+ (a real market)", 1.1, 99)):
    m = (bk >= lo) & (bk < hi); nr = int(((book_r[rr] >= lo) & (book_r[rr] < hi)).sum())
    print(f"| {lab} | {nr} | {int(m.sum())} | {m.sum()/max(nr,1):.2f} | {int(won[I[m]].sum())} | {S_[m].sum():.0f}u | {u[m].sum():+.0f}u | {100*u[m].sum()/max(S_[m].sum(),1e-9):+.0f}% | {100*np.mean(Pr[m] > bs[I[m]]):.0f}% | {np.median(Pr[m]/bs[I[m]]):.2f} |")
