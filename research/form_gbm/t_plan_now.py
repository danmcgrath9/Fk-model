"""Backtest of the plan as it stands 7 Oct 2026: live rules, back-settler shade x0.85, weight rule removed.
Settled at the open, at the open less an average 7% deduction (real TAB deductions so far: Pakenham 16c and 4c,
Geelong 7, 0, 4, 5, 13c), and at BSP less 8%."""
import numpy as np
exec(open("t_weightdrop.py").read().split("po_=np.load")[0])
po_=np.load("p_oof_blend9.npy"); pre=~hm&np.isfinite(po_)
for lab,P_,M_ in (("HOLDOUT (6 May - 4 Oct, the model never trained on it)",shade(p),hm),("BEFORE THE HOLDOUT (Jan - May, stage-1 out of fold)",shade(po_),pre)):
    L_,S_=bets2(P_,M_,block_nowd); idx=np.where(L_)[0]
    rd=dates[ri].astype(str); o=idx[np.argsort(rd[idx],kind="stable")]
    pwd=np.where(won,op*0.93-1,-1.0)
    inv=100*S_[L_].sum(); meets=len(np.unique(np.char.add(rd[L_],D["track"][ri][L_].astype(str))))
    allm=len(np.unique(np.char.add(rd[M_],D["track"][ri][M_].astype(str))))
    print(f"\n== {lab}")
    print(f"  bets {L_.sum()}  winners {won[L_].sum()} ({won[L_].mean()*100:.1f}%)  avg price ${op[L_].mean():.2f}  avg stake {S_[L_].mean():.2f}u  meetings {allm} ({L_.sum()/allm:.1f} bets a meeting)  invested ${inv:,.0f}")
    for nm,pw in (("at the open",pw_o),("open less 7% deductions",pwd),("at BSP less 8%",pw_b)):
        pr=100*(S_*pw)[o]; cum=np.cumsum(pr); dd=(np.maximum.accumulate(np.concatenate([[0],cum]))[1:]-cum).max()
        print(f"  {nm:24s} profit ${pr.sum():>+9,.0f}  ROI {pr.sum()/inv*100:+6.1f}%  worst drawdown ${dd:,.0f}")
    run=best=0
    for k in o: run=0 if won[k] else run+1; best=max(best,run)
    clv=(bsp[L_]<op[L_]).mean()
    print(f"  longest losing run {best}  |  shortened from our price to BSP: {clv*100:.0f}% of bets")
