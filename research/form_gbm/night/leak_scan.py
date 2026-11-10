"""Leak scan (night of 10 Nov 2026): does any model input know the winner beyond what BSP knows?
BSP is close to efficient, so an input that still predicts the winner strongly AFTER BSP is either a leak (a figure
written after the race, or a count that includes today's result) or a real hole in the market. Score test of a
conditional logit with BSP's chances as the null: per input, U = sum over races of (winner's value - BSP-weighted mean of
the field), V = the BSP-weighted variance; z = U / sqrt(V). Inputs are ranked within the race first (robust to outliers),
missing values sit at the race's BSP-weighted mean. With 809 inputs the largest |z| by chance is about 3.2.
Also the same against OUR out-of-sample price instead of BSP is not done here: this is only the leak check.
    python3.13 leak_scan.py   (night folder: F9n.npy, ds/model_ds.npz)"""
import numpy as np, bench as b
D = b.load("ds/model_ds.npz"); ri = D["race_idx"]; nR = D["n_races"]
F = np.load("F9n.npy"); NM = open("F9n_names.txt").read().split("\n"); q = D["q"]; won = D["won"] == 1
bs = D["bsp"]; ok_r = (np.bincount(ri, weights=~(np.isfinite(bs) & (bs > 1)), minlength=nR) == 0) & (np.bincount(ri, weights=won, minlength=nR) == 1)
date = D["date"].astype(str)[ri]; n = np.bincount(ri, minlength=nR)[ri]


def scan(mask):
    out = []
    m = mask & ok_r[ri]
    for j in range(F.shape[1]):
        x = F[:, j].astype(float); fin = np.isfinite(x) & m
        if fin.sum() < 2000: out.append((0.0, 0, np.nan)); continue
        # rank within race among finite values, scaled to [-0.5, 0.5]
        order = np.lexsort((x, ri)); r = np.empty(len(x)); r[order] = np.arange(len(x))
        first = np.searchsorted(ri[order], ri); xr = np.where(fin, (r - first) / np.maximum(n - 1, 1) - 0.5, np.nan)
        mu = np.bincount(ri, weights=np.where(fin, q * xr, 0), minlength=nR) / np.maximum(np.bincount(ri, weights=np.where(fin, q, 0), minlength=nR), 1e-12)
        xc = np.where(fin, xr - mu[ri], 0.0)             # missing -> the race's BSP-weighted mean
        U = np.sum(xc[m & won]); V = np.sum((q * xc ** 2)[m]) - np.sum(np.bincount(ri, weights=np.where(m, q * xc, 0), minlength=nR) ** 2)
        out.append((U / np.sqrt(max(V, 1e-12)), int(fin.sum()), U))
    return np.array([o[0] for o in out])


zall = scan(np.ones(len(ri), bool)); z1 = scan(date < "2026-03-01"); z2 = scan(date >= "2026-03-01")
print(f"{int(ok_r.sum())} races with a full BSP book and one winner; {F.shape[1]} inputs")
print(f"largest |z|: all {np.nanmax(np.abs(zall)):.2f}; inputs with |z| > 3.2: {int(np.sum(np.abs(zall) > 3.2))}; > 4: {int(np.sum(np.abs(zall) > 4))}; > 5: {int(np.sum(np.abs(zall) > 5))}")
print("\nThe 30 inputs with the most win information beyond BSP (z all races | before Mar 2026 | from Mar 2026):")
for j in np.argsort(-np.abs(zall))[:30]:
    print(f"  {NM[j]:44s} {zall[j]:+6.2f} | {z1[j]:+6.2f} | {z2[j]:+6.2f}")
same = np.sum((np.abs(zall) > 3.2) & (np.sign(z1) == np.sign(z2)) & (np.abs(z1) > 2) & (np.abs(z2) > 2))
print(f"\ninputs over 3.2 overall AND over 2 with the same sign in both halves: {int(same)}")
np.save("leak_z.npy", np.column_stack([zall, z1, z2]))
