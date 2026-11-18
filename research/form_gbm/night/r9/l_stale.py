"""l_stale.py: the big 9am overlays (a major 20%+ over the fair price): who is it, had the price ever moved, and how
many majors show it at once? (18 Nov 2026). Victoria, a_model's 'ours + median + move' fair price joined to the
national pull (each major's first price and minute, number of price changes, and its price 4 h and 1 h before the jump)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
D = np.load(os.path.join(HERE, "nat.npz"), allow_pickle=True); v = D["state"].astype(str) == "VIC"
FM = np.load(os.path.join(HERE, "fair_models.npy")); names = open(os.path.join(HERE, "fair_models.txt")).read().split("\n")
key = {(date[i], int(rno[i]), norm(name[i])): i for i in range(n)}
vd, vr, vn = D["date"].astype(str)[v], D["race"][v], D["name"].astype(str)[v]
j = np.array([key.get((vd[i], int(vr[i]), norm(vn[i])), -1) for i in range(len(vd))]); m = j >= 0; jj = np.maximum(j, 0)
NB = np.column_stack([D[f"{b}_0900"][v] for b in MAJORS]); NF = np.column_stack([D[f"{b}_first"][v] for b in MAJORS]); NFT = np.column_stack([D[f"{b}_ft"][v] for b in MAJORS])
T240 = np.column_stack([D[f"{b}_t240"][v] for b in MAJORS]); T60 = np.column_stack([D[f"{b}_t60"][v] for b in MAJORS]); nine_v = D["nine"][v]
for mdl in ("ours + median + move", "LIVE 0.20 ours + 1.00 TAB"):
    pa = FM[:, names.index(mdl)]; fa = np.where(pa > 0, 1 / np.maximum(pa, 1e-12), np.nan)
    fav = np.where(m, fa[jj], np.nan); e = m & (pa[jj] > 0) & ran[jj] & ~fs[jj] & (fav >= 1.6) & (fav <= 15) & (vd >= "2025-11-01")
    wv, limv, dedv = won[jj], lim[jj], DED[jj]
    print(f"\n## {mdl}")
    for a, b in ((1.05, 1.20), (1.20, 9)):
        hit = e[:, None] & np.isfinite(NB) & (NB / fav[:, None] >= a) & (NB / fav[:, None] < b)
        st = np.where(hit, limv[:, None] / np.maximum(NB - 1, 1e-9), 0.0); pl = np.where(hit, np.where(wv[:, None], (limv * (1 - dedv))[:, None], -st), 0.0)
        print(f"\n### price {a:.2f}-{b:.2f}x fair: {int(hit.sum())} bets on {int(hit.any(1).sum())} runners, ${pl.sum():+,.0f} on ${st.sum():,.0f} ({pl.sum() / st.sum():+.1%})")
        print("by major: " + "; ".join(f"{bk} {int(hit[:, k].sum())} bets ${pl[:, k].sum():+,.0f} ({pl[:, k].sum() / max(st[:, k].sum(), 1):+.0%})" for k, bk in enumerate(MAJORS)))
        nm = hit.sum(1)
        print("by how many majors show it: " + "; ".join(f"{lab}: {int((nm[:, None] * hit)[(nm >= lo_) & (nm <= hi_)].astype(bool).sum())} bets ${pl[(nm >= lo_) & (nm <= hi_)].sum():+,.0f} ({pl[(nm >= lo_) & (nm <= hi_)].sum() / max(st[(nm >= lo_) & (nm <= hi_)].sum(), 1):+.0%})" for lab, lo_, hi_ in (("one", 1, 1), ("two or three", 2, 3), ("four or more", 4, 7))))
        never = hit & (np.abs(NB - NF) < 0.011)                       # the 9am price is the major's first price: it has never moved
        print(f"the 9am price is that major's FIRST price (never moved): {int(never.sum())} bets ${pl[never].sum():+,.0f} ({pl[never].sum() / max(st[never].sum(), 1):+.0%}); it had moved: {int((hit & ~never).sum())} bets ${pl[hit & ~never].sum():+,.0f} ({pl[hit & ~never].sum() / max(st[hit & ~never].sum(), 1):+.0%})")
        # where was that major's price later? (4 h before the jump if that is after 9am, else 1 h before)
        later = np.where((nine_v[:, None] < -240) & np.isfinite(T240), T240, T60)
        ok2 = hit & np.isfinite(later); r = later[ok2] / NB[ok2]
        print(f"that major's price later in the morning against its 9am price ({int(ok2.sum())} bets): cut by 10%+ {np.mean(r < 0.9):.0%}, within 10% {np.mean((r >= 0.9) & (r <= 1.1)):.0%}, pushed out 10%+ {np.mean(r > 1.1):.0%}; median {np.median(r):.2f}")
        for lab, x in (("Nov 2025-Jun 2026", vd < "2026-07-01"), ("Jul-Nov 2026", vd >= "2026-07-01")):
            print(f"  {lab}: {int(hit[x].sum())} bets ${pl[x].sum():+,.0f} ({pl[x].sum() / max(st[x].sum(), 1):+.0%}); by major " + ", ".join(f"{bk} {int(hit[x][:, k].sum())}" for k, bk in enumerate(MAJORS)))
