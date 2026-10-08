"""Where the edge is: the live plan's bets split by segment, both samples, at the open and BSP less 8% (8 Oct 2026,
founder: 'back testing our model to market to find edges and what's going on'). Plus the model-vs-market check on
EVERY runner: when we disagree with the opening price, who is right."""
import numpy as np
exec(open("t_weightdrop.py").read().split("po_=np.load")[0])
po_=np.load("p_oof_blend9.npy"); pre=~hm&np.isfinite(po_)
col=lambda n: X[:,c[n]] if n in c else np.full(len(op),np.nan)
trk=D["track"][ri].astype(str)
METRO={"Flemington","Caulfield","Caulfield Heath","Moonee Valley","Sandown Hillside","Sandown Lakeside"}
ismetro=np.isin(trk,list(METRO)); field=D["field"][ri].astype(float); dist=D["distance"][ri].astype(float)
lws=D["lws"][ri].astype(float); onlyride=col("jockeysOnlyRideAtMeeting"); prep=col("raw_run_in_prep"); bar=col("raw_barrier")
# market rank at the open within the race
rk=np.full(len(op),99)
for r in np.unique(ri):
    idx=np.where((ri==r)&np.isfinite(op)&(op>1))[0]
    if len(idx): rk[idx[np.argsort(op[idx])]]=np.arange(1,len(idx)+1)
segs=[("market rank at open: favourite",rk==1),("market rank 2-3",(rk>=2)&(rk<=3)),("market rank 4+",rk>=4),
 ("open under $4",op<4),("open $4-$8",(op>=4)&(op<8)),("open $8-$15",(op>=8)&(op<15)),("open $15-$30",(op>=15)&(op<30)),("open $30+",op>=30),
 ("metro track",ismetro),("provincial/country",~ismetro),
 ("field 8 or fewer",field<=8),("field 9-12",(field>=9)&(field<=12)),("field 13+",field>=13),
 ("sprint under 1200m",dist<1200),("1200-1599m",(dist>=1200)&(dist<1600)),("1600m+",dist>=1600),
 ("class (LWS) under 75",lws<75),("LWS 75-85",(lws>=75)&(lws<85)),("LWS 85+",lws>=85),
 ("first-up",prep==1),("second-up",prep==2),("third-up+",prep>=3),
 ("barrier 1-4",bar<=4),("barrier 5-9",(bar>=5)&(bar<=9)),("barrier 10+",bar>=10),
 ("speed: leads/on pace",ss<0.3),("speed: midfield",(ss>=0.3)&(ss<0.65)),("speed: back (shaded)",ss>=0.65),
 ("jockey's only ride at the meeting",onlyride==1),("jockey has other rides",onlyride==0),
 ("SHORTENED open to BSP",bsp<op),("DRIFTED open to BSP",bsp>=op)]
for lab,P_,M_ in (("HOLDOUT (6 May - 4 Oct)",shade(p),hm),("BEFORE THE HOLDOUT (Jan - May)",shade(po_),pre)):
    L_,S_=bets2(P_,M_,block_nowd)
    print(f"\n== {lab}: {L_.sum()} bets, open ROI {roi(L_,S_,pw_o):+.1f}%, BSP ROI {roi(L_,S_,pw_b):+.1f}%")
    print(f"  {'segment':36s} {'bets':>5s} {'strike':>7s} {'won/our%':>9s} {'open ROI':>9s} {'BSP ROI':>8s}")
    for nm,m in segs:
        mm=L_&m
        if mm.sum()<15: print(f"  {nm:36s} {mm.sum():5d}  (too few)"); continue
        print(f"  {nm:36s} {mm.sum():5d} {won[mm].mean()*100:6.1f}% {won[mm].sum()/P_[mm].sum():9.2f} {roi(mm,S_,pw_o):+8.1f}% {roi(mm,S_,pw_b):+7.1f}%")
    # every runner: model vs opening market
    ok=M_&np.isfinite(op)&(op>1)&np.isfinite(P_)
    mk=1/op; mtot=np.bincount(ri,weights=np.where(ok,mk,0),minlength=nR)[ri]; mkn=np.where(mtot>0,mk/mtot,np.nan)
    print("  every runner, our chance vs the opening market's (margin removed): who is right when we disagree")
    print(f"  {'our chance / market chance':28s} {'runners':>8s} {'won':>6s} {'we said':>8s} {'mkt said':>9s} {'flat 1u at open':>16s}")
    ratio=P_/mkn
    for lo,hi in ((0,0.6),(0.6,0.8),(0.8,1.0),(1.0,1.2),(1.2,1.5),(1.5,2.0),(2.0,99)):
        mm=ok&(ratio>=lo)&(ratio<hi)
        print(f"  {lo:.1f}-{hi:<4.1f}                     {mm.sum():8d} {won[mm].mean()*100:5.1f}% {P_[mm].mean()*100:7.1f}% {mkn[mm].mean()*100:8.1f}% {np.where(won[mm],op[mm]-1,-1).mean()*100:+15.1f}%")
