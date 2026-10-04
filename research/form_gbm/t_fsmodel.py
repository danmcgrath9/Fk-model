"""First-starter races are the weakest segment (KL 0.12 vs 0.072). Does a stage 2 fitted ONLY on races with a
first-starter beat the general one on those races? And one fitted only on races without?"""
import numpy as np, bench as b, stage2
src=open("t_research.py").read().split("# 1. Accardi")[0]
exec(src)
P_=D["P"].astype(float); real=~(P_[:,:,f["trial"]]==1)&np.isfinite(P_[:,:,f["finish"]])&(P_[:,:,f["finish"]]>0); fs=real.sum(1)==0
fsr=np.bincount(ri,weights=fs.astype(float),minlength=nR)>0
hold_fs=hold[fsr[hold]]; hold_no=hold[~fsr[hold]]
def fit_on(races_fit,label):
    inner_,val_=b.split(0.8,races_fit); ks=[]
    for sd in (0,1):
        bst,bi=run(V4,inner_,val_races=val_,seed=sd); bst,_=run(V4,races_fit,rounds=int(bi*1.1),seed=sd); ks.append(b.softmax_races(L+bst.predict(V4)))
    pp=b.softmax_races(np.mean([np.log(k) for k in ks],0))
    print(f"{label:44s} KL on FS races {b.score(pp,hold_fs)[0]:.4f}   on non-FS races {b.score(pp,hold_no)[0]:.4f}   all {b.score(pp,hold)[0]:.4f}",flush=True); return pp
pp_all=fit_on(dev,"stage 2 fitted on every race (live)")
pp_fs=fit_on(dev[fsr[dev]],"stage 2 fitted on first-starter races only")
pp_no=fit_on(dev[~fsr[dev]],"stage 2 fitted on non-first-starter races only")
mix=np.where(fsr[ri],pp_fs,pp_no); print(f"{'split model (FS-only for FS races, else non-FS)':44s} KL all {b.score(mix,hold)[0]:.4f}")
