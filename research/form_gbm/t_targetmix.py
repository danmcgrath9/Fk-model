"""Stage 2 fitted to a blend of BSP and the actual winner (does the model learn where BSP itself is wrong?),
scored on the holdout by KL to BSP, log-loss on winners, and the live bet set's ROI at BSP."""
import numpy as np, bench as b, stage2, lightgbm as lgb, gbm
src=open("t_research.py").read().split("# 1. Accardi")[0]
exec(src)
q0=D["q"].copy(); won_=(D["won"]==1).astype(float)
def fit_mix(alpha,label):
    qm=(1-alpha)*q0+alpha*won_; D["q"]=qm   # the harness reads D["q"] inside run()
    ks=[]
    for sd in (0,1):
        bst,bi=run(V4,inner,val_races=val,seed=sd); bst,_=run(V4,dev,rounds=int(bi*1.1),seed=sd); ks.append(b.softmax_races(L+bst.predict(V4)))
    D["q"]=q0; pp=b.softmax_races(np.mean([np.log(k) for k in ks],0))
    kl,ll,_=b.score(pp,hold)[:3]
    m=np.isin(ri,hold)&np.isfinite(D["open"])&(D["open"]>1)&np.isfinite(D["bsp"])&(D["bsp"]>1)&(pp*D["open"]-1>=0.2)&(1/pp>=2)&(1/pp<=15)
    prof=np.where(D["won"]==1,(D["bsp"]-1)*0.92,-1.0)
    print(f"{label:34s} KL {kl:.4f}  LL {ll:.4f}  value bets {m.sum():4d}  BSP ROI {prof[m].mean()*100:+.1f}%",flush=True)
fit_mix(0.0,"target = BSP (live)"); fit_mix(0.15,"target = 85% BSP + 15% winner"); fit_mix(0.3,"target = 70% BSP + 30% winner")
