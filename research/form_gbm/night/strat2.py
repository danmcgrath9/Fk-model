"""Cross-check of the edge and the ceiling on the three-model blend, 16 months (night of 10 Nov 2026).
Price: the 10 Nov challenger's out-of-fold stage-1 blend (trees + network + CatBoost, five date blocks, every race priced
by models that never saw it; cross-fitted, so later races helped price earlier ones: a second opinion beside strat1.py's
walk-forward trees, not a replacement). First starters never bet (the live rule). Six periods; a change has to hold in all.
    python3.13 strat2.py   (night folder; p_oof_chal.npy)"""
import numpy as np, sys
sys.argv = ["x"]
src = open("strat1.py").read().split("HDR = ")[0]
exec(src)
P = np.load("p_oof_chal.npy").astype(float); fsr = D["X"][:, list(D["cols"]).index("firstStarter")] == 1
PER = (("Jul-Sep25", "2025-07-01", "2025-10-01"), ("Oct-Dec25", "2025-10-01", "2026-01-01"), ("Jan-Mar26", "2026-01-01", "2026-04-01"),
       ("Apr-Jun26", "2026-04-01", "2026-07-01"), ("Jul-Sep26", "2026-07-01", "2026-10-01"), ("Oct-9Nov26", "2026-10-01", "2027-01-01"))
per = np.select([(date >= lo) & (date < hi) for _, lo, hi in PER], list(range(6)), -1); OOS = (per >= 0) & ~fsr
NP = len(PER)
def line(lab, idx, st, pr):
    u = pl(idx, st, pr); cells = []
    for k in range(NP):
        m = per[idx] == k; cells.append(f"{int(m.sum()):4d} {u[m].sum():+6.0f}u {100*u[m].sum()/max(st[m].sum(),1e-9):+4.0f}%")
    print(f"| {lab} | " + " | ".join(cells) + f" | {len(idx)} {u.sum():+.0f}u {100*u.sum()/st.sum():+.0f}% |")
HDR = "| rule | " + " | ".join(p[0] for p in PER) + " | all |\n|" + "---|" * (NP + 2)
kw = dict(pm=P)
print(f"races {len(np.unique(ri[per >= 0]))}; first starters out\n\nTHE CEILING (edge 1.20)\n" + HDR)
for c in (2.2, 3.0, 4.0, 5.0, 6.0, 8.0, 99): line(f"under {c}x" + (" (live)" if c == 3 else ""), *bets(ceil=c, **kw))
print("\nTHE EDGE (ceiling 3x)\n" + HDR)
for e in (1.10, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40): line(f"edge {e:.2f}" + (" (live)" if e == 1.2 else ""), *bets(edge=e, **kw))
print("\nBOTH (edge x ceiling)\n" + HDR)
for e, c in ((1.2, 3), (1.2, 6), (1.25, 6), (1.3, 6), (1.3, 3)): line(f"edge {e}, under {c}x", *bets(edge=e, ceil=c, **kw))
I, S_, Pr = bets(ceil=99, **kw); ov = Pr * P[I]; u = pl(I, S_, Pr)
print("\nBY OVERLAY (open / our price), no ceiling: bets, winners (BSP expected), profit, ROI, flat ROI, median BSP/open")
for lo, hi in ((1.0, 1.4), (1.4, 1.7), (1.7, 2.2), (2.2, 3.0), (3.0, 4.0), (4.0, 6.0), (6.0, 99)):
    m = (ov >= lo) & (ov < hi); fl = np.where(won[I[m]], (Pr[m] - 1) * 0.84, -1)
    pos = sum(1 for k in range(NP) if u[m & (per[I] == k)].sum() > 0)
    print(f"  {lo:.1f}-{hi:g}x: {int(m.sum()):5d} bets, {int(won[I[m]].sum()):4d} won ({nl.q[I[m]].sum():6.1f}), {u[m].sum():+8.1f}u on {S_[m].sum():7.0f}u ({100*u[m].sum()/S_[m].sum():+4.0f}%), "
          f"flat {100*fl.mean():+4.0f}%, BSP/open {np.median(bs[I[m]]/Pr[m]):.2f}, profitable in {pos} of {NP} periods")
