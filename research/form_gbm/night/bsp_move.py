"""Does BSP under-react to its own move from the open? (night of 10 Nov 2026). No model: every runner with an open and
a BSP in races with a full BSP book, 16 months, three eras. Winners against BSP's expected winners by how far the
price moved (open / BSP: over 1 = firmed), and for the big firmers by BSP band. A/E over about 1.09 pays a back at BSP
after 8% commission; under about 0.92 pays a lay at mid prices.
    python3.13 bsp_move.py   (night folder)"""
import numpy as np
import nl
D, ri, nR, date, won, o, bs = nl.D, nl.ri, nl.nR, nl.date, nl.won, nl.o, nl.bs
okb = np.isfinite(bs) & (bs > 1); rok = (np.bincount(ri, weights=~okb, minlength=nR) == 0) & (np.bincount(ri, weights=won, minlength=nR) == 1)
fsr = D["X"][:, list(D["cols"]).index("firstStarter")] == 1
ok = rok[ri] & np.isfinite(o) & (o > 1); r = np.where(ok, o / bs, np.nan); q = 1 / np.where(okb, bs, 1e9)
ERA = (("Jul-Dec 2025", "2025-07-01", "2026-01-01"), ("Jan-May 2026", "2026-01-01", "2026-06-03"), ("Jun-9 Nov 2026", "2026-06-03", "2027-01-01"))
def cell(m):
    n, w, e = int(m.sum()), int(won[m].sum()), float(q[m].sum())
    return f"{n} {w} ({e:.0f}) A/E {w/max(e,1e-9):.2f}" if n >= 30 else f"{n} -"
print("ALL RUNNERS by the move, open / BSP: runners, winners (BSP expected), A/E\n| open / BSP | " + " | ".join(e[0] for e in ERA) + " | all | back at BSP, 8% comm | lay at BSP |\n|---|---|---|---|---|---|---|")
B = ((0, 0.5, "drifted 2x+"), (0.5, 0.67, "drifted 1.5-2x"), (0.67, 0.8, "drifted 1.25-1.5x"), (0.8, 0.95, "drifted a little"), (0.95, 1.05, "steady"), (1.05, 1.25, "firmed a little"),
     (1.25, 1.5, "firmed 1.25-1.5x"), (1.5, 2.0, "firmed 1.5-2x"), (2.0, 99, "firmed 2x+"))
for lo, hi, lab in B:
    m = ok & (r >= lo) & (r < hi); ub = np.where(won[m], (bs[m] - 1) * 0.92, -1.0); ul = np.where(won[m], -(bs[m] - 1), 0.92)
    print(f"| {lab} | " + " | ".join(cell(m & (date >= a) & (date < b_)) for _, a, b_ in ERA) + f" | {cell(m)} | {100*ub.mean():+.1f}% | {100*ul.mean():+.1f}% a lay |")
print("\nFIRMED 1.5x+ from the open, by BSP band\n| BSP | " + " | ".join(e[0] for e in ERA) + " | all | back at BSP, 8% comm |\n|---|---|---|---|---|---|")
for lo, hi in ((1, 3), (3, 5), (5, 7), (7, 10), (10, 15), (15, 99)):
    m = ok & (r >= 1.5) & (bs >= lo) & (bs < hi); ub = np.where(won[m], (bs[m] - 1) * 0.92, -1.0)
    print(f"| ${lo}-${hi} | " + " | ".join(cell(m & (date >= a) & (date < b_)) for _, a, b_ in ERA) + f" | {cell(m)} | {100*ub.mean():+.1f}% |")
print("\nDRIFTED 1.5x+ from the open, by BSP band\n| BSP | " + " | ".join(e[0] for e in ERA) + " | all | lay at BSP, 8% comm |\n|---|---|---|---|---|---|")
for lo, hi in ((1, 5), (5, 8), (8, 12), (12, 20), (20, 40), (40, 999)):
    m = ok & (r < 0.67) & (bs >= lo) & (bs < hi); ul = np.where(won[m], -(bs[m] - 1), 0.92)
    print(f"| ${lo}-${hi} | " + " | ".join(cell(m & (date >= a) & (date < b_)) for _, a, b_ in ERA) + f" | {cell(m)} | {100*ul.mean():+.1f}% a lay |")
