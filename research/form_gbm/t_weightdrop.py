"""The weight-down rule (no bet when 2kg+ lighter than last start), split by speed-map habit (7 Oct 2026, founder:
'what about dropping weight and being on speed?'). The bets the rule blocks, settled as if taken, holdout (stage 2)
and before the holdout (stage-1 out of fold), at the open and BSP less 8%. Shade for back-settlers applied as live."""
import numpy as np
exec(open("t_backsettle.py").read().split("p_=p; lv,st=bets(p,hm)")[0])
wd=X[:,c["weight"]]-ld(wt)
block_nowd=fs|fsb|fu_block|bounce|(secup&(op>8))
def bets2(pp,mask,blk):
    mkt_=D["mkt"].astype(float)
    okr_=np.bincount(ri,weights=(~np.isfinite(mkt_)|~np.isfinite(pp)).astype(float),minlength=nR)==0
    cp=mask&okr_[ri]&np.isfinite(bsp)&np.isfinite(op)&(op>1)&(bsp>1)&(1/pp<50)&(op<3/pp)
    lv=cp&(pp*op-1>=0.2)&~blk&(1/pp>=1.6)&(1/pp<=15)
    return lv,np.where(lv,np.minimum(4.0,75*np.clip(((pp/op)**0.5*op-1)/(op-1),0,None)),0.0)
def shade(P_):
    pa=np.where(ss>=.65,P_*0.85,P_); tot=np.bincount(ri,weights=np.nan_to_num(pa),minlength=nR)[ri]; return pa/np.where(tot>0,tot,1)
po_=np.load("p_oof_blend9.npy"); pre=~hm&np.isfinite(po_)
for lab,P_,M_ in (("HOLDOUT",shade(p),hm),("BEFORE THE HOLDOUT",shade(po_),pre)):
    L_,S_=bets2(P_,M_,block_nowd)
    print(f"\n== {lab}: value bets ignoring the weight rule {L_.sum()}")
    for nm,m in (("not dropping 2kg (bet now)",~(wd<=-2)),("DROPPING 2kg+ (blocked now)",wd<=-2)):
        mm=L_&m; print(f"  {nm:30s} bets {mm.sum():4d}  open ROI {roi(mm,S_,pw_o):+6.1f}%  BSP ROI {roi(mm,S_,pw_b):+6.1f}%  strike {won[mm].mean()*100:4.1f}%  wins/expected {won[mm].sum()/max(P_[mm].sum(),1e-9):.2f}")
    print("  the dropping-2kg+ bets, by speed-map habit:")
    for lo,hi,sl in ((0,.3,"forward (leads / on pace)"),(.3,.65,"midfield"),(.65,1.01,"back")):
        mm=L_&(wd<=-2)&(ss>=lo)&(ss<hi)
        print(f"    {sl:26s} bets {mm.sum():4d}  open ROI {roi(mm,S_,pw_o):+6.1f}%  BSP ROI {roi(mm,S_,pw_b):+6.1f}%  strike {won[mm].mean()*100 if mm.sum() else 0:4.1f}%  wins/expected {won[mm].sum()/max(P_[mm].sum(),1e-9):.2f}")
    print("  by how much weight dropped:")
    for lo,hi in ((-2,-3),(-3,-4),(-4,-99)):
        mm=L_&(wd<=lo)&(wd>hi)
        print(f"    {abs(lo)}-{abs(hi) if hi>-99 else '+'}kg lighter       bets {mm.sum():4d}  open ROI {roi(mm,S_,pw_o):+6.1f}%  BSP ROI {roi(mm,S_,pw_b):+6.1f}%")
print("\n  the plan with and without the weight rule ($100 a unit):")
for lab,P_,M_ in (("holdout",shade(p),hm),("before the holdout",shade(po_),pre)):
    for nm,blk in (("with the rule",block_nowd|(wd<=-2)),("without it",block_nowd)):
        L_,S_=bets2(P_,M_,blk)
        print(f"    {lab:20s} {nm:14s} bets {L_.sum():4d}  open profit ${100*(S_*pw_o)[L_].sum():>+9,.0f} ({roi(L_,S_,pw_o):+5.1f}%)  BSP profit ${100*(S_*pw_b)[L_].sum():>+8,.0f} ({roi(L_,S_,pw_b):+5.1f}%)")
