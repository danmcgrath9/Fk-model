"""Is 0.82 ours + 0.22 open still the right blend? (night of 10 Nov 2026). The weights were fitted 12 Oct on the holdout
(stage-2 price KL 0.080). The committed live price has run at 0.10 since (riders missing in October, late scratchings,
stale history), so the best mix on the live weeks may lean more on the open. Grid on the live files, 15 Oct - 9 Nov,
two halves (fit on one, score on the other), and on the replay's fresh-history stage-2 price for comparison.
    python3.13 blend_live.py   (replay folder)"""
import numpy as np
Z = np.load("ds/model_ds.npz", allow_pickle=True); LJ = np.load("live_join.npz"); R = np.load("replay_stale.npz")
ri = Z["race_idx"]; nR = len(Z["race_id"]); rdate = Z["date"].astype(str); date = rdate[ri]
bs = Z["bsp"].astype(float); op = Z["open"].astype(float); won = Z["finish"] == 1
def norm(x):
    ok = np.isfinite(x) & (x > 1); inv = np.where(ok, 1 / np.where(ok, x, 2), 0)
    return inv / np.maximum(np.bincount(ri, weights=inv, minlength=nR)[ri], 1e-12), np.bincount(ri, weights=~ok, minlength=nR) == 0
q, qf = norm(bs); mk, mf = norm(op)
def sm(s):
    mx = np.full(nR, -np.inf); np.maximum.at(mx, ri, np.where(np.isfinite(s), s, -np.inf)); e = np.where(np.isfinite(s), np.exp(s - mx[ri]), 0)
    return e / np.maximum(np.bincount(ri, weights=e, minlength=nR)[ri], 1e-300)
def kl(p, m): return np.sum(np.where(q[m] > 0, q[m] * np.log(np.maximum(q[m], 1e-300) / np.maximum(p[m], 1e-12)), 0)) / len(np.unique(ri[m]))
def ll(p, m): return -np.mean(np.log(np.maximum(p[m & won], 1e-12)))
for lab, pm in (("LIVE committed price", LJ["p_model"]), ("replay, stale history", R["stale"][:, 3]), ("replay, FRESH history", R["fresh"][:, 3])):
    have = np.isfinite(pm) & (pm > 0); g = ((np.bincount(ri, weights=~have, minlength=nR) == 0) & qf & mf & (np.bincount(ri, weights=won, minlength=nR) == 1))[ri] & (date > "2026-10-14")
    lp, lo = np.log(np.maximum(np.nan_to_num(pm, nan=1e-12), 1e-12)), np.log(np.maximum(mk, 1e-12))
    A = np.arange(0.40, 1.01, 0.02); B = np.arange(0.0, 0.71, 0.02)
    def best(m):
        grid = np.array([[kl(sm(a * lp + b_ * lo), m) for b_ in B] for a in A]); i, j = np.unravel_index(grid.argmin(), grid.shape); return A[i], B[j], grid[i, j]
    h1 = g & (date < "2026-10-29"); h2 = g & (date >= "2026-10-29")
    a1, b1, _ = best(h1); a2, b2, _ = best(h2); aa, bb, kk = best(g)
    live_w = sm(0.82 * lp + 0.22 * lo); cross = (kl(sm(a1 * lp + b1 * lo), h2) * len(np.unique(ri[h2])) + kl(sm(a2 * lp + b2 * lo), h1) * len(np.unique(ri[h1]))) / len(np.unique(ri[g]))
    print(f"{lab}: {len(np.unique(ri[g]))} races")
    print(f"  ours alone KL {kl(pm, g):.4f} log loss {ll(pm, g):.4f} | open alone {kl(mk, g):.4f} / {ll(mk, g):.4f} | 0.82/0.22 blend {kl(live_w, g):.4f} / {ll(live_w, g):.4f}")
    print(f"  best weights: first half {a1:.2f}/{b1:.2f}, second half {a2:.2f}/{b2:.2f}, all {aa:.2f}/{bb:.2f} (KL {kk:.4f}); fitted on one half and scored on the other: KL {cross:.4f}")
