"""Follow-up to t_stake_shape.py: the live stake does not grow with the overlay at the open (average 2u in every edge band),
while bets opening at 2.2x+ our price made +99%. An extra top tier (orders from k x our price up to the 3x ceiling)
is the same as multiplying those bets' stake by M. Tested here, live rules otherwise, and by halves and price band."""
import numpy as np, collections, stake_rule
src = open("t_all_rules.py").read().split('summ(plan(pm0), "all rules')[0]
exec(src)
b = plan(pmS); idx = np.array([i for i, _ in b]); st0 = np.array([s for _, s in b]); od = np.argsort(dd[idx], kind="stable"); idx, st0 = idx[od], st0[od]
e = pmS[idx] * o[idx]; h1 = dd[idx] < "2026-08-01"; ours = 1 / pmS[idx]
def show(lab, st):
    pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st); c = np.cumsum(pl); D = np.max(np.maximum.accumulate(c) - c)
    print(f"{lab:36s} {st.sum():6.0f}u {pl.sum():+6.0f}u ({100*pl.sum()/st.sum():+5.1f}%)  DD {D:3.0f}u  P/DD {pl.sum()/D:4.1f}  halves {100*pl[h1].sum()/st[h1].sum():+3.0f}%/{100*pl[~h1].sum()/st[~h1].sum():+3.0f}%  max {st.max():.1f}u")
show("LIVE", st0)
for k in (1.8, 2.0, 2.2, 2.5):
    for M in (1.5, 2.0):
        show(f"x{M} when open >= {k}x our price", np.minimum(10, np.where(e >= k, st0 * M, st0)))
print("\nbets opening at 2.2x+ our price, by half and by our price")
pl0 = np.where(won[idx], st0 * (o[idx] - 1) * 0.93, -st0)
for lab, k in (("Jun-Jul", (e >= 2.2) & h1), ("Aug-Oct", (e >= 2.2) & ~h1),
               ("ours under $4", (e >= 2.2) & (ours < 4)), ("ours $4-$8", (e >= 2.2) & (ours >= 4) & (ours < 8)), ("ours $8+", (e >= 2.2) & (ours >= 8)),
               ("metro", (e >= 2.2) & metro[idx]), ("country", (e >= 2.2) & ~metro[idx])):
    print(f"  {lab:14s} {k.sum():4d} bets {won[idx[k]].sum():3d} won {st0[k].sum():6.1f}u {pl0[k].sum():+6.1f}u ({100*pl0[k].sum()/max(st0[k].sum(),1e-9):+5.1f}%)  BSP/open {np.median(bs[idx[k]]/o[idx[k]]):.2f}")
print("\nsame for 1.3-2.2x (the rest)")
for lab, k in (("Jun-Jul", (e < 2.2) & h1), ("Aug-Oct", (e < 2.2) & ~h1)):
    print(f"  {lab:14s} {k.sum():4d} bets {won[idx[k]].sum():3d} won {st0[k].sum():6.1f}u {pl0[k].sum():+6.1f}u ({100*pl0[k].sum()/max(st0[k].sum(),1e-9):+5.1f}%)  BSP/open {np.median(bs[idx[k]]/o[idx[k]]):.2f}")
print("\nrefined: x2 only where we rate it under $8")
show("x2 when open >= 2.2x ours, ours < $8", np.minimum(10, np.where((e >= 2.2) & (ours < 8), st0 * 2, st0)))
show("x2 when open >= 2.0x ours, ours < $8", np.minimum(10, np.where((e >= 2.0) & (ours < 8), st0 * 2, st0)))
k = (e >= 2.2) & (ours < 8); print(f"  bets affected: {k.sum()} of {len(k)} ({k.sum()/ (dd[idx][-1] > '') / 19:.1f} a week over ~19 weeks)")
