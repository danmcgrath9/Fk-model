"""Batch of plan variants, 8 Oct 2026 (founder: 'do all the tests you want'). Each one against the live plan, both
samples, profit at the open, open less 7% deductions, BSP less 8%, worst drawdown at the open."""
import numpy as np
exec(open("t_edges.py").read().split("for lab,P_,M_ in")[0])
def plan(pp,mask,thr=0.2,k=75,cap=4.0,lo=1.6,hi=15):
    mkt_=D["mkt"].astype(float)
    okr_=np.bincount(ri,weights=(~np.isfinite(mkt_)|~np.isfinite(pp)).astype(float),minlength=nR)==0
    cp=mask&okr_[ri]&np.isfinite(bsp)&np.isfinite(op)&(op>1)&(bsp>1)&(1/pp<50)&(op<3/pp)
    lv=cp&(pp*op-1>=thr)&~block_nowd&(1/pp>=lo)&(1/pp<=hi)
    return lv,np.where(lv,np.minimum(cap,k*np.clip(((pp/op)**0.5*op-1)/(op-1),0,None)),0.0)
rd=dates[ri].astype(str)
def report(L_,S_):
    idx=np.where(L_)[0]; o=idx[np.argsort(rd[idx],kind="stable")]; inv=100*S_[L_].sum(); out=[]
    for pw in (pw_o,np.where(won,op*0.93-1,-1.0),pw_b):
        pr=100*(S_*pw)[o]; out.append(pr.sum())
    cum=np.cumsum(100*(S_*pw_o)[o]); dd=(np.maximum.accumulate(np.concatenate([[0],cum]))[1:]-cum).max()
    return L_.sum(),inv,out,dd
V=[("LIVE PLAN",{},None),
 ("only-ride stake x1.5",{},("onlyride",1.5)),("only-ride stake x2",{},("onlyride",2.0)),
 ("field<=8 stake x1.5",{},("small",1.5)),
 ("barrier 1-4 stake x0.5",{},("inside",0.5)),
 ("value 15c+",{"thr":0.15},None),("value 25c+",{"thr":0.25},None),("value 30c+",{"thr":0.30},None),("value 40c+",{"thr":0.40},None),
 ("Kelly x50",{"k":50},None),("Kelly x100",{"k":100},None),
 ("cap 3u",{"cap":3.0},None),("cap 6u",{"cap":6.0},None),
 ("our price up to $20",{"hi":20},None),("our price up to $10",{"hi":10},None),
 ("only-ride x1.5 + field<=8 x1.5",{},("both",1.5))]
for lab,PP,M_ in (("HOLDOUT (6 May - 4 Oct)",p,hm),("BEFORE THE HOLDOUT (Jan - May)",po_,pre)):
    P_=shade(PP); print(f"\n== {lab}")
    print(f"  {'variant':32s} {'bets':>5s} {'invested':>10s} {'open':>18s} {'open-7%':>18s} {'BSP-8%':>18s} {'worst DD':>9s}")
    for nm,kw,mult in V:
        L_,S_=plan(P_,M_,**kw)
        if mult:
            w,f=mult; m={"onlyride":onlyride==1,"small":field<=8,"inside":bar<=4,"both":(onlyride==1)|(field<=8)}[w]
            S_=np.where(L_&m,S_*f,S_)
        n,inv,(a,b,cc),dd=report(L_,S_)
        print(f"  {nm:32s} {n:5d} ${inv:>9,.0f} ${a:>+9,.0f} {a/inv*100:+5.1f}% ${b:>+9,.0f} {b/inv*100:+5.1f}% ${cc:>+9,.0f} {cc/inv*100:+5.1f}% ${dd:>8,.0f}")
