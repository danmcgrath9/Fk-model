"""t_stake_edge.py settled at BSP instead of the open (2 Nov 2026, founder: "how does this testing go at BSP now?").
Same bets and same stakes, chosen at the open by every live rule; the only change is the price each is settled at:
BSP less 8% commission (the house BSP convention, t_after_open.py) against the open less 7%."""
import numpy as np, collections
src = open("t_all_rules.py").read().split('summ(plan(pm0), "all rules')[0]
exec(src)
b = plan(pmS); idx = np.array([i for i, _ in b]); st0 = np.array([s for _, s in b]); od = np.argsort(dd[idx], kind="stable"); idx, st0 = idx[od], st0[od]
okb = np.isfinite(bs[idx]) & (bs[idx] > 1)
print(f"bets {len(idx)}, with a BSP {okb.sum()} (the rest left out of both columns)")
idx, st0 = idx[okb], st0[okb]
e = pmS[idx] * o[idx]; h1 = dd[idx] < "2026-08-01"; ours = 1 / pmS[idx]
big = (e >= 2.2) & (ours < 8)
def pl_at(st, px, keep):
    return np.where(won[idx], st * (px[idx] - 1) * keep, -st)
def show(lab, st):
    for nm_, px, keep in (("open-7%", o, 0.93), ("BSP-8%", bs, 0.92)):
        pl = pl_at(st, px, keep); c = np.cumsum(pl); D = np.max(np.maximum.accumulate(c) - c)
        print(f"{lab:30s} {nm_:7s} {st.sum():6.0f}u {pl.sum():+6.0f}u ({100*pl.sum()/st.sum():+5.1f}%)  DD {D:3.0f}u  P/DD {pl.sum()/max(D,1e-9):5.1f}  halves {100*pl[h1].sum()/st[h1].sum():+3.0f}%/{100*pl[~h1].sum()/st[~h1].sum():+3.0f}%")
st2 = np.minimum(10, np.where(big, st0 * 2, st0))
show("LIVE (no doubling)", st0)
show("x2 at 2.2x+, ours < $8", st2)
print("\nthe doubled bets alone (one stake, live)")
for lab, k in (("all", big), ("Jun-Jul", big & h1), ("Aug-Oct", big & ~h1), ("ours under $4", big & (ours < 4)), ("ours $4-$8", big & (ours >= 4))):
    for nm_, px, keep in (("open-7%", o, 0.93), ("BSP-8%", bs, 0.92)):
        pl = pl_at(st0, px, keep)[k]
        print(f"  {lab:14s} {nm_:7s} {k.sum():4d} bets {won[idx[k]].sum():3d} won {st0[k].sum():6.1f}u {pl.sum():+6.1f}u ({100*pl.sum()/max(st0[k].sum(),1e-9):+6.1f}%)")
print(f"  median BSP/open on the doubled bets {np.median(bs[idx[big]]/o[idx[big]]):.2f}; on the rest {np.median(bs[idx[~big]]/o[idx[~big]]):.2f}")
print(f"  share of doubled bets whose BSP is shorter than the open: {np.mean(bs[idx[big]] < o[idx[big]]):.0%}; the rest {np.mean(bs[idx[~big]] < o[idx[~big]]):.0%}")
print(f"  doubled bets: our price v BSP, median BSP/ours {np.median(bs[idx[big]]*pmS[idx[big]]):.2f} (1.00 = BSP agreed with us)")
print("\nthe rest (not doubled), one stake")
for nm_, px, keep in (("open-7%", o, 0.93), ("BSP-8%", bs, 0.92)):
    pl = pl_at(st0, px, keep)[~big]
    print(f"  {nm_:7s} {(~big).sum():4d} bets {pl.sum():+6.1f}u ({100*pl.sum()/st0[~big].sum():+5.1f}%)")
