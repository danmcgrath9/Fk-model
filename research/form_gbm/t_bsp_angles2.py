"""Follow-up to t_bsp_angles.py: size the two angles that held in both halves. (1) The back-at-open / lay-at-BSP hedge:
liability per bet, units a month, worst month. (2) The widened roughie lay (ours/BSP 1.6+): $8-$30 and $8-$50 against
the $15-$30 rule, ROI on stake and on liability, units a month, worst month. $100 a unit."""
import numpy as np, collections
exec(open("t_bsp_angles.py").read().split("# A. back at the open")[0])
UNIT = 100
def monthly(idx, pl, liab, title):
    g = collections.OrderedDict()
    for k, p, l in sorted(zip(date[idx], pl, liab)):
        a = g.setdefault(k[:7], [0, 0.0, 0.0]); a[0] += 1; a[1] += p; a[2] += l
    print(f"\n{title}\n| month | bets | profit (u) | profit ($) | ROI on stake | liability ($) | ROI on liability |\n|---|---|---|---|---|---|---|")
    for k, (n, p, l) in g.items(): print(f"| {k} | {n} | {p:+.1f} | ${p*UNIT:+,.0f} | {100*p/n:+.0f}% | ${l*UNIT:,.0f} | {100*p/l:+.1f}% |")
    n, p, l = len(idx), pl.sum(), liab.sum()
    print(f"| all | {n} | {p:+.1f} | ${p*UNIT:+,.0f} | {100*p/n:+.0f}% | ${l*UNIT:,.0f} | {100*p/l:+.1f}% |")
    vals = [v[1] for v in g.values()]; print(f"worst month {min(vals):+.1f}u, best {max(vals):+.1f}u, losing months {sum(v<0 for v in vals)} of {len(vals)}")

# 1. hedge on plan bets
idx = np.where(plan)[0]; oe = 1 + (o[idx] - 1) * (1 - DED); L = oe / (bs[idx] - COMM); hedged = -1 + L * (1 - COMM)
monthly(idx, hedged, L * (bs[idx] - 1), "## Hedge: back 1u at the open, lay at BSP for a level result (plan bets); liability = the lay's")
print(f"lay stake per 1u backed: median {np.median(L):.2f}u, 90th pct {np.percentile(L,90):.2f}u; liability per bet: median {np.median(L*(bs[idx]-1)):.1f}u, 90th pct {np.percentile(L*(bs[idx]-1),90):.1f}u")
print(f"share of the open edge kept: hedged {100*hedged.mean():+.1f}% of {100*back_open(plan).mean():+.1f}% unhedged; bets that lock a profit {(hedged>0).mean():.0%}")
# unhedged swing for comparison
po = back_open(plan); print(f"unhedged: worst single bet {po.min():+.1f}u, std per bet {po.std():.2f}u; hedged: worst {hedged.min():+.2f}u, std {hedged.std():.2f}u")

# 2. widened lay
for lo_, hi_, nm in ((15, 30, "$15-$30 (the rule)"), (8, 30, "$8-$30"), (8, 50, "$8-$50"), (8, 12, "$8-$12 only"), (30, 50, "$30-$50 only")):
    g = m & (ratio >= 1.6) & (bs >= lo_) & (bs < hi_); idx = np.where(g)[0]
    monthly(idx, lay_pl(g), bs[idx] - 1, f"## Lay 1u at BSP, ours/BSP 1.6+, BSP {nm}")
