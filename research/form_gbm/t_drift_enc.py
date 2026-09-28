import numpy as np, bench as b, lightgbm as lgb, gbm, datetime as dt
D=b.load(); p=np.load("p_oof.npy"); ri=D["race_idx"]; nR=D["n_races"]; dates=D["date"]; rd=dates[ri]
ud=np.unique(rd); byd=[np.where(rd==d)[0] for d in ud]
def enc(key,res,k=5,last=False):
    s={};n={};out=np.zeros(len(ri))
    for ix in byd:
        for i in ix:
            if key[i] in s: out[i]=s[key[i]]/(n[key[i]]+k)
        for i in ix:
            kk=key[i]
            if last: s[kk]=res[i]; n[kk]=1.0
            else: s[kk]=s.get(kk,0.0)+res[i]; n[kk]=n.get(kk,0.0)+1
    return out
drift=np.clip(np.log(np.maximum(D["q"],1e-4))-np.log(np.maximum(D["mkt"],1e-4)),-3,3)  # firmed (+) / drifted (-) last time
H=D["horse_id"].astype(str); T=D["trainer"].astype(str)
Xd=np.stack([enc(H,drift,1,last=True),enc(T,drift,10)],1)
E=np.load("renc_oof.npy"); cnt=np.bincount(ri,minlength=nR)
cen=lambda v: v-(np.bincount(ri,weights=v,minlength=nR)/cnt)[ri]
L=np.log(np.maximum(p,1e-12)); Lc=L-(np.bincount(ri,weights=L,minlength=nR)/cnt)[ri]
base=np.column_stack([E,np.stack([cen(E[:,j]) for j in range(E.shape[1])],1),Lc,np.log(cnt[ri]),p])
cut="2026-05-06"; dev=np.where(dates<cut)[0]; hold=np.where(dates>=cut)[0]; inner,val=b.split(0.8,dev)
def part(races):
    m=np.isin(ri,races); _,rr=np.unique(ri[m],return_inverse=True); return m,rr,rr.max()+1
def run(X,races_fit,rounds=None,val_races=None):
    m,rr,n=part(races_fit)
    P=dict(learning_rate=0.03,num_leaves=7,min_data_in_leaf=200,feature_fraction=0.7,bagging_fraction=0.8,bagging_freq=1,lambda_l2=10,verbose=-1,objective="none",num_threads=4)
    bst=lgb.Booster(params=P,train_set=lgb.Dataset(X[m],init_score=L[m])); f=gbm.make_obj(rr,n,D["q"][m]); best,bi=9,0
    for it in range(1,(rounds or 2000)+1):
        bst.update(fobj=f)
        if val_races is not None and it%25==0:
            s=b.score(b.softmax_races(L+bst.predict(X)),val_races)[0]
            if s<best-1e-5: best,bi=s,it
            elif it-bi>=150: break
    return bst,bi
for nm,X in (("stage-2",base),("stage-2 + past drift",np.column_stack([base,Xd,np.stack([cen(Xd[:,j]) for j in range(2)],1)]))):
    bst,bi=run(X,inner,val_races=val); bst,_=run(X,dev,rounds=int(bi*1.1))
    print(b.fmt(f"hold {nm} r{bi}",b.score(b.softmax_races(L+bst.predict(X)),hold)),flush=True)
