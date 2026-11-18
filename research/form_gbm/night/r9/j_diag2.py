import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
V = np.load(os.path.join(HERE, "i_vic_9am.npz"), allow_pickle=True)
FM = np.load(os.path.join(HERE, "fair_models.npy")); names = open(os.path.join(HERE, "fair_models.txt")).read().split("\n")
k = names.index("ours + median + move"); pa = FM[:, k]; fa = np.where(pa > 0, 1 / np.maximum(pa, 1e-12), np.nan)
key = {(date[i], int(rno[i]), norm(name[i])): i for i in range(n)}
vd, vr, vn = V["date"].astype(str), V["race"], V["name"].astype(str)
j = np.array([key.get((vd[i], int(vr[i]), norm(vn[i])), -1) for i in range(len(vd))]); m = j >= 0
hit, st, pl = bets(fa, pa > 0, B7)
late = (date >= "2026-03-01")
print("a_model 'ours + median + move', all test months:", int(hit.sum()), "bets", int(hit.any(1).sum()), "runners", f"${pl.sum():+,.0f}", f"{pl.sum() / st.sum():+.1%}")
print("a_model, Mar-Nov 2026 only:", int(hit[late].sum()), "bets", int(hit[late].any(1).sum()), "runners", f"${pl[late].sum():+,.0f}", f"{pl[late].sum() / st[late].sum():+.1%}", "; races with a fair price:", len(np.unique(ri[late & (pa > 0)])))
print("a_model, Nov 2025-Feb 2026:", int(hit[~late].sum()), "bets", f"${pl[~late].sum():+,.0f}", f"{pl[~late].sum() / max(st[~late].sum(), 1):+.1%}")
vt = V["test"]; print("i_vic 9am: test runners", int(vt.sum()), "; matched to common", int((vt & m).sum()), "; with an a_model fair price", int((vt & m & (pa[np.maximum(j, 0)] > 0)).sum()))
both = vt & m & (pa[np.maximum(j, 0)] > 0) & np.isfinite(V["fp"])
r = V["fp"][both] / fa[j[both]]
print("fair price i_vic / a_model on the same runners: median", np.median(r), "; 10th-90th", np.percentile(r, [10, 90]), "; share within 3%", np.mean(np.abs(np.log(r)) < 0.03))
hv = V["hits"] > 0
print("i_vic runners bet", int(hv.sum()), "; of them matched", int((hv & m).sum()), "; with an a_model fair price", int((hv & both).sum()), "; also bet by a_model", int((hv & both & hit.any(1)[np.maximum(j, 0)]).sum()))
only = hv & ~(both & hit.any(1)[np.maximum(j, 0)])
print("bet by i_vic only:", int(only.sum()), f"P/L ${V['pl'][only].sum():+,.0f} on ${V['st'][only].sum():,.0f}; in a race a_model did not use: {int((only & ~both).sum())}, P/L ${V['pl'][only & ~both].sum():+,.0f} on ${V['st'][only & ~both].sum():,.0f}")
com = hv & both & hit.any(1)[np.maximum(j, 0)]
print("bet by both:", int(com.sum()), f"i_vic P/L ${V['pl'][com].sum():+,.0f} on ${V['st'][com].sum():,.0f}")
x = only & both
print("bet by i_vic only, in a race both used:", int(x.sum()), "; fair price ratio i_vic/a_model median", np.median(V["fp"][x] / fa[j[x]]), f"P/L ${V['pl'][x].sum():+,.0f} on ${V['st'][x].sum():,.0f}")
# why are races not used by a_model?
x2 = np.where(only & ~both)[0][:12]
for i in x2:
    jj = j[i]; print("  ", vd[i], vr[i], vn[i], "fp", round(float(V["fp"][i]), 2), "matched" if jj >= 0 else "NOT IN COMMON", ("P>0 " + str(P[jj] > 0) + " pa>0 " + str(pa[jj] > 0) + " T9 " + str(T9[jj]) + " ghost " + str(bool(ghost[jj]))) if jj >= 0 else "")
