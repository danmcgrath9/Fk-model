"""Would our model blended with the market beat BSP? (12 Nov 2026, founder: "If we blended our model with the market,
would we beat bsp?") The 10 Nov challenger's out-of-fold blend (p_oof_chal.npy) mixed in log space with a market price,
log p = a log(ours) + b log(market), renormalised per race. Weights are fitted on one half and scored on the other
(2025 <-> 2026), never on the races they are scored on. Two questions:
  1. Is the blend a better price than BSP? Winner log loss (lower is better) against BSP's own (1/BSP renormalised).
  2. Does it find bets at BSP? Back every runner whose BSP is at least k x the blend's price; 1u at BSP, 8% commission.
Markets: the open (every race, 16 months), 9am race morning and the last price before the jump (timed races only: fluc_minutes.py).
    python3.13 t_blend_bsp.py FLUC_MINUTES.md   (night folder)"""
import csv, io, sys
import numpy as np
z = np.load("ds/model_ds.npz", allow_pickle=True); P = np.load("p_oof_chal.npy").astype(float)
ri = z["race_idx"]; nR = len(z["race_id"]); date = z["date"].astype(str)[ri]; rid = z["race_id"].astype(str)[ri]; hid = z["horse_id"].astype(str)
won = np.asarray(z["finish"], float) == 1; o = np.asarray(z["open"], float); bs = np.asarray(z["bsp"], float)
s = open(sys.argv[1]).read(); a = s.find("CSV-BEGIN") + 9; b = s.find("CSV-END")
key = {(r["race_id"], r["horse_id"]): r for r in csv.DictReader(io.StringIO(s[a:b].strip()))}
col = lambda c: np.array([float(key[(rid[i], hid[i])][c]) if (rid[i], hid[i]) in key and key[(rid[i], hid[i])][c] else np.nan for i in range(len(ri))])
jp = col("jump"); p9 = col("c0900")
def norm(x, m):
    out = np.full(len(x), np.nan); s_ = np.bincount(ri[m], weights=x[m], minlength=nR); out[m] = x[m] / s_[ri[m]]; return out
def good(mk):   # races where every runner has a positive model price, a BSP, a winner and the market price
    ok = np.isfinite(mk) & (mk > 1) & np.isfinite(bs) & (bs > 1) & (P > 0)
    r_ok = (np.bincount(ri, weights=~ok, minlength=nR) == 0) & (np.bincount(ri, weights=won, minlength=nR) == 1)
    return r_ok[ri]
def ll(p, m): return -np.mean(np.log(np.maximum(p[m & won], 1e-12)))
def blend(wa, wb, mk, m):
    x = np.where(m, np.exp(wa * np.log(np.maximum(P, 1e-12)) + wb * np.log(1 / mk)), 0.0); return norm(x, m)
H1 = date < "2026-01-01"
for name, mk in (("the open", o), ("9am race morning", p9), ("the last price before the jump", jp)):
    m = good(mk); pb = norm(1 / bs, m); pm = norm(1 / mk, m); po = norm(P, m)
    print(f"\n## Market = {name}: {len(set(ri[m]))} races")
    grid = [(wa, wb) for wa in np.arange(0, 1.51, 0.05) for wb in np.arange(0, 1.51, 0.05) if wa + wb > 0]
    preds = np.full(len(ri), np.nan); wts = {}
    for fit, test in ((H1, ~H1), (~H1, H1)):
        fm, tm = m & fit, m & test
        if not tm.any() or not fm.any(): continue
        best = min(grid, key=lambda w: ll(blend(w[0], w[1], mk, fm), fm))
        bb = blend(best[0], best[1], mk, tm); preds[tm] = bb[tm]; wts["2026" if test is ~H1 or (test & ~H1).any() else "2025"] = best
    mm = m & np.isfinite(preds)
    print(f"weights fitted on the other half: {', '.join(f'{k}: ours {w[0]:.2f}, market {w[1]:.2f}' for k, w in wts.items())}")
    print("| price | winner log loss (lower is better) |\n|---|---|")
    for lab, p in (("BSP", pb), ("the market alone", pm), ("our model alone", po), ("the blend", preds)):
        print(f"| {lab} | {ll(p, mm):.4f} |")
    print("\n| back when BSP >= k x the blend | bets | won | BSP expected | at BSP ROI | 2025 | 2026 |\n|---|---|---|---|---|---|---|")
    rb = np.where(won, (bs - 1) * 0.92, -1.0)
    for k in (1.1, 1.2, 1.3, 1.5, 2.0):
        q = mm & (bs * preds >= k)
        cells = [f"{100 * rb[q & h].mean():+.1f}%" if (q & h).sum() >= 30 else "-" for h in (H1, ~H1)]
        print(f"| {k:g} | {q.sum()} | {won[q].sum()} | {(1 / bs[q]).sum():.0f} | {100 * rb[q].mean():+.1f}% | " + " | ".join(cells) + " |")
