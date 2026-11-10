"""Should the blend with the open depend on the race? (night of 10 Nov 2026). One pair of weights (0.82 ours, 0.22 open)
is used everywhere (metro has its own lean in the order sheet). Walk-forward trees, races with every open and BSP,
1 Jan - 9 Nov 2026. For each way of splitting the races, the weights are fitted per group on one half of the year and
scored on the other (both directions), against ONE pair of weights fitted the same way.
    python3.13 blend_segments.py   (night folder)"""
import numpy as np, sys
import nl
D, ri, nR, date, q = nl.D, nl.ri, nl.nR, nl.date, nl.q
P = np.where(date >= "2026-06-03", np.load("preds/base_A.npy"), np.load("preds/base_B.npy")).astype(float)
o = nl.o; okr = nl.race_ok & (np.bincount(ri, weights=~(np.isfinite(nl.bs) & (nl.bs > 1)), minlength=nR) == 0)
mk = D["mkt"]; lp, lo = np.log(np.maximum(P, 1e-12)), np.log(np.maximum(mk, 1e-12))
oos = (nl.rdate >= "2026-01-01") & okr; H = {0: oos & (nl.rdate < "2026-06-03"), 1: oos & (nl.rdate >= "2026-06-03")}
starts, ends = D["starts"], D["ends"]
def klr(a, b_, races):
    tot = 0.0
    for r in races:
        s = a * lp[starts[r]:ends[r]] + b_ * lo[starts[r]:ends[r]]; s = s - s.max(); p = np.exp(s); p /= p.sum(); qq = q[starts[r]:ends[r]]
        tot += np.sum(np.where(qq > 0, qq * np.log(np.maximum(qq, 1e-300) / np.maximum(p, 1e-12)), 0))
    return tot
A = np.arange(0.5, 1.01, 0.04); B = np.arange(0.0, 0.61, 0.04)
def fit(races):
    if len(races) < 40: return (0.82, 0.22)
    g = [(klr(a, b_, races), a, b_) for a in A for b_ in B]; _, a, b_ = min(g); return (a, b_)
X, cols = D["X"], list(D["cols"]); fs = np.bincount(ri, weights=(X[:, cols.index("firstStarter")] == 1), minlength=nR)
track = np.char.lower(D["track"].astype(str)); metro = np.isin(track, ("flemington", "caulfield", "caulfield heath", "moonee valley", "sandown hillside", "sandown lakeside"))
field = np.bincount(ri, minlength=nR); dist = D["distance"].astype(float)
age2 = np.bincount(ri, weights=(X[:, cols.index("age")] == 2), minlength=nR) > 0
SPLITS = {"one pair for every race": np.zeros(nR, int), "first starters in the race: 0 / 1 / 2+": np.minimum(fs, 2).astype(int), "metro / not": metro.astype(int),
          "field: up to 8 / 9-12 / 13+": np.where(field <= 8, 0, np.where(field <= 12, 1, 2)), "distance: to 1200 / to 1600 / longer": np.where(dist <= 1200, 0, np.where(dist <= 1600, 1, 2)),
          "a 2yo in the race / not": age2.astype(int)}
nall = int(oos.sum()); print(f"{nall} races; ours alone KL {klr(1, 0, np.where(oos)[0])/nall:.4f}, the open alone {klr(0, 1, np.where(oos)[0])/nall:.4f}, live 0.82/0.22 {klr(0.82, 0.22, np.where(oos)[0])/nall:.4f}\n")
print("| weights by | KL to BSP, fitted on the other half | weights fitted on the whole year |\n|---|---|---|")
for name, grp in SPLITS.items():
    tot = 0.0; desc = []
    for h in (0, 1):
        for g in np.unique(grp):
            tr = np.where(H[1 - h] & (grp == g))[0]; te = np.where(H[h] & (grp == g))[0]; a, b_ = fit(tr); tot += klr(a, b_, te)
    for g in np.unique(grp):
        a, b_ = fit(np.where(oos & (grp == g))[0]); desc.append(f"{a:.2f}/{b_:.2f} ({int((oos & (grp == g)).sum())})")
    print(f"| {name} | {tot/nall:.4f} | {'; '.join(desc)} |")
