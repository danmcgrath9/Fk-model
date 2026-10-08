"""Adjustments suggested by t_edges.py (8 Oct 2026): the jockey's only ride at the meeting wins 1.21-1.22x our chance
in both samples; barriers 1-4 win 0.82-0.87x. Each factor applied to our chance (on top of the back-settler shade),
race renormalised, same live rules, both samples."""
import numpy as np
exec(open("t_edges.py").read().split("for lab,P_,M_ in")[0])
def adj(P_,ko,kb):
    pa=np.where(ss>=.65,P_*0.85,P_); pa=np.where(onlyride==1,pa*ko,pa); pa=np.where(bar<=4,pa*kb,pa)
    tot=np.bincount(ri,weights=np.nan_to_num(pa),minlength=nR)[ri]; return pa/np.where(tot>0,tot,1)
for lab,PP,M_ in (("HOLDOUT",p,hm),("BEFORE THE HOLDOUT",po_,pre)):
    print(f"\n== {lab}")
    for ko,kb in ((1,1),(1.1,1),(1.2,1),(1.3,1),(1,0.9),(1,0.85),(1.2,0.9)):
        P_=adj(PP,ko,kb); L_,S_=bets2(P_,M_,block_nowd); inv=100*S_[L_].sum()
        po=100*(S_*pw_o)[L_].sum(); pb=100*(S_*pw_b)[L_].sum()
        print(f"  only-ride x{ko:<4} barrier1-4 x{kb:<5} bets {L_.sum():5d}  open profit ${po:>+9,.0f} ({po/inv*100:+5.1f}%)  BSP profit ${pb:>+9,.0f} ({pb/inv*100:+5.1f}%)")
