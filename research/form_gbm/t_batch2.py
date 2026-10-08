"""Combinations of the variants that raised BOTH profit and ROI in both samples (t_batch.py), 8 Oct 2026."""
import numpy as np
exec(open("t_batch.py").read().split("V=[")[0])
def var(P_,M_,mo=1,ms=1,cap=4.0,recap=None):
    L_,S_=plan(P_,M_,cap=cap)
    S_=np.where(L_&(onlyride==1),S_*mo,S_); S_=np.where(L_&(field<=8),S_*ms,S_)
    if recap: S_=np.minimum(S_,recap)
    return L_,S_
V=[("LIVE PLAN",{}),("only-ride x2",{"mo":2}),("only-ride x2, max 6u",{"mo":2,"recap":6}),("field<=8 x1.5",{"ms":1.5}),
   ("cap 6u",{"cap":6.0}),("only-ride x2 + field<=8 x1.5",{"mo":2,"ms":1.5}),("only-ride x2 + field<=8 x1.5, max 6u",{"mo":2,"ms":1.5,"recap":6}),
   ("only-ride x2 + field<=8 x1.5 + cap 6u",{"mo":2,"ms":1.5,"cap":6.0}),("only-ride x2 + field<=8 x1.5 + cap 6u, max 8u",{"mo":2,"ms":1.5,"cap":6.0,"recap":8})]
for lab,PP,M_ in (("HOLDOUT (6 May - 4 Oct)",p,hm),("BEFORE THE HOLDOUT (Jan - May)",po_,pre)):
    P_=shade(PP); print(f"\n== {lab}")
    for nm,kw in V:
        L_,S_=var(P_,M_,**kw); n,inv,(a,b,cc),dd=report(L_,S_)
        print(f"  {nm:46s} invested ${inv:>9,.0f}  open ${a:>+9,.0f} {a/inv*100:+5.1f}%  open-7% {b/inv*100:+5.1f}%  BSP ${cc:>+8,.0f} {cc/inv*100:+5.1f}%  DD ${dd:>7,.0f}  max stake {S_.max():.1f}u")
