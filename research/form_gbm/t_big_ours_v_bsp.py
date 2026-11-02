"""The doubled bets (open 2.2x+ ours, ours < $8): how close does our rated price land to BSP? (2 Nov 2026)"""
import numpy as np
src = open("t_all_rules.py").read().split('summ(plan(pm0), "all rules')[0]
exec(src)
b = plan(pmS); idx = np.array([i for i, _ in b])
ours = 1 / pmS[idx]; e = pmS[idx] * o[idx]; big = (e >= 2.2) & (ours < 8)
def rep(lab, k):
    r = bs[idx[k]] / ours[k]; w = won[idx[k]]
    print(f"\n{lab}: {k.sum()} bets, {w.sum()} won")
    print(f"  median: ours ${np.median(ours[k]):.2f}, open ${np.median(o[idx[k]]):.2f}, BSP ${np.median(bs[idx[k]]):.2f}; BSP/ours median {np.median(r):.2f}, middle half {np.percentile(r,25):.2f}-{np.percentile(r,75):.2f}")
    print(f"  BSP within 10% of ours {np.mean(abs(r-1)<=0.10):.0%}, within 20% {np.mean(abs(r-1)<=0.20):.0%}, within 33% {np.mean((r>=0.75)&(r<=1.33)):.0%}")
    print(f"  BSP shorter than ours {np.mean(r<1):.0%}; longer {np.mean(r>1):.0%}; BSP still 1.5x+ ours {np.mean(r>=1.5):.0%}")
    print(f"  open/ours median {np.median(o[idx[k]]/ours[k]):.2f}: how much of the gap closed by BSP, median {np.median((o[idx[k]]-bs[idx[k]])/(o[idx[k]]-ours[k])):.0%}")
    print(f"  winners expected: by our price {pmS[idx[k]].sum():.1f}, by BSP {np.sum(1/bs[idx[k]]):.1f} (BSP before its ~2-3% overround), actual {w.sum()}")
    for lo, hi in ((0, 4), (4, 8)):
        kk = k & (ours >= lo) & (ours < hi)
        if kk.sum(): print(f"    ours ${lo}-${hi}: {kk.sum()} bets, BSP/ours median {np.median(bs[idx[kk]]/ours[kk]):.2f}, won {won[idx[kk]].sum()} v ours {pmS[idx[kk]].sum():.1f} v BSP {np.sum(1/bs[idx[kk]]):.1f}")
    return r
r = rep("DOUBLED (open 2.2x+ ours, ours < $8)", big)
rep("THE REST of the live book", ~big)
print("\ndoubled bets, BSP/ours buckets:")
for lo, hi in ((0, .8), (.8, .9), (.9, 1.1), (1.1, 1.25), (1.25, 1.5), (1.5, 2), (2, 99)):
    kk = (r >= lo) & (r < hi); print(f"  {lo:.2f}-{hi:.2f}: {kk.sum():3d} bets ({kk.mean():.0%}), won {won[idx[big][kk]].sum()}")
