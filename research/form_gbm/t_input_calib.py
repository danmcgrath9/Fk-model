"""Does every input make sense? (1 Nov 2026, founder.) Full history, out of fold (p_oof_blend9: each race priced by trees
that never saw it). For every stage-1 column: runners split into five bands of that input (missing as its own band), and in
each band the actual winners against the model's expected winners. An input the model has right shows 1.00 in every band.
A SLOPE (ratio rising or falling across the bands) means the model under- or over-reacts to that input: the first place a
direct adjustment, like the metro and straight ones, could earn. Flagged when the top and bottom bands differ by 0.15+ and
each holds 40+ expected winners, and the slope holds in BOTH date halves."""
import numpy as np
z = np.load("ds/model_ds.npz", allow_pickle=True); p = np.load("p_oof_blend9.npy").astype(float)
ri = z["race_idx"]; nR = int(ri.max()) + 1; won = z["finish"] == 1; bs = z["bsp"].astype(float); cols = [str(c) for c in z["cols"]]; X = z["X"].astype(float)
cnt = np.bincount(ri, minlength=nR); ok = np.isfinite(p) & (p > 0) & np.isfinite(bs) & (bs > 1)
race_ok = (np.bincount(ri, weights=ok.astype(float), minlength=nR) == cnt) & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1); m = race_ok[ri]
s = np.bincount(ri, weights=np.where(m, p, 0), minlength=nR); pm = np.where(m, p / np.where(s[ri] > 0, s[ri], 1), np.nan)
d = z["date"].astype(str)[ri]; h1 = d < "2026-02-15"
out = []
for j, c in enumerate(cols):
    v = X[:, j]; f = m & np.isfinite(v)
    if f.sum() < 2000 or len(np.unique(v[f])) < 3: continue
    qs = np.nanpercentile(v[f], [20, 40, 60, 80]); band = np.searchsorted(qs, v, side="right"); band = np.where(np.isfinite(v), band, -1)
    def ratio(sel):
        r = []
        for b in range(5):
            g = sel & (band == b); e = pm[g].sum(); r.append((won[g].sum() / e if e >= 40 else np.nan, e))
        return r
    ra = ratio(m); r1 = ratio(m & h1); r2 = ratio(m & ~h1)
    vals = [x for x, e in ra if np.isfinite(x)]
    if len(vals) < 3: continue
    lo, hi = vals[0], vals[-1]; slope = hi - lo
    s1 = [x for x, e in r1 if np.isfinite(x)]; s2 = [x for x, e in r2 if np.isfinite(x)]
    both = len(s1) >= 2 and len(s2) >= 2 and np.sign(s1[-1] - s1[0]) == np.sign(slope) and np.sign(s2[-1] - s2[0]) == np.sign(slope) and abs(s1[-1] - s1[0]) >= 0.08 and abs(s2[-1] - s2[0]) >= 0.08
    worst = max(abs(x - 1) for x in vals)
    out.append((abs(slope) if both else 0, worst, c, slope, both, [f"{x:.2f}" if np.isfinite(x) else "-" for x, e in ra], f"{min(e for x,e in ra if np.isfinite(x)):.0f}"))
out.sort(reverse=True)
print(f"{len(out)} inputs tested. Bands are low -> high of the input; each cell = actual winners / model expected.")
print("\nFLAGGED: a slope across the bands that holds in both date halves")
for sl, w, c, slope, both, r, e in out:
    if both and abs(slope) >= 0.15: print(f"  {c:42s} {' '.join(f'{x:>5s}' for x in r)}  (min exp wins/band {e})")
print("\nWORST SINGLE BAND (0.80 or under / 1.20 or over), any input, both halves not required")
k = 0
for sl, w, c, slope, both, r, e in sorted(out, key=lambda t: -t[1]):
    if w >= 0.2 and k < 25: print(f"  {c:42s} {' '.join(f'{x:>5s}' for x in r)}"); k += 1
