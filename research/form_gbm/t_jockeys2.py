"""Follow-up to t_jockeys.py: bets ridden by jockeys in the top third of our rolling wins-vs-market (jockey_ae, prior rides)
underperform in every price band in both samples. Fixed threshold (the holdout's top-third cut), stake variants."""
import numpy as np
exec(open("t_jockeys.py").read().split("bands = ")[0])
L0, _ = stakes(shade(p), hm); thr = float(np.nanquantile(ae[L0], 0.67)); thr_wp = float(np.nanquantile(wp[L0], 0.67))
print(f"A/E top-third cut {thr:.3f}; 12m win% top-third cut {thr_wp*100:.1f}%")
hiae = ae >= thr; topwp = wp >= thr_wp
for lab, PP, M_ in (("HOLDOUT", p, hm), ("BEFORE", po_, pre)):
    P_ = shade(PP); L_, S_ = stakes(P_, M_); print(f"\n== {lab}")
    for nm, mult in (("live", np.ones(len(op))), ("high-A/E jockey: skip", np.where(hiae, 0, 1.0)), ("high-A/E jockey: half stake", np.where(hiae, 0.5, 1.0)),
                     ("$10+ top-12m-win% jockey: x1.5", np.where(topwp & (op >= 10), 1.5, 1.0)),
                     ("half high-A/E + x1.5 $10+ top win%", np.where(hiae, 0.5, 1.0) * np.where(topwp & (op >= 10) & ~hiae, 1.5, 1.0))):
        S2 = np.minimum(S_ * mult, 5.0); L2 = L_ & (S2 > 0); n, inv, (a, b_, cc), dd = report(L2, S2)
        print(f"  {nm:36s} bets {n:5d} invested ${inv:>9,.0f} open ${a:>+9,.0f} {a/inv*100:+5.1f}% open-7% {b_/inv*100:+5.1f}% BSP {cc/inv*100:+5.1f}% DD ${dd:>6,.0f}")
