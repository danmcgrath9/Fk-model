"""A systematic scan of back and lay cells at BSP (3 Nov 2026, founder: "Surely there's some other things we can find?").
v10 holdout from 3 Jun, 8% commission, flat 1u. Cells: BSP band x (BSP / ours) x market rank. A cell is reported only if
it is positive in BOTH halves with at least 60 runners in each; with ~100 cells some will pass by luck, so this is a
list of candidates, not rules."""
import numpy as np, itertools
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
p10 = np.load("v10_profit_preds.npz")["p10"]; o = z["open"].astype(float); bs = z["bsp"].astype(float); won = z["finish"] == 1
okr = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1)
m = race_ok[ri]
s = np.bincount(ri, weights=np.where(m, p10, 0), minlength=nR); pm = np.where(m, p10 / np.where(s[ri] > 0, s[ri], 1), np.nan); ours = 1 / pm
ratio = bs / ours   # >1: market longer than us (we are short); <1: market shorter than us
rank = np.zeros(len(bs), int)
for r in np.where(race_ok)[0]:
    ii = np.where(ri == r)[0]; order = ii[np.argsort(bs[ii])]
    for k, i in enumerate(order): rank[i] = k + 1
cut = sorted(set(rdate[race_ok]))[len(set(rdate[race_ok])) // 2]; early = date < cut
bands = [(1, 2.5), (2.5, 4), (4, 7), (7, 12), (12, 20), (20, 40), (40, 1000)]
ratios = [(0, 0.5), (0.5, 0.7), (0.7, 0.85), (0.85, 1.0), (1.0, 1.2), (1.2, 1.6), (1.6, 2.5), (2.5, 99)]
ranks = [(1, 1, "fav"), (2, 2, "2nd"), (3, 99, "3rd+"), (1, 99, "any")]
out = []
for (b0, b1), (r0, r1), (k0, k1, kl) in itertools.product(bands, ratios, ranks):
    g = m & (bs >= b0) & (bs < b1) & (ratio >= r0) & (ratio < r1) & (rank >= k0) & (rank <= k1)
    res = []
    for hm in (early, ~early):
        gg = g & hm; n = gg.sum()
        if n < 60: res = None; break
        back = np.where(won[gg], (bs[gg] - 1) * 0.92, -1.0).sum() / n; lay = np.where(won[gg], -(bs[gg] - 1), 0.92).sum() / n
        res.append((n, int(won[gg].sum()), (1 / bs[gg]).sum(), back, lay))
    if not res: continue
    for side in ("back", "lay"):
        j = 3 if side == "back" else 4
        if res[0][j] > 0 and res[1][j] > 0:
            out.append((side, f"BSP ${b0}-${b1}", f"BSP/ours {r0}-{r1}", kl, res))
print(f"{len(out)} cells positive in both halves (of {len(bands)*len(ratios)*len(ranks)*2} tested, many too small to count)")
for side, b, r, kl, res in sorted(out, key=lambda x: -min(x[4][0][3 if x[0]=='back' else 4], x[4][1][3 if x[0]=='back' else 4])):
    j = 3 if side == "back" else 4
    print(f"{side:<4} {b:<14} {r:<20} {kl:<4}  early n={res[0][0]:4d} won {res[0][1]:3d} exp {res[0][2]:5.1f} {100*res[0][j]:+5.0f}%   late n={res[1][0]:4d} won {res[1][1]:3d} exp {res[1][2]:5.1f} {100*res[1][j]:+5.0f}%")
