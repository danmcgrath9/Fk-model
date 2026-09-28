# leak-free check: stage-1 = model trained only on the older 70% (p_final3); residuals only from unseen races, earlier dates.
import numpy as np, bench as b, torch
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; dates=D["date"]
TR,TE=b.split(); p=np.load("p_final3.npy"); rd=dates[ri]
inTE=np.isin(ri,TE)
res=np.clip(np.log(np.maximum(D["q"],1e-4))-np.log(np.maximum(p,1e-4)),-3,3)
def enc(key,k=10):
    s={};n={};out=np.zeros(len(ri))
    for d in np.unique(rd[inTE]):
        ix=np.where((rd==d)&inTE)[0]
        for i in ix: out[i]=s.get(key[i],0.0)/(n.get(key[i],0)+k)
        for i in ix: s[key[i]]=s.get(key[i],0.0)+res[i]; n[key[i]]=n.get(key[i],0)+1
    return out
keys=["trainer","jockey","horse_id","sire","training_location"]
E=np.stack([enc(D[k].astype(str)) for k in keys],1)
m=np.bincount(ri,weights=np.ones(len(ri)),minlength=nR)
Ec=E-np.stack([np.bincount(ri,weights=E[:,j],minlength=nR)/m for j in range(E.shape[1])],1)[ri]
ted=np.sort(dates[TE]); cut=ted[len(ted)//2]; A=TE[dates[TE]<cut]; B_=TE[dates[TE]>=cut]
L=np.log(np.maximum(p,1e-12)); q=torch.tensor(D["q"]); R=torch.tensor(ri).long(); Lt=torch.tensor(L)
def fit(cols):
    Z=torch.tensor(Ec[:,cols]); w=torch.zeros(len(cols),dtype=torch.float64,requires_grad=True); ma=torch.tensor(np.isin(ri,A))
    def lf():
        s=Lt+Z@w; mx=torch.zeros(nR,dtype=torch.float64).index_reduce_(0,R,s.detach(),"amax",include_self=False)
        e=torch.exp(s-mx[R]); den=torch.zeros(nR,dtype=torch.float64).index_add_(0,R,e)
        return -(q*(s-mx[R]-torch.log(den[R])))[ma].sum()/len(A)+1e-3*(w**2).sum()
    opt=torch.optim.LBFGS([w],max_iter=100)
    def cl(): opt.zero_grad(); l=lf(); l.backward(); return l
    opt.step(cl); wv=w.detach().numpy(); return wv,b.softmax_races(L+Ec[:,cols]@wv)
print("second half of unseen races:",len(B_))
print(b.fmt("model (trained on older 70%)",b.score(p,B_)))
print(b.fmt("opening market",b.score(D["mkt"],B_)))
for cols in ([2],[0],[1],[0,1,2],[0,1,2,3,4]):
    wv,pn=fit(cols); print(b.fmt(f"+{'+'.join(keys[c] for c in cols)} {np.round(wv,2)}",b.score(pn,B_)))
wv,p2=fit([0,1,2])
op=D["open"]; bsp=np.where(np.isfinite(D["bsp"])&(D["bsp"]>1),D["bsp"],np.nan); won=D["won"]==1; mh=np.isin(ri,B_)
for lab_,pp in (("base",p),("+encodings",p2)):
    fair=1/np.maximum(pp,1e-9); ev=pp*op-1; ok=np.isfinite(op)&(op>1)&mh; base=ok&(fair<50)&(op<3*fair)
    for t in (0.2,0.5):
        sel=base&(ev>t); n=sel.sum(); r=op[sel&won].sum(); rb=np.nan_to_num(bsp[sel&won]).sum()
        print(f"{lab_:11s} value {int(t*100)}c+ bets {n:4d} ROI open {r/n-1:+.1%} BSP {rb/n-1:+.1%}")
