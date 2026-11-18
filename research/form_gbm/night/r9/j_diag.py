"""j_diag.py: why does the Victorian 9am test differ between the two price sources? Join them runner by runner."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
D = np.load(os.path.join(HERE, "nat.npz"), allow_pickle=True)
v = D["state"].astype(str) == "VIC"
nd, nrace, nname = D["date"].astype(str)[v], D["race"][v], D["name"].astype(str)[v]
nscr, nnine, npos = D["scr"][v], D["nine"][v], D["pos"][v]
NB = np.column_stack([D[f"{b}_0900"][v] for b in MAJORS]); NF = D["tab_first"][v]
key = {(date[i], int(rno[i]), norm(name[i])): i for i in range(n)}
j = np.array([key.get((nd[i], int(nrace[i]), norm(nname[i])), -1) for i in range(len(nd))])
m = j >= 0; print("national VIC runners", len(nd), "matched to common (incl ghosts)", int(m.sum()))
a = B7[j[m]]; b = NB[m]
for k, bk in enumerate(MAJORS):
    both = np.isfinite(a[:, k]) & np.isfinite(b[:, k]); same = both & (np.abs(a[:, k] - b[:, k]) < 0.011)
    print(f"  {bk}: both have a 9am price {int(both.sum())}, same {int(same.sum())} ({same.sum() / max(both.sum(), 1):.1%}); only common {int((np.isfinite(a[:, k]) & ~np.isfinite(b[:, k])).sum())}; only national {int((~np.isfinite(a[:, k]) & np.isfinite(b[:, k])).sum())}; "
          f"median ratio national/common {np.nanmedian(b[both, k] / a[both, k]):.3f}; national longer by 5%+ {int((both & (b[:, k] > 1.05 * a[:, k])).sum())}, shorter by 5%+ {int((both & (b[:, k] < a[:, k] / 1.05)).sum())}")
# nine: minutes
print("nine (common) vs nine (national), matched: median diff", np.nanmedian(nine[j[m]] - nnine[m]), "; share within 2 min", np.nanmean(np.abs(nine[j[m]] - nnine[m]) <= 2))
# ghosts
late = np.isfinite(nscr) & (nscr >= nnine)                 # scratched after 9am, exact
early = np.isfinite(nscr) & (nscr < nnine)
print("national: scratched after 9am", int(late.sum()), "; of them a ghost in common", int((late & m & ghost[np.maximum(j, 0)]).sum()), "; not in common at all", int((late & ~m).sum()), "; in common as a runner", int((late & m & ~ghost[np.maximum(j, 0)]).sum()))
print("national: scratched before 9am", int(early.sum()), "; of them a ghost in common (a false ghost)", int((early & m & ghost[np.maximum(j, 0)]).sum()))
gi = np.where(ghost)[0]; gset = set(j[m]); print("common ghosts", len(gi), "; matched to a national row", sum(1 for g in gi if g in gset))
gm = m & ghost[np.maximum(j, 0)]
print("  common ghosts by national status: scratched after 9am", int((gm & late).sum()), ", before 9am", int((gm & early).sum()), ", no scratching time (ran?)", int((gm & ~np.isfinite(nscr)).sum()))
# first price
fc = np.array([p[1][0] if p is not None else np.nan for p in tab])[j[m]]; both = np.isfinite(fc) & np.isfinite(NF[m])
print("TAB first price: same", np.mean(np.abs(fc[both] - NF[m][both]) < 0.011))
