import numpy as np, bench as b, lightgbm as lgb, gbm
D=b.load(); p=np.load("p_oof.npy"); ri=D["race_idx"]; nR=D["n_races"]; dates=D["date"]
E=np.load("renc_oof.npy"); cnt=np.bincount(ri,minlength=nR)
cen=lambda v: v-(np.bincount(ri,weights=v,minlength=nR)/cnt)[ri]
L=np.log(np.maximum(p,1e-12)); Lc=L-(np.bincount(ri,weights=L,minlength=nR)/cnt)[ri]
X=np.column_stack([E,np.stack([cen(E[:,j]) for j in range(E.shape[1])],1),Lc,np.log(cnt[ri]),p])
cut="2026-05-06"; dev=np.where(dates<cut)[0]; hold=np.where(dates>=cut)[0]
inner,val=b.split(0.8,dev)
def part(races):
    m=np.isin(ri,races); _,rr=np.unique(ri[m],return_inverse=True); return m,rr,rr.max()+1
def run(races_fit,rounds=None,val_races=None,params={}):
    m,rr,n=part(races_fit)
    P=dict(learning_rate=0.03,num_leaves=7,min_data_in_leaf=200,feature_fraction=0.7,bagging_fraction=0.8,bagging_freq=1,lambda_l2=10,verbose=-1,objective="none",num_threads=4); P.update(params)
    ds=lgb.Dataset(X[m],init_score=L[m]); bst=lgb.Booster(params=P,train_set=ds); f=gbm.make_obj(rr,n,D["q"][m])
    best,bi=9,0
    for it in range(1,(rounds or 2000)+1):
        bst.update(fobj=f)
        if val_races is not None and it%25==0:
            s=b.score(b.softmax_races(L+bst.predict(X)),val_races)[0]
            if s<best-1e-5: best,bi=s,it
            elif it-bi>=150: break
    return bst,bi
bst,bi=run(inner,val_races=val); print("best rounds",bi)
bst,_=run(dev,rounds=int(bi*1.1))
print(b.fmt("hold base",b.score(p,hold)))
print(b.fmt("hold tree stage-2",b.score(b.softmax_races(L+bst.predict(X)),hold)))
F=np.load("F7.npy"); g=np.load("F7_gain.npy"); top=np.argsort(-g)[:30]
X0=X.copy()
for k in ():
    X=np.column_stack([X0,F[:,top[:k]]])
    bst,bi=run(inner,val_races=val); bst,_=run(dev,rounds=int(bi*1.1))
    print(b.fmt(f"hold stage-2 + top{k} form feats (r{bi})",b.score(b.softmax_races(L+bst.predict(X)),hold)))
X=X0
for s in range(1):
    bst,bi=run(inner,val_races=val,params=dict(seed=s)); bst,_=run(dev,rounds=int(bi*1.1),params=dict(seed=s))
    print(s,b.fmt("seed",b.score(b.softmax_races(L+bst.predict(X)),hold)))
p2=b.softmax_races(L+bst.predict(X)); np.save("p_stage2_hold.npy",p2)
op=D["open"]; bsp=np.where(np.isfinite(D["bsp"])&(D["bsp"]>1),D["bsp"],np.nan); won=D["won"]==1
Fz=np.load("F7.npy"); nm=open("F7_names.txt").read().split("\n"); cc={n:i for i,n in enumerate(nm)}
solid=(np.nan_to_num(Fz[:,cc["f_careerForm_s"]],nan=-1)>=1)&~np.isnan(Fz[:,cc["e_speedRating_last"]])&(Fz[:,cc["age"]]!=2)
mh=np.isin(ri,hold)
for lab_,pp in (("base",p),("stage-2",p2)):
    fair=1/np.maximum(pp,1e-9); ev=pp*op-1; ok=np.isfinite(op)&(op>1)&mh; base=ok&(fair<50)&(op<3*fair)
    kel=np.clip(25*ev/np.maximum(op-1,0.01),0,5)
    for nm_,sel,st in (("value 20c",base&(ev>0.2),np.ones(len(ri))),("kelly 5c",base&(ev>0.05),kel),("best bet",base&(ev>0.5)&solid&(op>=3)&(op<=20),np.ones(len(ri)))):
        s=np.where(sel,st,0); r=np.where(sel&won,s*op,0).sum(); rb=np.where(sel&won&np.isfinite(bsp),s*bsp,0).sum()
        print(f"{lab_:8s} {nm_:10s} bets {sel.sum():5d} units {s.sum():8.1f} ROI open {r/s.sum()-1:+.1%}  BSP {rb/s.sum()-1:+.1%}")
