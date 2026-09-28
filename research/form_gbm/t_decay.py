import numpy as np, bench as b, lab, gbm, datetime as dt, time
D=lab.D; F=np.load("F7.npy"); names=open("F7_names.txt").read().split("\n"); ri=D["race_idx"]
dn=np.array([(dt.date.fromisoformat(str(d)[:10])-dt.date(2025,1,1)).days for d in D["date"]])
last=dn[lab.INNER].max()
orig=gbm.make_obj
for hl in (180,90):
    w_r=0.5**((last-dn)/hl)
    def make_obj(rr,nR,t,_w=w_r):
        # rr indexes the stacked (orig + augmented) inner races in order; recover race weights through lab's partition
        return orig(rr,nR,t)
    # weight via duplicated gradients: wrap objective using the training mask order
    nRall=D["n_races"]; tr=np.concatenate([lab.INNER,lab.INNER+nRall]); rix=np.concatenate([ri,ri+nRall])
    m=np.isin(rix,tr); wrun=np.concatenate([w_r[ri],w_r[ri]])[m]
    def mk(rr,nR,t,wrun=wrun):
        f=orig(rr,nR,t)
        def obj(preds,ds):
            g,h=f(preds,ds); return g*wrun, h*wrun
        return obj
    gbm.make_obj=mk
    t0=time.time(); s,it,bst=lab.valid_score(F,names,params=dict(feature_fraction=0.2,extra_trees=True),rounds=8000,seed=0)
    print(b.fmt(f"half-life {hl}d it{it}",s),f"{time.time()-t0:.0f}s",flush=True)
gbm.make_obj=orig
