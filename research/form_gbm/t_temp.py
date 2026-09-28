# race-level temperature on OOF prices: p ∝ p_oof^T, T = exp(w·z_race). fit on older races, test newer.
import numpy as np, bench as b, torch
D=b.load(); p=np.load("p_oof.npy"); ri=D["race_idx"]; nR=D["n_races"]
F=np.load("F7.npy"); names=open("F7_names.txt").read().split("\n"); c={n:i for i,n in enumerate(names)}
dates=D["date"]; cut="2026-05-06"; dev=np.where(dates<cut)[0]; hold=np.where(dates>=cut)[0]
def rmean(v): v=np.nan_to_num(v.astype(float)); return np.bincount(ri,weights=v,minlength=nR)/np.bincount(ri,minlength=nR)
fs=np.nan_to_num(F[:,c["f_careerForm_s"]],nan=-1)
spd=np.isnan(F[:,c["e_speedRating_last"]]).astype(float)
field=np.bincount(ri,minlength=nR).astype(float)
lp=np.log(np.maximum(p,1e-12))
ent=-np.bincount(ri,weights=p*lp,minlength=nR)
Z=np.stack([np.ones(nR),np.log(field),rmean(fs<1),rmean(spd),rmean(F[:,c["age"]]==2),ent,np.log(D["distance"].astype(float)) if "distance" in D else np.zeros(nR)],1)
Z[:,1:]=(Z[:,1:]-Z[dev][:,1:].mean(0))/np.maximum(Z[dev][:,1:].std(0),1e-9)
q=torch.tensor(D["q"]); L=torch.tensor(lp); R=torch.tensor(ri).long(); Zt=torch.tensor(Z)
def kl(w,races):
    m=torch.tensor(np.isin(ri,races))
    T=torch.exp(Zt@w)[R]; s=T*L
    mx=torch.zeros(nR,dtype=torch.float64).index_reduce_(0,R,s,"amax",include_self=False)
    e=torch.exp(s-mx[R]); den=torch.zeros(nR,dtype=torch.float64).index_add_(0,R,e)
    lq=s-mx[R]-torch.log(den[R])
    return -(q*lq)[m].sum()/len(races)
for cols,label in ((1,"single T"),(Z.shape[1],"race-feature T")):
    w=torch.zeros(Z.shape[1],dtype=torch.float64,requires_grad=True)
    mask=torch.zeros(Z.shape[1],dtype=torch.float64); mask[:cols]=1
    opt=torch.optim.LBFGS([w],max_iter=200)
    def cl():
        opt.zero_grad(); l=kl(w*mask,dev); l.backward(); return l
    opt.step(cl)
    wv=(w*mask).detach()
    T=np.exp(Z@wv.numpy())[ri]; pn=b.softmax_races(T*lp)
    print(label, np.round(wv.numpy(),3))
    print("  hold base", b.fmt("",b.score(p,hold)), "\n  hold new ", b.fmt("",b.score(pn,hold)))
