import numpy as np, bench as b
D=b.load("ds/model_ds.npz"); ri=D["race_idx"]; nR=D["n_races"]; c=D["colidx"]; X=D["X"].astype(float)
dates=D["date"][ri]; newer=dates>="2026-05-06"
pb=np.load("p_oof_blend9.npy"); op=D["open"].astype(float); bsp=D["bsp"].astype(float); won=D["finish"]==1
val=np.isfinite(op)&(op>1)&np.isfinite(bsp)&(bsp>1)&(pb*op-1>=0.2); prof=np.where(won,(bsp-1)*0.92,-1.0)
field=np.bincount(ri,minlength=nR)[ri]; bs=X[:,c["raw_barrier_share"]]; ss=X[:,c["raw_settle_share"]]; es=X[:,c["sm_early_speed"]]; pp=X[:,c["sm_predicted_position"]]
dist=D["distance"][ri].astype(float); tempo=X[:,c["tempo_max"]]
def rep(m,lab):
    for nm,mm in (("all",m),("newer",m&newer)):
        n=mm.sum(); print(f"  {lab:52s} {nm:5s} bets {n:5d}  BSP ROI {prof[mm].mean()*100 if n else float('nan'):+6.1f}%")
wide=(bs>=0.75)&(field>=10); inside=bs<=0.35; lead=ss<=0.25; back=ss>=0.6
rep(val,"value 20c+ (all)")
rep(val&wide&lead,"wide draw, usually leads/on pace")
rep(val&inside&lead,"inside draw, usually leads/on pace")
rep(val&wide&back,"wide draw, usually back")
rep(val&wide&(dist<=1200),"wide draw, sprint (<=1200m)")
rep(val&wide&(dist>=1600),"wide draw, 1600m+")
rep(val&(X[:,c["blinkers_first"]]==1),"blinkers first time")
rep(val&(X[:,c["gear_first_time"]]>=1),"any gear first time")
rep(val&(dist<=1000),"1000m or shorter")
