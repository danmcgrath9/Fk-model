import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
n7 = np.isfinite(B7).sum(1)
with np.errstate(all="ignore"):
    mx = np.nanmax(np.where(np.isfinite(B7), B7, -np.inf), 1); mx[~np.isfinite(mx)] = np.nan
have = np.isfinite(T9)
print("| month | dataset runners | TAB 9am | 4+ majors | majors a runner | best major / median (mean) | share with best >= 1.05x median | share >= 1.10x | TAB/median mean | TAB is the best |")
print("|---|---|---|---|---|---|---|---|---|---|")
for mo in sorted(set(month)):
    m = month == mo; h = m & have & (n7 >= 4) & (MED7 > 1.6) & (MED7 < 15)
    r = mx[h] / MED7[h]
    print(f"| {mo} | {int(m.sum())} | {int((m & have).sum())} | {int((m & (n7 >= 4)).sum())} | {n7[m & have].mean():.1f} | {r.mean():.3f} | {(r >= 1.05).mean():.0%} | {(r >= 1.10).mean():.0%} | "
          f"{np.nanmean(T9[h] / MED7[h]):.3f} | {(T9[h] >= mx[h] - 1e-9).mean():.0%} |")
print("\nby bookmaker, price / median of the majors (runners with median $1.60-$15): mean ratio, share at 1.05x+")
for j, k in enumerate(MAJORS):
    out = []
    for a, b_, lab in PERIODS:
        m = (date >= a) & (date < b_) & np.isfinite(B7[:, j]) & (n7 >= 4) & (MED7 > 1.6) & (MED7 < 15)
        r = B7[m, j] / MED7[m]; out.append(f"{lab}: {r.mean():.3f}, {(r >= 1.05).mean():.0%}")
    print(f"- {k}: " + "; ".join(out))
