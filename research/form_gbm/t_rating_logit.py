"""Conditional logit of winning on Form King WFA ratings (last start, best of last 5), within race.
Fitted on the v10 dataset (Vic races). Prints coefficients per point for all races and metro-only."""
import numpy as np, sys
z = np.load(sys.argv[1], allow_pickle=True)
pf = list(z["past_fields"]); P = z["P"]; ri = z["race_idx"]; fin = z["finish"]; trk = z["track"]
iw, iwr, itr = pf.index("wfa"), pf.index("wfaRat"), pf.index("trial")
rat = np.where(np.isfinite(P[:, :, iwr]) & (P[:, :, iwr] > 0), P[:, :, iwr], P[:, :, iw])
trial = np.nan_to_num(P[:, :, itr]) > 0
rat = np.where(trial | ~np.isfinite(rat) | (rat <= 0), np.nan, rat)
def first_valid(row):
    v = row[np.isfinite(row)]; return v[0] if len(v) else np.nan
last = np.array([first_valid(r) for r in rat])
best5 = np.array([np.nanmax(r[np.isfinite(r)][:5]) if np.isfinite(r).any() else np.nan for r in rat])
metro = {"Flemington", "Caulfield", "Caulfield Heath", "Moonee Valley", "Sandown Hillside", "Sandown Lakeside"}
def fit(mask_races, feats):
    # keep races where every runner is rated and exactly one winner
    rows = []
    for r in mask_races:
        m = ri == r
        if m.sum() < 6 or (fin[m] == 1).sum() != 1: continue
        X = np.column_stack([f[m] for f in feats])
        if not np.isfinite(X).all(): continue
        rows.append((X - X.mean(0), (fin[m] == 1).astype(float)))
    b = np.zeros(len(feats))
    for _ in range(30):
        g = np.zeros_like(b); H = np.zeros((len(b), len(b))); ll = 0
        for X, y in rows:
            u = X @ b; p = np.exp(u - u.max()); p /= p.sum()
            g += X.T @ (y - p); H -= (X * p[:, None]).T @ X - np.outer(X.T @ p, X.T @ p); ll += np.log(p[y == 1][0])
        b -= np.linalg.solve(H, g)
    se = np.sqrt(np.diag(np.linalg.inv(-H)))
    base = sum(np.log(1 / len(y)) for _, y in rows)
    return b, se, len(rows), ll, base
races = np.unique(ri)
mr = [r for r in races if str(trk[r]) in metro]
for name, rs in (("all", races), ("metro", mr)):
    for fn, feats in (("last", [last]), ("last+best5", [last, best5])):
        b, se, n, ll, base = fit(rs, feats)
        print(f"{name:5} {fn:11} races {n:4}  coef/pt {np.round(b,4)}  se {np.round(se,4)}  loglik {ll/n:.4f} vs uniform {base/n:.4f}")
