import numpy as np
exec(open("t_confidence.py").read().split('print("(a)')[0])
rng=np.random.default_rng(1)
def plan(w,mult,cap):
    ps=np.exp(w*np.log(p)+(1-w)*np.log(1/op)); k=np.clip((ps*op-1)/(op-1),0,1); return np.minimum(cap,k*mult)
def rep(nm,s,cap=3.0):
    m=live; s=s[m]; inv=s.sum(); ro=(s*po[m]).sum(); rb=(s*pb[m]).sum()
    # bank needed: bootstrap 2,000 seasons of these bets in random order, 5th percentile of worst drawdown
    pr_=s*po[m]; dds=[]
    for _ in range(2000):
        x=rng.permutation(pr_); c=np.cumsum(x); dds.append((np.maximum.accumulate(np.concatenate([[0],c]))[1:]-c).max())
    print(f"{nm:46s} open {ro/inv*100:+6.1f}%  BSP {rb/inv*100:+5.1f}%  avg stake {s.mean():.2f}u  max {s.max():.1f}u  at cap {np.mean(s>=cap-1e-9)*100:3.0f}%  under 0.5u {np.mean(s<0.5)*100:3.0f}%  drawdown: typical ${100*np.median(dds):,.0f}  bad season (95th) ${100*np.percentile(dds,95):,.0f}")
rep("current: overlay/0.2, cap 3",np.minimum(3.0,v/0.2))
for w,mult,cap in ((0.5,25,3),(0.5,20,3),(0.5,30,3),(0.5,25,2),(0.5,25,4),(0.75,25,3),(0.5,25,99)):
    rep(f"Kelly x{mult}, ours {int(w*100)}%/open {int((1-w)*100)}%, cap {cap}",plan(w,mult,cap),cap)
print("\nclosing line value: did our bets shorten by the jump?")
m=live; mv=np.log(bsp[m]/op[m]); print(f"live bets: {np.mean(bsp[m]<op[m])*100:.0f}% shortened, median move {100*(np.exp(np.median(mv))-1):+.0f}%, mean {100*(np.exp(mv.mean())-1):+.0f}%")
m2=caps&~live&(v<0); mv2=np.log(bsp[m2]/op[m2]); print(f"horses we price UNDER the open (no bet): {np.mean(bsp[m2]<op[m2])*100:.0f}% shortened, median move {100*(np.exp(np.median(mv2))-1):+.0f}%")
print("\nby stake plan, how much goes on each price band (share of turnover):")
for nm,s in (("overlay cap 3",np.minimum(3.0,v/0.2)),("Kelly x25 50/50 cap 3",plan(0.5,25,3))):
    out=[]
    for lo,hi in ((2,4),(4,6),(6,9),(9,12),(12,15)):
        mm=live&(1/p>=lo)&(1/p<hi); out.append(f"${lo}-{hi}: {s[mm].sum()/s[live].sum()*100:3.0f}%")
    print(f"  {nm:24s} "+"  ".join(out))
