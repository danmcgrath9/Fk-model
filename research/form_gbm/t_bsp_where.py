"""Where, if anywhere, do we beat BSP? (3 Nov 2026, founder: "Is there anywhere / price band or situation that we are
better than BSP? Like when a horse stays similar price within 15% and we have it shorter?")
v10 holdout 3 Jun - 13 Oct. Part A: the live book (every live rule, bets struck at the open), each slice settled at the
open less 7% AND at BSP less 8%, with winners against what our price and BSP each expected (A/E under 1 = we beat it).
Part B: every runner in the holdout, a pure BSP rule (back 1u at BSP when BSP is at least k x our price), by k, by our
price and by what the market did from the open."""
import numpy as np
src = open("t_all_rules.py").read().split('summ(plan(pm0), "all rules')[0]
exec(src)
b = plan(pmS); idx = np.array([i for i, _ in b]); st = np.array([s for _, s in b])
ours = 1 / pmS[idx]; ratio = bs[idx] / o[idx]; bv = bs[idx] / ours
def line(lab, k, st_=None):
    k = np.asarray(k); n = k.sum()
    if n == 0: print(f"  {lab:44s}    0 bets"); return
    s = (st if st_ is None else st_)[k]; w = won[idx[k]]
    plo = np.where(w, s * (o[idx[k]] - 1) * 0.93, -s).sum(); plb = np.where(w, s * (bs[idx[k]] - 1) * 0.92, -s).sum()
    eo = pmS[idx[k]].sum(); eb = (1 / bs[idx[k]]).sum()
    print(f"  {lab:44s} {n:4d} bets {w.sum():3d} won | ours exp {eo:5.1f} A/E {w.sum()/eo:4.2f} | BSP exp {eb:5.1f} A/E {w.sum()/eb:4.2f} | open {100*plo/s.sum():+5.0f}%  BSP {100*plb/s.sum():+5.0f}% ({plb:+.0f}u)")
print("A. THE LIVE BOOK, sliced (A/E = winners / expected; under 1.00 against BSP means BSP had them too short, i.e. we beat BSP)")
line("all", np.ones(len(idx), bool))
print(" by what the market did from the open to BSP:")
for lab, k in (("firmed hard (BSP < 0.6x open)", ratio < 0.6), ("firmed (0.6-0.85x)", (ratio >= 0.6) & (ratio < 0.85)),
               ("held (0.85-1.15x)", (ratio >= 0.85) & (ratio < 1.15)), ("drifted (1.15x+)", ratio >= 1.15)):
    line(lab, k)
print(" by BSP against our price:")
for lab, k in (("BSP shorter than ours", bv < 1), ("BSP within 15% over ours", (bv >= 1) & (bv < 1.15)),
               ("BSP 1.15-1.5x ours", (bv >= 1.15) & (bv < 1.5)), ("BSP 1.5x+ ours", bv >= 1.5)):
    line(lab, k)
print(" the founder's slice, held within 15% of the open AND ours shorter than BSP:")
line("held 0.85-1.15x, BSP > ours", (ratio >= 0.85) & (ratio < 1.15) & (bv > 1))
line("held 0.85-1.15x, BSP 1.15x+ ours", (ratio >= 0.85) & (ratio < 1.15) & (bv >= 1.15))
line("drifted 1.15x+, BSP 1.15x+ ours", (ratio >= 1.15) & (bv >= 1.15))
print(" by our price:")
for lo, hi in ((1.6, 3), (3, 5), (5, 8), (8, 15.01)):
    line(f"ours ${lo:g}-${hi:g}", (ours >= lo) & (ours < hi))
print(" metro v country:")
line("metro", metro[idx]); line("country/provincial", ~metro[idx])
print("\nB. EVERY RUNNER, pure BSP rule: back 1u at BSP when BSP >= k x our price (first starters out), settled at BSP less 8%")
sel = m & ~fs & np.isfinite(pmS) & (pmS > 0)
I = np.where(sel)[0]; OU = 1 / pmS[I]; BV = bs[I] / OU; RT = bs[I] / o[I]
def lineB(lab, k):
    k = np.asarray(k); n = k.sum()
    if n < 20: print(f"  {lab:44s} {n:5d} bets (too few)"); return
    w = won[I[k]]; pl = np.where(w, (bs[I[k]] - 1) * 0.92, -1.0).sum(); eo = pmS[I[k]].sum(); eb = (1 / bs[I[k]]).sum()
    print(f"  {lab:44s} {n:5d} bets {w.sum():4d} won | ours exp {eo:6.1f} A/E {w.sum()/eo:4.2f} | BSP exp {eb:6.1f} A/E {w.sum()/eb:4.2f} | BSP {100*pl/n:+5.1f}% ({pl:+.0f}u)")
for kk in (1.0, 1.2, 1.5, 2.0):
    lineB(f"BSP >= {kk:g}x ours, ours $1.60-$15", (BV >= kk) & (OU >= 1.6) & (OU <= 15))
print(" BSP >= 1.2x ours, by our price:")
for lo, hi in ((1.6, 3), (3, 5), (5, 8), (8, 15.01)):
    lineB(f"ours ${lo:g}-${hi:g}", (BV >= 1.2) & (OU >= lo) & (OU < hi))
print(" BSP >= 1.2x ours, ours $1.60-$15, by the market's move from the open:")
for lab, k in (("firmed hard (BSP < 0.6x open)", RT < 0.6), ("firmed (0.6-0.85x)", (RT >= 0.6) & (RT < 0.85)),
               ("held (0.85-1.15x)", (RT >= 0.85) & (RT < 1.15)), ("drifted (1.15x+)", RT >= 1.15)):
    lineB(lab, (BV >= 1.2) & (OU >= 1.6) & (OU <= 15) & k)
print(" BSP >= 1.2x ours AND open >= 1.2x ours (value at both), ours $1.60-$15:")
lineB("value at the open and at BSP", (BV >= 1.2) & (o[I] / OU >= 1.2) & (OU >= 1.6) & (OU <= 15))
lineB("  of those, held 0.85-1.15x", (BV >= 1.2) & (o[I] / OU >= 1.2) & (OU >= 1.6) & (OU <= 15) & (RT >= 0.85) & (RT < 1.15))
lineB("  of those, metro", (BV >= 1.2) & (o[I] / OU >= 1.2) & (OU >= 1.6) & (OU <= 15) & metro[I])
lineB("  of those, country", (BV >= 1.2) & (o[I] / OU >= 1.2) & (OU >= 1.6) & (OU <= 15) & ~metro[I])
print(" our top pick in the race (shortest by our price), backed at BSP:")
top = np.zeros(len(pmS), bool)
for r in np.unique(ri[I]):
    j = I[ri[I] == r]; top[j[np.argmax(pmS[j])]] = True
lineB("top pick, any price", top[I]); lineB("top pick, BSP >= 1.2x ours", top[I] & (BV >= 1.2)); lineB("top pick, BSP >= ours", top[I] & (BV >= 1.0))
print("\nC. THE SLICES THAT HELD UP, BY HALF (Jun-Jul / Aug-Oct) and by our price")
H1 = dd[I] < "2026-08-01"
val_both = (BV >= 1.2) & (o[I] / OU >= 1.2) & (OU >= 1.6) & (OU <= 15) & ~metro[I]
for lab, k in (("country, value at the open AND at BSP", val_both), ("top pick, BSP >= ours", top[I] & (BV >= 1.0)), ("top pick, BSP >= 1.2x ours", top[I] & (BV >= 1.2))):
    print(f" {lab}:"); lineB("  Jun-Jul", k & H1); lineB("  Aug-Oct", k & ~H1)
    for lo, hi in ((1.6, 3), (3, 5), (5, 8), (8, 15.01)):
        lineB(f"  ours ${lo:g}-${hi:g}", k & (OU >= lo) & (OU < hi))
print(" live book, ours $8-$15 at BSP, by half:")
h1 = dd[idx] < "2026-08-01"; line("  Jun-Jul", (ours >= 8) & h1); line("  Aug-Oct", (ours >= 8) & ~h1)
