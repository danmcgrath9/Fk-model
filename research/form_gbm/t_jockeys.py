"""Jockeys by price band (founder, 9 Oct 2026: 'backtesting on jockeys sub $8 / $4 / $10+'). The live plan's bets
(staking as live: stake_rule, x2 only ride, x1.5 field<=8, 8u ceiling x5/8) split by opening price band and by the
jockey's quality measured BEFORE the race: Form King's 12-month win % (national, pre-race), our rolling wins-vs-market
(VIC, prior rides only), and apprentice. Both samples, open ROI and BSP ROI."""
import numpy as np
exec(open("t_batch2.py").read().split("\nV=[")[0])
F9 = np.load("F9.npy", mmap_mode="r"); nm9 = open("F9_names.txt").read().split("\n"); col9 = lambda n: np.asarray(F9[:, nm9.index(n)], float)
assert F9.shape[0] == len(op), (F9.shape, len(op))
wp = col9("jockeyForm_lastTwelveMonthWinPercentage"); ae = col9("jockey_ae"); appr = col9("apprenticeJockey")
wp = np.where(wp > 1.5, wp / 100, wp)   # percent or fraction
def stakes(P_, M_):
    L_, S_ = var(P_, M_, mo=2, ms=1.5, recap=8); return L_, S_ * 5 / 8
bands = (("open under $4", op < 4), ("$4-$8", (op >= 4) & (op < 8)), ("$8-$10", (op >= 8) & (op < 10)), ("$10+", op >= 10))
for lab, PP, M_ in (("HOLDOUT (6 May - 4 Oct)", p, hm), ("BEFORE THE HOLDOUT (Jan - May)", po_, pre)):
    P_ = shade(PP); L_, S_ = stakes(P_, M_)
    q = np.nanquantile(wp[L_], [0.33, 0.67]); qa = np.nanquantile(ae[L_], [0.33, 0.67])
    tiers = (("jockey 12m win% top third", wp >= q[1]), ("jockey 12m win% middle", (wp >= q[0]) & (wp < q[1])), ("jockey 12m win% bottom third", wp < q[0]),
             ("jockey beats market (A/E top third)", ae >= qa[1]), ("jockey A/E bottom third", ae < qa[0]), ("apprentice", appr == 1))
    print(f"\n== {lab}: {L_.sum()} bets, open ROI {roi(L_, S_, pw_o):+.1f}%  (12m win% thirds at {q[0]*100:.0f}% / {q[1]*100:.0f}%)")
    print(f"  {'band':14s} {'jockey':38s} {'bets':>5s} {'strike':>7s} {'won/our':>8s} {'open ROI':>9s} {'BSP ROI':>8s}")
    for bn, bm in bands:
        m0 = L_ & bm
        print(f"  {bn:14s} {'ALL':38s} {m0.sum():5d} {won[m0].mean()*100:6.1f}% {won[m0].sum()/max(P_[m0].sum(),1e-9):8.2f} {roi(m0,S_,pw_o):+8.1f}% {roi(m0,S_,pw_b):+7.1f}%")
        for tn, tm in tiers:
            m = m0 & tm
            if m.sum() < 15: print(f"  {'':14s} {tn:38s} {m.sum():5d}  (too few)"); continue
            print(f"  {'':14s} {tn:38s} {m.sum():5d} {won[m].mean()*100:6.1f}% {won[m].sum()/max(P_[m].sum(),1e-9):8.2f} {roi(m,S_,pw_o):+8.1f}% {roi(m,S_,pw_b):+7.1f}%")
