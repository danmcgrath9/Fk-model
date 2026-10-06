"""Do our value bets on horses that usually settle back lose? (6 Oct 2026, from t_place.py, where back-settling
live bets were the weak spot at the open, at BSP and for places.) The finding came from the holdout, so it is
tested (a) on both halves of the holdout, (b) over several cut-offs, and (c) on the races BEFORE the holdout
(Jan-May), priced with the stage-1 out-of-fold chances, which played no part in finding it."""
import numpy as np
exec(open("t_backtest_full.py").read().split("rd=dates")[0])
ss=X[:,c["raw_settle_share"]]
pw_o=np.where(won,op-1,-1.0); pw_b=np.where(won,(bsp-1)*0.92,-1.0)
def bets(pp,mask):
    """The live rules (t_backtest_full) with chance pp on the races in mask."""
    mkt_=D["mkt"].astype(float)
    okr_=np.bincount(ri,weights=(~np.isfinite(mkt_)|~np.isfinite(pp)).astype(float),minlength=nR)==0
    cp=mask&okr_[ri]&np.isfinite(bsp)&np.isfinite(op)&(op>1)&(bsp>1)&(1/pp<50)&(op<3/pp)
    vv=pp*op-1
    lv=cp&(vv>=0.2)&~blockset&(1/pp>=2)&(1/pp<=15)
    st=np.where(lv,np.minimum(4.0,75*np.clip(((pp/op)**0.5*op-1)/(op-1),0,None)),0.0)
    return lv,st
def roi(m,st,po): return (st*po)[m].sum()/max(st[m].sum(),1e-9)*100
def show(lab,lv,st,parts):
    print(f"\n== {lab}: {lv.sum()} bets")
    for nm,pm in parts:
        print(f"  {nm}")
        for lo,hi,sl in ((0,.3,"forward (leads/on pace)"),(.3,.65,"midfield"),(.65,1.01,"back"),(-1,9,"ALL")):
            m=lv&pm&(((ss>=lo)&(ss<hi)) if lo>=0 else True)
            if lo<0: m=lv&pm
            print(f"    {sl:24s} bets {m.sum():4d}  open ROI {roi(m,st,pw_o):+6.1f}%  BSP ROI {roi(m,st,pw_b):+6.1f}%  strike {won[m].mean()*100:4.1f}%  wins/expected {won[m].sum()/max(p_[m].sum(),1e-9):.2f}")
p_=p; lv,st=bets(p,hm)
show("HOLDOUT (stage 2, where it was found)",lv,st,[("older half",~newer),("newer half",newer)])
print("\n  cut-offs on the holdout (open ROI / BSP ROI of the bets at or behind the cut):")
for cut in (.5,.6,.65,.7,.8):
    m=lv&(ss>=cut); k=lv&~(ss>=cut)
    print(f"    settle >= {cut:.2f}: {m.sum():4d} bets  open {roi(m,st,pw_o):+6.1f}%  BSP {roi(m,st,pw_b):+6.1f}%   | the rest: open {roi(k,st,pw_o):+6.1f}%  BSP {roi(k,st,pw_b):+6.1f}%")
po_=np.load("p_oof_blend9.npy"); pre=~hm&np.isfinite(po_)
p_=po_; lv2,st2=bets(po_,pre)
first=np.isin(ri,np.where(dates<"2026-03-20")[0])
show("BEFORE THE HOLDOUT (stage-1 out-of-fold, independent)",lv2,st2,[("Jan to mid-Mar",first),("mid-Mar to May",~first)])
print("\n  what the plan would have done with the back-settlers blocked or halved:")
for lab,L_,S_ in (("holdout",lv,st),("before the holdout",lv2,st2)):
    for nm,mult in (("as is",1.0),("halve back",0.5),("block back",0.0)):
        s2=np.where(ss>=.65,S_*mult,S_)
        print(f"    {lab:20s} {nm:11s} invested ${100*s2[L_].sum():>9,.0f}  open profit ${100*(s2*pw_o)[L_].sum():>+9,.0f} ({roi(L_,s2,pw_o):+5.1f}%)  BSP profit ${100*(s2*pw_b)[L_].sum():>+8,.0f} ({roi(L_,s2,pw_b):+5.1f}%)")
print("\n  softer: shade our chance for back-settlers (the model gives them ~15-30% too many wins), then the same rules:")
for lab,P_,M_ in (("holdout",p,hm),("before the holdout",po_,pre)):
    for k in (1.0,0.9,0.85,0.8):
        pa=np.where(ss>=.65,P_*k,P_)
        # renormalise per race so the field still adds to 1
        tot=np.bincount(ri,weights=np.nan_to_num(pa),minlength=nR)[ri]; pa=pa/np.where(tot>0,tot,1)
        L_,S_=bets(pa,M_)
        print(f"    {lab:20s} back x{k:.2f}: bets {L_.sum():4d}  invested ${100*S_[L_].sum():>9,.0f}  open profit ${100*(S_*pw_o)[L_].sum():>+9,.0f} ({roi(L_,S_,pw_o):+5.1f}%)  BSP profit ${100*(S_*pw_b)[L_].sum():>+8,.0f} ({roi(L_,S_,pw_b):+5.1f}%)")
