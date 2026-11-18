import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
V = np.load(os.path.join(HERE, "i_vic_9am.npz"), allow_pickle=True)
FM = np.load(os.path.join(HERE, "fair_models.npy")); names = open(os.path.join(HERE, "fair_models.txt")).read().split("\n")
pa = FM[:, names.index("ours + median + move")]; fa = np.where(pa > 0, 1 / np.maximum(pa, 1e-12), np.nan)
key = {(date[i], int(rno[i]), norm(name[i])): i for i in range(n)}
vd, vr, vn = V["date"].astype(str), V["race"], V["name"].astype(str)
j = np.array([key.get((vd[i], int(vr[i]), norm(vn[i])), -1) for i in range(len(vd))]); m = j >= 0; jj = np.maximum(j, 0)
hit, st, pl = bets(fa, pa > 0, B7); ha = hit.any(1)[jj] & m
hv = V["hits"] > 0; both = V["test"] & m & (pa[jj] > 0) & np.isfinite(V["fp"])
vm = np.array([d[:7] for d in vd])
print("| month | i_vic runners bet | P/L | also a_model | i_vic only: n, P/L | a_model only: n | median fair ratio i/a | ours share ratio Pe/P median, 10-90 |")
for mo in sorted(set(vm[V["test"]])):
    x = vm == mo; r = V["fp"][both & x] / fa[jj[both & x]]; q = V["Pe"][both & x & V["ran"]] / np.maximum(P[jj[both & x & V["ran"]]], 1e-12)
    ao = ha & ~hv & x
    print(f"| {mo} | {int((hv & x).sum())} | ${V['pl'][hv & x].sum():+,.0f} | {int((hv & ha & x).sum())} | {int((hv & ~ha & x).sum())}, ${V['pl'][hv & ~ha & x].sum():+,.0f} | {int(ao.sum())} | {np.median(r):.3f} | {np.median(q):.3f}, {np.percentile(q, 10):.2f}-{np.percentile(q, 90):.2f} |")
# is the difference the ghosts? races where the two disagree about who was in the 9am market
vkey = np.char.add(vd, np.char.add("|", vr.astype(str)))
gh_v = V["ok"] & ~V["ran"]                                    # exact late scratchings in i_vic
vrace_has = {}
for i in np.where(gh_v)[0]: vrace_has[(vd[i], int(vr[i]))] = vrace_has.get((vd[i], int(vr[i])), 0) + 1
crace_has = {}
for i in np.where(ghost)[0]: crace_has[(date[i], int(rno[i]))] = crace_has.get((date[i], int(rno[i])), 0) + 1
dis = np.array([(vrace_has.get((vd[i], int(vr[i])), 0) != crace_has.get((vd[i], int(vr[i])), 0)) for i in range(len(vd))])
for lab, x in (("races where the two agree on late scratchings", ~dis), ("races where they disagree", dis)):
    print(f"{lab}: i_vic bets on {int((hv & x).sum())} runners ${V['pl'][hv & x].sum():+,.0f} on ${V['st'][hv & x].sum():,.0f}; of them also a_model {int((hv & ha & x).sum())}; i_vic only {int((hv & ~ha & x).sum())} ${V['pl'][hv & ~ha & x].sum():+,.0f}")
# the i_vic-only bets: how far over the take price were they, and what would a_model's fair price say
x = hv & ~ha & both
Bv = V["B"]; bestp = np.nanmax(Bv, 1)
print("i_vic only: best major price / i_vic fair, median", np.median(bestp[x] / V["fp"][x]), "; best / a_model fair, median", np.median(bestp[x] / fa[jj[x]]), "; share where a_model fair is longer than the best price", np.mean(fa[jj[x]] > bestp[x]))
print("  by i_vic fair price: " + "; ".join(f"${a}-${b}: {int((x & (V['fp'] >= a) & (V['fp'] < b)).sum())} runners ${V['pl'][x & (V['fp'] >= a) & (V['fp'] < b)].sum():+,.0f}" for a, b in ((1.6, 3), (3, 5), (5, 8), (8, 15.01))))
x3 = hv & ha
print("both:  best / i_vic fair median", np.median(bestp[x3] / V["fp"][x3]), "; best / a_model fair median", np.median(bestp[x3] / fa[jj[x3]]))
