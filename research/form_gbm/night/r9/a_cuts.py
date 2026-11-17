"""a_cuts.py: where the 9am money is (18 Nov 2026). Test months Nov 2025 - Nov 2026, late scratchings handled
(r9/build.py). Fair prices from a_model.py's walk-forward fits. Bets to win the limit at each bookmaker's own 9am price."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
labels = open(os.path.join(HERE, "fair_models.txt")).read().split("\n"); FM = np.load(os.path.join(HERE, "fair_models.npy"))
fairp = lambda lab: np.where(FM[:, labels.index(lab)] > 0, 1 / np.maximum(FM[:, labels.index(lab)], 1e-12), np.nan)
LIVE, MEDB, MOVE = "LIVE 0.20 ours + 1.00 TAB", "0.20 ours + 1.00 median majors", "ours + median + move"
test = (FM[:, labels.index(MOVE)] > 0) & (month >= "2025-11")
okb = (FM[:, labels.index(LIVE)] > 0)

# 1. The market price the LIVE list reads: Form King's best price now across its bookmakers (scripts/scratchings.py, bestNow)
FK = ("tab", "sportsbet", "ladbrokes", "neds", "pointsbet", "tabtouch", "betdeluxe", "betnation", "noisy", "pulsebet", "surge", "unibet", "betr")
BF = np.column_stack([col9(k) for k in FK])
with np.errstate(all="ignore"):
    fk_best = np.nanmax(np.where(np.isfinite(BF), BF, -np.inf), 1); fk_best[~np.isfinite(fk_best)] = np.nan
    fk_avg = np.nanmean(BF, 1)
def blend(mkt, w=0.20):
    ok = okb & np.isfinite(mkt) & (mkt > 1)
    p = softmax_by_race(w * np.log(np.where(ok, P, 1.0)) - np.log(np.where(ok, mkt, 2.0)), ok)
    return np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan)
print("### 1. The market price inside the blend (0.20 ours + 1.00 market), bets with every major at 1.05x\n\n" + MONEY_HEAD)
for lab, mk in (("TAB's price (the rule as tested)", T9), ("median of the seven majors", MED7), ("AVERAGE of Form King's bookmakers", fk_avg),
                ("BEST of Form King's bookmakers (what the live list reads today)", fk_best)):
    hit, st, pl = bets(blend(mk), test, B7); print(money_row(lab, hit, st, pl, test))
fb = blend(fk_best); e = test & ran & ~fs & (fb >= 1.6) & (fb <= 15) & (fk_best >= 1.05 * fb)
st = np.where(e, lim / (fk_best - 1), 0); pl = np.where(e, np.where(won, lim * (1 - DED), -st), 0)
print(f"| the live list as it prints: one bet at the BEST price when it is 1.05x the blend | {int(e.sum())} | {int(e.sum())} | {int((e & won).sum())} | ${st.sum():,.0f} | ${pl.sum():+,.0f} | {pl.sum() / max(st.sum(), 1):+.1%} | |")

# 2. Threshold
print("\n### 2. The take threshold (price / fair price), every major\n\n| fair price from | " + " | ".join(f"{t:.2f}x" for t in (1.00, 1.03, 1.05, 1.08, 1.10, 1.15, 1.20)) + " |\n|---|" + "---|" * 7)
for lab in (LIVE, MEDB, MOVE):
    out = []
    for t in (1.00, 1.03, 1.05, 1.08, 1.10, 1.15, 1.20):
        hit, st, pl = bets(fairp(lab), test, B7, thr=t); out.append(f"{int(hit.sum())} bets ${pl.sum():+,.0f} {pl.sum() / max(st.sum(), 1):+.0%}")
    print(f"| {lab} | " + " | ".join(out) + " |")
print("\nby overlay band, fair price from '" + MOVE + "' (each bookie bet in its own band)\n| price / fair | bookie bets | winners | staked | profit | ROI |\n|---|---|---|---|---|---|")
fp = fairp(MOVE); e = test & ran & ~fs & (fp >= 1.6) & (fp <= 15)
ratio = B7 / fp[:, None]
for a, b_ in ((0.97, 1.0), (1.0, 1.03), (1.03, 1.05), (1.05, 1.08), (1.08, 1.12), (1.12, 1.2), (1.2, 9)):
    h = e[:, None] & np.isfinite(ratio) & (ratio >= a) & (ratio < b_)
    st = np.where(h, lim[:, None] / (B7 - 1), 0); pl = np.where(h, np.where(won[:, None], (lim * (1 - DED))[:, None], -st), 0)
    print(f"| {a:.2f}-{b_:.2f} | {int(h.sum())} | {int((h & won[:, None]).sum())} | ${st.sum():,.0f} | ${pl.sum():+,.0f} | {pl.sum() / max(st.sum(), 1):+.1%} |")

# 3. By bookmaker, every bookmaker Betwatch holds for most of the period
print("\n### 3. By bookmaker (fair price from '" + MOVE + "', 1.05x)\n\n| bookmaker | 9am prices held | bets | winners | staked | profit | ROI | its price / median major |\n|---|---|---|---|---|---|---|---|")
names = sorted({k for d in bk9 if d for k in d}, key=lambda k: -sum(1 for d in bk9 if d and k in d))
rows = []
for k in names:
    c = col9(k); held = int(np.isfinite(c[test]).sum())
    if held < 15000: continue
    hit, st, pl = bets(fp, test, c[:, None]); m = test & np.isfinite(c) & (MED7 > 1.6) & (MED7 < 15)
    rows.append((pl.sum(), f"| {k} | {held} | {int(hit.sum())} | {int((hit[:, 0] & won).sum())} | ${st.sum():,.0f} | ${pl.sum():+,.0f} | {pl.sum() / max(st.sum(), 1):+.0%} | {np.nanmean(c[m] / MED7[m]):.3f} |"))
for _, r in sorted(rows, key=lambda x: -x[0]): print(r)

# 4. Fair price band, track, how many majors are over
print("\n### 4. Cuts of '" + MOVE + "' at 1.05x, every major\n\n" + MONEY_HEAD)
hit, st, pl = bets(fp, test, B7, lo=1.01, hi=1000)
for a, b_ in ((1.01, 1.6), (1.6, 3), (3, 5), (5, 8), (8, 15), (15, 30), (30, 1000)):
    print(money_row(f"fair price ${a:g}-${b_:g}", hit, st, pl, test & (fp >= a) & (fp < b_)))
hit, st, pl = bets(fp, test, B7)
print(money_row("metro", hit, st, pl, test & metro)); print(money_row("country and provincial", hit, st, pl, test & ~metro))
k = hit.sum(1)
for a, b_, lab in ((1, 1, "one major over"), (2, 3, "2-3 majors over"), (4, 7, "4+ majors over")):
    print(money_row(lab, hit, st, pl, test & (k >= a) & (k <= b_)))
ov = 1 / P / MED7       # our price / the market
for a, b_, lab in ((0, 0.8, "our price under 0.8x the median"), (0.8, 1.0, "0.8-1.0x"), (1.0, 1.25, "1.0-1.25x"), (1.25, 99, "our price over 1.25x the median")):
    print(money_row(lab, hit, st, pl, test & (ov >= a) & (ov < b_)))
