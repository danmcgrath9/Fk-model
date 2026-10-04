"""Is travel + collateral real? Four seeds instead of two, and the holdout scored by half."""
import numpy as np, bench as b, stage2, gbm, lightgbm as lgb
src=open("t_research.py").read().split("# 1. Accardi")[0]
exec(src)
GC=np.load("G_collateral.npy"); GT=np.load("G_travel.npy")
newer=hold[dates[hold]>="2026-07-20"]; older=hold[dates[hold]<"2026-07-20"]
def ev(X,label,seeds=(0,1,2,3)):
    ks=[]
    for sd in seeds:
        bst,bi=run(X,inner,val_races=val,seed=sd); bst,_=run(X,dev,rounds=int(bi*1.1),seed=sd); ks.append(b.softmax_races(L+bst.predict(X)))
    pp=b.softmax_races(np.mean([np.log(k) for k in ks],0))
    per=[b.score(b.softmax_races(np.log(k)),hold)[0] for k in ks]
    print(f"{label:40s} KL all {b.score(pp,hold)[0]:.4f}  older {b.score(pp,older)[0]:.4f}  newer {b.score(pp,newer)[0]:.4f}  per-seed {np.round(per,4)}",flush=True)
ev(V4,"live (blend9 + stage-2 v4)")
ev(np.column_stack([V4,GT]),"live + travel")
ev(np.column_stack([V4,GC]),"live + collateral")
ev(np.column_stack([V4,GT,GC]),"live + travel + collateral")
