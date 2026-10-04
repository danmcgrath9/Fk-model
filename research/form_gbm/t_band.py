"""Focus on the $2-$15 horses. Band KL = KL to BSP over runners that started $15 or shorter, each race's chances
renormalised among those runners. Experiments: (E) stage 2 fitted on band runners only (stage-1 price >= 1/20),
roughies kept at stage 1; (G) per-price-band log shift learned on dev; (O) oracle: roughies set to BSP (ceiling)."""
import numpy as np, bench as b, stage2, lightgbm as lgb, gbm
src=open("t_research.py").read().split("# 1. Accardi")[0]
exec(src)
q=D["q"]; mkt=D["mkt"]; hm=np.isin(ri,hold); pp=np.load("pp_hold_v4.npy")
def band_kl(pr,races,cut=1/15):
    m=np.isin(ri,races)&(q>=cut)&np.isfinite(pr); r_=ri[m]
    qn=q[m]/np.bincount(r_,weights=q[m],minlength=nR)[r_]; pn=pr[m]/np.bincount(r_,weights=pr[m],minlength=nR)[r_]
    return np.sum(qn*np.log(np.maximum(qn,1e-300)/np.maximum(pn,1e-12)))/len(np.unique(r_))
def gaps(pr,m):
    ap=np.abs(pr[m]/q[m]-1); return f"typical gap {np.median(ap)*100:3.0f}%  within 25% {np.mean(ap<=0.25)*100:3.0f}%"
band=hm&(1/q<=15)&(1/q>=2)
def report(nm,pr):
    print(f"{nm:46s} KL all {b.score(pr,hold)[0]:.4f}  band KL {band_kl(pr,hold):.4f}  $2-$15: {gaps(pr,band)}",flush=True)
report("opening market",np.where(np.isfinite(mkt),mkt,p))
report("live v5 (stage 2 on everyone)",pp)
# O: oracle, roughies at BSP exactly, band renormalised to the remaining mass
rough=1/p>20
o=pp.copy(); o[rough]=q[rough]
for r in np.unique(ri[hm]):
    m=ri==r; mass=1-o[m&rough].sum(); kb=m&~rough; o[kb]=o[kb]/max(o[kb].sum(),1e-9)*max(mass,1e-6)
report("oracle: roughies (stage-1 $20+) at BSP",o)
# E: stage 2 fitted on band runners only
keep=(1/p<=20)
def run2(X,rows,val_rows=None,rounds=None,seed=0):
    _,rr=np.unique(ri[rows],return_inverse=True); n_=rr.max()+1
    qn=q[rows]/np.bincount(rr,weights=q[rows])[rr]
    Pm=dict(learning_rate=0.03,num_leaves=7,min_data_in_leaf=200,feature_fraction=0.7,bagging_fraction=0.8,bagging_freq=1,lambda_l2=10,verbose=-1,objective="none",num_threads=4,seed=seed)
    bst=lgb.Booster(params=Pm,train_set=lgb.Dataset(X[rows],init_score=L[rows])); fo=gbm.make_obj(rr,n_,qn); best,bi=9,0
    for it in range(1,(rounds or 2000)+1):
        bst.update(fobj=fo)
        if val_rows is not None and it%25==0:
            s=score_rows(L+bst.predict(X),val_rows)
            if s<best-1e-5: best,bi=s,it
            elif it-bi>=150: break
    return bst,bi
def score_rows(z,rows):
    _,rr=np.unique(ri[rows],return_inverse=True); e=np.exp(z[rows]-np.array([z[rows][rr==k].max() for k in range(rr.max()+1)])[rr]); pn=e/np.bincount(rr,weights=e)[rr]
    qn=q[rows]/np.bincount(rr,weights=q[rows])[rr]; return np.sum(qn*np.log(np.maximum(qn,1e-300)/np.maximum(pn,1e-12)))/(rr.max()+1)
def band_fit(X,label):
    ks=[]
    for sd in (0,1):
        bst,bi=run2(X,np.isin(ri,inner)&keep,val_rows=np.isin(ri,val)&keep,seed=sd); bst,_=run2(X,np.isin(ri,dev)&keep,rounds=int(bi*1.1),seed=sd); ks.append(L+bst.predict(X))
    z=np.mean(ks,0); out=p.copy()
    for r in np.unique(ri[hm]):
        m=ri==r; kb=m&keep
        if kb.sum()==0: continue
        mass=1-p[m&~keep].sum(); e=np.exp(z[kb]-z[kb].max()); out[kb]=e/e.sum()*max(mass,1e-6)
    report(label,out); return out
e_out=band_fit(V4,"E: stage 2 fitted on $20-or-shorter only")
# G: per-band log shift (10 bands by model price) learned on dev races, applied everywhere
bands=np.digitize(1/pp,[2,3,4,6,8,12,20,35,60])
devm=np.isin(ri,dev); shift=np.zeros(10)
for k in range(10):
    m=devm&(bands==k)
    if m.sum()>200: shift[k]=np.log(q[m].sum()/pp[m].sum())
print("band shifts (log, by model price band):",shift.round(3))
g=np.exp(np.log(pp)+shift[bands]); g=g/np.bincount(ri,weights=g,minlength=nR)[ri]
report("G: per-band calibration of live v5",g)
