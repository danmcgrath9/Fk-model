# market-residual encodings (what BSP knew beyond our model), strictly from earlier dates; stage-2 on OOF.
import numpy as np, bench as b
D=b.load(); p=np.load("p_oof.npy"); ri=D["race_idx"]; nR=D["n_races"]; dates=D["date"]
res=np.clip(np.log(np.maximum(D["q"],1e-4))-np.log(np.maximum(p,1e-4)),-3,3)
rd=dates[ri]; order=np.argsort(rd,kind="stable")
keys={"trainer":D["trainer"],"jockey":D["jockey"],"horse":D["horse_id"],"sire":D["sire"],"loc":D["training_location"],
      "trk_trainer":np.char.add(D["trainer"].astype(str),D["track"][ri].astype(str))}
def enc(key,k=10):
    s={};n={};out=np.zeros(len(ri)); cnt=np.zeros(len(ri))
    ud=np.unique(rd)
    idx_by_date={d:np.where(rd==d)[0] for d in ud}
    for d in ud:
        ix=idx_by_date[d]
        for i in ix:
            kk=key[i]; out[i]=s.get(kk,0.0)/(n.get(kk,0)+k); cnt[i]=n.get(kk,0)
        for i in ix:
            kk=key[i]; s[kk]=s.get(kk,0.0)+res[i]; n[kk]=n.get(kk,0)+1
    return out,cnt
E={}
for nm,key in keys.items(): E[nm],_=enc(key.astype(str)); print(nm,"done",flush=True)
def centered(v):
    m=np.bincount(ri,weights=v,minlength=nR)/np.bincount(ri,minlength=nR); return v-m[ri]
cut="2026-05-06"; dev=np.where(dates<cut)[0]; hold=np.where(dates>=cut)[0]
import torch
L=np.log(np.maximum(p,1e-12)); q=torch.tensor(D["q"]); R=torch.tensor(ri).long()
def fit(cols):
    Z=torch.tensor(np.stack([centered(E[c]) for c in cols],1)); Lt=torch.tensor(L)
    w=torch.zeros(len(cols),dtype=torch.float64,requires_grad=True)
    md=torch.tensor(np.isin(ri,dev))
    def lossf(w,m):
        s=Lt+Z@w; mx=torch.zeros(nR,dtype=torch.float64).index_reduce_(0,R,s.detach(),"amax",include_self=False)
        e=torch.exp(s-mx[R]); den=torch.zeros(nR,dtype=torch.float64).index_add_(0,R,e)
        return -(q*(s-mx[R]-torch.log(den[R])))[m].sum()
    opt=torch.optim.LBFGS([w],max_iter=100)
    def cl():
        opt.zero_grad(); l=lossf(w,md)/len(dev)+1e-3*(w**2).sum(); l.backward(); return l
    opt.step(cl); wv=w.detach().numpy()
    pn=b.softmax_races(L+np.stack([centered(E[c]) for c in cols],1)@wv); return wv,pn
print(b.fmt("hold base",b.score(p,hold)))
for cols in (["trainer"],["jockey"],["horse"],["sire"],["loc"],["trk_trainer"],list(keys)):
    wv,pn=fit(cols); print(b.fmt(f"hold +{'+'.join(cols)} w={np.round(wv,2)}",b.score(pn,hold)))
np.save("resid_enc.npy",np.stack([E[c] for c in keys],1))
