"""Live scorecard, 15 Oct - 9 Nov 2026 (night of 10 Nov): the committed live files (live_join.npz from score_replay.py)
against BSP, the open and the winners: by week, by price band, and by how far we disagree with BSP.
    python3.13 live_scorecard.py   (replay folder)"""
import numpy as np
Z = np.load("ds/model_ds.npz", allow_pickle=True); LJ = np.load("live_join.npz")
ri = Z["race_idx"]; nR = len(Z["race_id"]); rdate = Z["date"].astype(str); date = rdate[ri]
bs = Z["bsp"].astype(float); op = Z["open"].astype(float); won = Z["finish"] == 1
def norm(x):
    ok = np.isfinite(x) & (x > 1); inv = np.where(ok, 1 / np.where(ok, x, 2), 0)
    return inv / np.maximum(np.bincount(ri, weights=inv, minlength=nR)[ri], 1e-12), np.bincount(ri, weights=~ok, minlength=nR) == 0
q, qf = norm(bs); mk, mf = norm(op); pm, pb = LJ["p_model"], LJ["p"]
have = np.isfinite(pm); rf = (np.bincount(ri, weights=~have, minlength=nR) == 0) & qf & (np.bincount(ri, weights=won, minlength=nR) == 1)
g = rf[ri]
def kl(p, m): return np.sum(np.where(q[m] > 0, q[m] * np.log(np.maximum(q[m], 1e-300) / np.maximum(p[m], 1e-12)), 0)) / len(np.unique(ri[m]))
def ll(p, m): return -np.mean(np.log(np.maximum(p[m & won], 1e-12)))
print(f"{int(rf.sum())} live races 15 Oct - 9 Nov where every runner that ran is in the committed file\n")
print("| week | races | our price KL | blended with open KL | open KL | log loss: ours | blended | open | BSP |\n|---|---|---|---|---|---|---|---|---|")
for lo, hi in (("2026-10-15", "2026-10-22"), ("2026-10-22", "2026-10-29"), ("2026-10-29", "2026-11-05"), ("2026-11-05", "2026-11-10"), ("2026-10-15", "2026-11-10")):
    m = g & (date >= lo) & (date < hi); mo = m & mf[ri]
    print(f"| {lo[5:]} to {hi[5:]} | {len(np.unique(ri[m]))} | {kl(pm, m):.4f} | {kl(pb, m):.4f} | {kl(mk, mo):.4f} | {ll(pm, m):.4f} | {ll(pb, m):.4f} | {ll(mk, mo):.4f} | {ll(q, m):.4f} |")
print("\nCalibration of the live betting price (blended), by its own price band: winners against the chance it gave")
print("| our price | runners | expected winners | actual | A/E | BSP expected |\n|---|---|---|---|---|---|")
pr = 1 / np.maximum(pb, 1e-9)
for lo, hi in ((1, 2.5), (2.5, 4), (4, 6), (6, 9), (9, 15), (15, 30), (30, 1e9)):
    m = g & (pr >= lo) & (pr < hi)
    print(f"| ${lo}-{'$%g' % hi if hi < 1e8 else 'up'} | {int(m.sum())} | {pb[m].sum():.1f} | {int(won[m].sum())} | {won[m].sum()/pb[m].sum():.2f} | {q[m].sum():.1f} |")
print("\nWhere we disagree with BSP (our price before the blend / BSP): who was right?")
print("| ours v BSP | runners | we expected | BSP expected | actual winners | A/E v ours | A/E v BSP |\n|---|---|---|---|---|---|---|")
ratio = q / np.maximum(pm, 1e-12)     # >1: BSP rates it higher than we do (we are too long)
for lab, lo, hi in (("we are 1.5x+ longer than BSP", 1.5, 1e9), ("1.2-1.5x longer", 1.2, 1.5), ("within 20%", 1 / 1.2, 1.2), ("1.2-1.5x shorter", 1 / 1.5, 1 / 1.2), ("we are 1.5x+ shorter than BSP", 0, 1 / 1.5)):
    m = g & (ratio >= lo) & (ratio < hi) & (q > 0)
    print(f"| {lab} | {int(m.sum())} | {pm[m].sum():.1f} | {q[m].sum():.1f} | {int(won[m].sum())} | {won[m].sum()/pm[m].sum():.2f} | {won[m].sum()/q[m].sum():.2f} |")
# value at the open on the live files: open >= 1.2 x the blended price, $1.60-$15
o = op; val = g & np.isfinite(o) & (o > 1) & (pr >= 1.6) & (pr <= 15) & (o >= 1.2 * pr) & (o < 3 * pr)
print(f"\nRunners the live blended price rated value at Form King's open (open >= 1.2x ours, ours $1.60-$15, under 3x): {int(val.sum())}; "
      f"won {int(won[val].sum())} (we expected {pb[val].sum():.1f}, BSP {q[val].sum():.1f}); flat 1u at the open {np.where(won[val], o[val]-1, -1).sum():+.1f}u "
      f"({100*np.where(won[val], o[val]-1, -1).mean():+.0f}%); beat BSP {100*np.mean(o[val] > bs[val]):.0f}%, median open/BSP {np.median(o[val]/bs[val]):.2f}")
