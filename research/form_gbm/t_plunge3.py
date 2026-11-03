"""Ranarsson's profile on the holdout: lightly raced last-start winners we rate short. Do we underrate them? (3 Nov 2026)"""
import numpy as np
src = open("t_all_rules.py").read().split('summ(plan(pm0), "all rules')[0]
exec(src)
X = z["X"]; cols = list(map(str, z["cols"])); col = lambda c: X[:, cols.index(c)].astype(float)
pf = list(map(str, z["past_fields"])); P = z["P"]; fin = pf.index("finish")
# most recent run = the first row holding a finish (check both orders on the data below)
first = np.array([next((P[i, r, fin] for r in range(P.shape[1]) if np.isfinite(P[i, r, fin])), np.nan) for i in range(len(P))])
last_ = np.array([next((P[i, r, fin] for r in range(P.shape[1] - 1, -1, -1) if np.isfinite(P[i, r, fin])), np.nan) for i in range(len(P))])
days = np.exp(col("raw_days_log")); starts = col("raw_starts"); age = col("raw_age")
b = plan(pmS); idx = np.array([i for i, _ in b]); st = np.array([s for _, s in b])
ours = 1 / pmS; ratio = bs / o
def line(lab, k, base):
    ii = base[k[base]]
    if len(ii) < 15: print(f"  {lab:48s} {len(ii):4d} (too few)"); return
    w = won[ii]; s = st[np.isin(idx, ii)] if base is idx else np.ones(len(ii))
    plo = np.where(w, s * (o[ii] - 1) * 0.93, -s).sum(); plb = np.where(w, s * (bs[ii] - 1) * 0.92, -s).sum()
    print(f"  {lab:48s} {len(ii):4d} bets {w.sum():3d} won | ours exp {pmS[ii].sum():5.1f} A/E {w.sum()/pmS[ii].sum():4.2f} | BSP exp {(1/bs[ii]).sum():5.1f} A/E {w.sum()/(1/bs[ii]).sum():4.2f} | plunge {100*(ratio[ii]<=0.6).mean():3.0f}% | open {100*plo/s.sum():+4.0f}% BSP {100*plb/s.sum():+4.0f}%")
for nm, wonlast in (("row 0 = most recent", first == 1), ("last row = most recent", last_ == 1)):
    print(f"\nSHEET BETS, won last start ({nm}):")
    line("won last start", wonlast, idx)
    line("won last start, 1-3 career starts", wonlast & (starts <= 3), idx)
    line("won last start, 1-3 starts, ours under $4", wonlast & (starts <= 3) & (ours < 4), idx)
    line("won last start, 3yo, 1-3 starts", wonlast & (starts <= 3) & (age == 3), idx)
    line("did not win last start", ~wonlast & np.isfinite(first), idx)
A = np.where(m & ~fs & (ours >= 1.6) & (ours <= 15))[0]
print("\nALL RATED RUNNERS $1.60-$15 (1u each):")
line("won last start, 1-3 starts", (first == 1) & (starts <= 3), A)
line("won last start, 1-3 starts, ours under $4", (first == 1) & (starts <= 3) & (ours < 4), A)
line("won last start, 1-3 starts, ours under $4, open >= 1.2x", (first == 1) & (starts <= 3) & (ours < 4) & (o >= 1.2 * ours), A)
