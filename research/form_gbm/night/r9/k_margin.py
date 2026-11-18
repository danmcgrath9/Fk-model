"""k_margin.py: how far over the fair price does a 9am price have to be? (18 Nov 2026)
a_model's 'ours + median + move' fair price, Victoria, test months Nov 2025 - Nov 2026. Each major's 9am price is put in
a band by price / fair, and bet to win the limit. If the fair price were fair, the 1.00-1.05 band would break even."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
FM = np.load(os.path.join(HERE, "fair_models.npy")); names = open(os.path.join(HERE, "fair_models.txt")).read().split("\n")
for mdl in ("ours + median + move", "LIVE 0.20 ours + 1.00 TAB", "market only (median majors)"):
    pa = FM[:, names.index(mdl)]; fa = np.where(pa > 0, 1 / np.maximum(pa, 1e-12), np.nan)
    e = (pa > 0) & ran & ~fs & (fa >= 1.6) & (fa <= 15) & (date >= "2025-11-01")
    r = B7 / fa[:, None]
    print(f"\n### {mdl}\n\n| price / fair | bookie bets | runners | winners | expected by the fair price | staked | profit | ROI | Mar-Jun 2026 | Jul-Nov 2026 |\n|---|---|---|---|---|---|---|---|---|---|")
    for a, b in ((0.90, 0.95), (0.95, 1.00), (1.00, 1.03), (1.03, 1.05), (1.05, 1.08), (1.08, 1.12), (1.12, 1.20), (1.20, 1.35), (1.35, 9)):
        hit = e[:, None] & np.isfinite(B7) & (r >= a) & (r < b)
        st = np.where(hit, lim[:, None] / np.maximum(B7 - 1, 1e-9), 0.0); pl = np.where(hit, np.where(won[:, None], (lim * (1 - DED))[:, None], -st), 0.0)
        ru = hit.any(1); h1 = (date >= "2026-03-01") & (date < "2026-07-01"); h2 = date >= "2026-07-01"
        print(f"| {a:.2f}-{b:.2f}x | {int(hit.sum())} | {int(ru.sum())} | {int((ru & won).sum())} | {pa[ru].sum():.0f} | ${st.sum():,.0f} | ${pl.sum():+,.0f} | {pl.sum() / max(st.sum(), 1):+.1%} | "
              f"{int(hit[h1].sum())} bets {pl[h1].sum() / max(st[h1].sum(), 1):+.0%} | {int(hit[h2].sum())} bets {pl[h2].sum() / max(st[h2].sum(), 1):+.0%} |")
