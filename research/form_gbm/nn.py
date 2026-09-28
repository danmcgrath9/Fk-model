import numpy as np, torch, bench as b, lab
torch.set_num_threads(4)
D=lab.D; ri=lab.ri0; nR=D["n_races"]

def pack(X, races, target):
    """races -> padded tensors [R, M, k], mask, target."""
    M=int((D["ends"]-D["starts"]).max())
    R=len(races); k=X.shape[1]
    Xt=np.zeros((R,M,k),np.float32); T=np.zeros((R,M),np.float32); Mk=np.zeros((R,M),bool)
    for i,r in enumerate(races):
        s,e=D["starts"][r],D["ends"][r]; n=e-s
        Xt[i,:n]=X[s:e]; T[i,:n]=target[s:e]; Mk[i,:n]=True
    return torch.tensor(Xt),torch.tensor(T),torch.tensor(Mk)

class Net(torch.nn.Module):
    def __init__(s,k,h=128,drop=0.2):
        super().__init__(); s.f=torch.nn.Sequential(torch.nn.Linear(k,h),torch.nn.ReLU(),torch.nn.Dropout(drop),torch.nn.Linear(h,64),torch.nn.ReLU(),torch.nn.Dropout(drop),torch.nn.Linear(64,1))
    def forward(s,x,m):
        z=s.f(x).squeeze(-1); z=z.masked_fill(~m,-1e9); return torch.log_softmax(z,-1)

def prep(F, fit_rows):
    X=F.astype(np.float64).copy()
    mu=np.nanmean(X[fit_rows],0); sd=np.nanstd(X[fit_rows],0); sd[~np.isfinite(sd)|(sd<1e-9)]=1; mu[~np.isfinite(mu)]=0
    X=(X-mu)/sd; miss=np.isnan(X); X[miss]=0; X=np.clip(X,-5,5)
    return X.astype(np.float32)

def fit(F, names, train_races, valid_races=None, epochs=60, seed=0, lr=1e-3, wd=1e-4, h=128, drop=0.2, fixed_epochs=None):
    torch.manual_seed(seed); np.random.seed(seed)
    rows=np.isin(ri,train_races); X=prep(F,rows); Xa=prep(lab.augmented(F,names,seed=seed+40),rows)
    Xtr,Ttr,Mtr=pack(X,train_races,D["q"]); Xa_,_,_=pack(Xa,train_races,D["q"])
    Xtr=torch.cat([Xtr,Xa_]); Ttr=torch.cat([Ttr,Ttr]); Mtr=torch.cat([Mtr,Mtr])
    net=Net(X.shape[1],h,drop); opt=torch.optim.AdamW(net.parameters(),lr=lr,weight_decay=wd)
    if valid_races is not None: Xv,Tv,Mv=pack(X,valid_races,D["q"])
    best=(1e9,0,None); E=fixed_epochs or epochs
    for ep in range(E):
        net.train(); perm=torch.randperm(len(Xtr))
        for i in range(0,len(perm),256):
            j=perm[i:i+256]; lp=net(Xtr[j],Mtr[j]); loss=-(Ttr[j]*lp).sum()/len(j)
            opt.zero_grad(); loss.backward(); opt.step()
        if valid_races is not None:
            net.eval()
            with torch.no_grad(): lp=net(Xv,Mv); kl=(Tv*(torch.log(Tv.clamp_min(1e-12))-lp)).masked_fill(~Mv,0).sum()/len(Xv)
            if kl.item()<best[0]-1e-5: best=(kl.item(),ep+1,{k:v.clone() for k,v in net.state_dict().items()})
            elif ep+1-best[1]>=8: break
    if valid_races is not None: net.load_state_dict(best[2])
    net.eval()
    with torch.no_grad():
        allr=np.arange(nR); Xall,_,Mall=pack(X,allr,D["q"]); lp=net(Xall,Mall).numpy()
    p=np.zeros(len(ri))
    for i,r in enumerate(allr):
        s,e=D["starts"][r],D["ends"][r]; p[s:e]=np.exp(lp[i,:e-s])
    return p, (best[1] if valid_races is not None else E)
