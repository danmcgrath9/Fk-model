"""e_bsp.py: the price-only Betfair SP rules on every state (18 Nov 2026; founder, 18 Nov: "Markets can move").
Data: scripts/betwatch_national.py. A rule here reads only TAB's first price (the open Betwatch holds) and Betfair SP,
so it needs no model and every state's races count. 1u at BSP, 8% commission; a lay is 1u of the backer's stake.
Expected winners = the sum of 1/BSP. The tracker's rules use Form King's average open and leave first starters out;
this open is TAB's first price and first starters are in (no form data outside Victoria)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from nat_load import HERE
D = np.load(os.path.join(HERE, "nat.npz"), allow_pickle=True)
date, state = D["date"].astype(str), D["state"].astype(str)
bsp, op, pos, scr = D["bsp"], D["tab_first"], D["pos"], D["scr"]
ok = ~np.isfinite(scr) & np.isfinite(bsp) & (bsp > 1.01) & np.isfinite(op) & (op > 1.011) & np.isfinite(pos)
won = pos == 1
ERAS = (("2025-07-01", "2026-01-01", "Jul-Dec 2025"), ("2026-01-01", "2026-06-03", "Jan-May 2026"), ("2026-06-03", "2027-01-01", "Jun-Nov 2026"))
back = np.where(won, (bsp - 1) * 0.92, -1.0); lay = np.where(won, -(bsp - 1), 0.92)
print(f"{int(ok.sum())} runners with a result, a Betfair SP and a TAB first price; {min(date[ok])} to {max(date[ok])}; "
      f"winners {int(won[ok].sum())} against {np.sum(1 / bsp[ok]):.0f} expected at BSP (book check)")


def cell(m):
    if m.sum() < 30: return f"{int(m.sum())}"
    return f"{int(m.sum())}, {int(won[m].sum())} ({np.sum(1 / bsp[m]):.0f}) A/E {won[m].sum() / np.sum(1 / bsp[m]):.2f}"
RULES = [("Lay $25-$40, drifted 2x from open", "lay", lambda: (bsp >= 25) & (bsp < 40) & (bsp >= 2 * op)),
         ("Lay $8-$12, firmed 1.5x from open", "lay", lambda: (bsp >= 8) & (bsp < 12) & (bsp * 1.5 <= op)),
         ("Lay $12-$15, drifted 1.25x from open", "lay", lambda: (bsp >= 12) & (bsp < 15) & (bsp >= 1.25 * op)),
         ("Back $3-$5, firmed 1.5x from open", "back", lambda: (bsp >= 3) & (bsp < 5) & (bsp * 1.5 <= op)),
         ("Back $4-$7, firmed 1.5x from open", "back", lambda: (bsp >= 4) & (bsp < 7) & (bsp * 1.5 <= op)),
         ("Lay drifted 1.5x+, BSP $8-$40 (the shift since June)", "lay", lambda: (bsp >= 8) & (bsp < 40) & (bsp >= 1.5 * op))]
for grp, gm in (("EVERY STATE", ok), ("VICTORIA", ok & (state == "VIC")), ("EVERY STATE BUT VICTORIA", ok & (state != "VIC"))):
    print(f"\n### {grp}: bets, winners (BSP expected), A/E, then units and return a bet\n\n| rule | " + " | ".join(e[2] for e in ERAS) + " | all | periods up |\n|---|---|---|---|---|---|")
    for label, side, f in RULES:
        m0 = gm & f(); pl = lay if side == "lay" else back; out = []; ups = 0
        for a, b_, _ in ERAS:
            m = m0 & (date >= a) & (date < b_); ups += pl[m].sum() > 0
            out.append(f"{cell(m)}; {pl[m].sum():+.0f}u {pl[m].mean() if m.any() else 0:+.1%}")
        print(f"| {label} | " + " | ".join(out) + f" | {cell(m0)}; {pl[m0].sum():+.0f}u {pl[m0].mean() if m0.any() else 0:+.1%} | {ups} of 3 |")
print("\n### Winners against BSP's expected winners by the move from TAB's first price to BSP, every state\n\n| open / BSP | " + " | ".join(e[2] for e in ERAS) + " | all | back at BSP | lay at BSP |\n|---|---|---|---|---|---|---|")
r = op / bsp
for lo, hi, lab in ((0, 0.5, "drifted 2x+"), (0.5, 0.667, "drifted 1.5-2x"), (0.667, 0.8, "drifted 1.25-1.5x"), (0.8, 0.95, "drifted a little"), (0.95, 1.05, "steady"),
                    (1.05, 1.25, "firmed a little"), (1.25, 1.5, "firmed 1.25-1.5x"), (1.5, 2, "firmed 1.5-2x"), (2, 99, "firmed 2x+")):
    m0 = ok & (r >= lo) & (r < hi)
    print(f"| {lab} | " + " | ".join(cell(m0 & (date >= a) & (date < b_)) for a, b_, _ in ERAS) + f" | {cell(m0)} | {back[m0].mean():+.1%} | {lay[m0].mean():+.1%} a lay |")
print("\n### Firmed 1.5x+ from the open, by BSP band, every state\n\n| BSP | " + " | ".join(e[2] for e in ERAS) + " | all | back at BSP |\n|---|---|---|---|---|---|")
for lo, hi in ((1, 3), (3, 5), (5, 7), (7, 10), (10, 15), (15, 99)):
    m0 = ok & (r >= 1.5) & (bsp >= lo) & (bsp < hi)
    print(f"| ${lo}-${hi} | " + " | ".join(cell(m0 & (date >= a) & (date < b_)) for a, b_, _ in ERAS) + f" | {cell(m0)} | {back[m0].mean():+.1%} |")
