"""a_calib.py: is the move model's chance honest on the runners it bets? (18 Nov 2026) Winners against the model's
expected winners on the 9am list, by grade and by fair-price band, and against the market's own (median) chance."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
with np.errstate(all="ignore"):
    ALL = [np.array([v for v in (d or {}).values() if v > 1.011], float) for d in bk9]
    BEST = np.array([a.max() if len(a) >= 6 else np.nan for a in ALL])
pm = np.load(os.path.join(HERE, "fair_move.npy")); ok = pm > 0; test = ok & (month >= "2025-11")
pb = softmax_by_race(0.2 * np.log(np.where(ok, P, 1.0)) - np.log(np.where(ok & np.isfinite(BEST), BEST, 2.0)), ok & np.isfinite(BEST))
pk = softmax_by_race(-np.log(np.where(ok, MED7, 2.0)), ok)                        # the market's own chance (median, margin taken out)
f = lambda p: np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan)
hA, _, _ = bets(f(pb), test, B7); hB, _, _ = bets(f(pm), test, B7)
a, b1, b2 = (hA & hB).any(1), hA.any(1) & ~(hA & hB).any(1) & ~hB.any(1), hB.any(1) & ~hA.any(1)
print("| runners | n | won | the move model expected | the live blend expected | the market expected | our model alone expected |\n|---|---|---|---|---|---|---|")
for lab, m in (("A: both lists", a), ("B1: live list only", b1), ("B2: move model only", b2), ("every listed runner", hA.any(1) | hB.any(1)),
               ("not listed, fair $1.60-$15", test & ran & ~fs & ~(hA.any(1) | hB.any(1)) & (f(pm) >= 1.6) & (f(pm) <= 15))):
    w_ = (1 - DED[m])  # a winner in a race with a late scratching still won
    print(f"| {lab} | {int(m.sum())} | {int(won[m].sum())} | {pm[m].sum():.1f} | {pb[m].sum():.1f} | {pk[m].sum():.1f} | {P[m].sum():.1f} |")
