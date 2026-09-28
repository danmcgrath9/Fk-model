# tune the encodings on the OOF set (dev < 2026-05-06, hold after): shrinkage, time decay, last-run residual
import numpy as np, bench as b, torch
D=b.load(); p=np.load("p_oof.npy"); ri=D["race_idx"]; nR=D["n_races"]; dates=D["date"]; rd=dates[ri]
import datetime as dt
dn=np.array([(dt.date.fromisoformat(str(d)[:10])-dt.date(2025,1,1)).days for d in rd])
res=np.clip(np.log(np.maximum(D["q"],1e-4))-np.log(np.maximum(p,1e-4)),-3,3)
ud=np.unique(rd); byd=[np.where(rd==d)[0] for d in ud]
def enc(key,k=10,half=None,last=False):
    s={};n={};t={};out=np.zeros(len(ri))
    for ix in byd:
        for i in ix:
            kk=key[i]
            if kk in s:
                if half: f=0.5**((dn[i]-t[kk])/half); S,N=s[kk]*f,n[kk]*f
                else: S,N=s[kk],n[kk]
                out[i]=S/(N+k)
        for i in ix:
            kk=key[i]
            if half and kk in s: f=0.5**((dn[i]-t[kk])/half); s[kk]*=f; n[kk]*=f
            if last: s[kk]=res[i]; n[kk]=1.0
            else: s[kk]=s.get(kk,0.0)+res[i]; n[kk]=n.get(kk,0.0)+1
            t[kk]=dn[i]
    return out
cut="2026-05-06"; dev=np.where(dates<cut)[0]; hold=np.where(dates>=cut)[0]
cnt=np.bincount(ri,minlength=nR)
cen=lambda v: v-(np.bincount(ri,weights=v,minlength=nR)/cnt)[ri]
L=np.log(np.maximum(p,1e-12)); q=torch.tensor(D["q"]); R=torch.tensor(ri).long(); Lt=torch.tensor(L); md=torch.tensor(np.isin(ri,dev))
def fit(Zn):
    Z=torch.tensor(Zn); w=torch.zeros(Zn.shape[1],dtype=torch.float64,requires_grad=True)
    def lf():
        s=Lt+Z@w; mx=torch.zeros(nR,dtype=torch.float64).index_reduce_(0,R,s.detach(),"amax",include_self=False)
        e=torch.exp(s-mx[R]); den=torch.zeros(nR,dtype=torch.float64).index_add_(0,R,e)
        return -(q*(s-mx[R]-torch.log(den[R])))[md].sum()/len(dev)+1e-3*(w**2).sum()
    opt=torch.optim.LBFGS([w],max_iter=100)
    def cl(): opt.zero_grad(); l=lf(); l.backward(); return l
    opt.step(cl); wv=w.detach().numpy(); return wv,b.score(b.softmax_races(L+Zn@wv),hold)
H=D["horse_id"].astype(str); T=D["trainer"].astype(str); J=D["jockey"].astype(str)
print(b.fmt("base",b.score(p,hold)))
for k in ():
    print(b.fmt(f"horse k={k}",fit(cen(enc(H,k))[:,None])[1]))
# k=1",fit(cen(enc(H,1,last=True))[:,None])[1]))
for hl in ():
    print(b.fmt(f"horse k=5 half-life {hl}d",fit(cen(enc(H,5,half=hl))[:,None])[1]))
for k in ():
    print(b.fmt(f"trainer k={k}",fit(cen(enc(T,k))[:,None])[1]), b.fmt(f"jockey k={k}",fit(cen(enc(J,k))[:,None])[1]))
print("--- combos")
hl=cen(enc(H,1,last=True)); hm=cen(enc(H,5,half=120)); tr_=cen(enc(T,5)); jo=cen(enc(J,5))
S=D["sire"].astype(str); si=cen(enc(S,20))
TT=np.char.add(T,D["track"][ri].astype(str)); tt=cen(enc(TT,10))
for nm,Z in (("last+mean",[hl,hm]),("last+mean+trainer+jockey",[hl,hm,tr_,jo]),("all six",[hl,hm,tr_,jo,si,tt])):
    wv,s=fit(np.stack(Z,1)); print(b.fmt(f"{nm} {np.round(wv,2)}",s))
np.save("renc_oof.npy",np.stack([enc(H,1,last=True),enc(H,5,half=120),enc(T,5),enc(J,5),enc(S,20),enc(TT,10)],1))
