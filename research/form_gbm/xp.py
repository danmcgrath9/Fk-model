"""lab experiment runner: python xp.py NAME ; appends to xp.log"""
import numpy as np, bench as b, lab, time, sys, feats
D=lab.D; F=np.load("F7.npy"); names=open("F7_names.txt").read().split("\n"); ri=D["race_idx"]; nR=D["n_races"]
name=sys.argv[1]; seed=int(name.split("@")[1]) if "@" in name else 0; name0=name; name=name.split("@")[0]; params=dict(feature_fraction=0.2,extra_trees=True,num_threads=4); target=None
def norm(v):
    return v/np.bincount(ri,weights=v,minlength=nR)[ri]
def past_market():
    P=D["P"].astype(float); f={n:i for i,n in enumerate(D["past_fields"])}; col=lambda n:P[:,:,f[n]].copy()
    trial=col("trial")==1; race=lambda n: np.where(trial,np.nan,col(n))
    bsp,sp,run,fs=race("bsp"),race("sp"),race("runners"),race("field_strength")
    mr=-np.log(bsp)+np.log(run); ms=-np.log(sp)+np.log(run); steam=np.log(sp)-np.log(bsp)
    out={}
    for k,A in (("mr",mr),("ms",ms),("steam",steam),("pfs",fs),("mrfs",mr+0.1*fs)):
        out[f"k_{k}_last"]=feats.nanfirst(A); out[f"k_{k}_rw"]=feats.recency(A); out[f"k_{k}_max5"]=feats.firstk(A,5,np.nanmax); out[f"k_{k}_mean3"]=feats.firstk(A,3,np.nanmean)
    cols=[];nm=[]
    for k,v in out.items():
        cols.append(v); nm.append(k)
        a,m,r=feats.relative(v); cols+=[a,m,r]; nm+=[k+"__vmax",k+"__vmean",k+"__rank"]
    return np.column_stack(cols).astype(np.float32), nm
if name.startswith("spblend"):
    a=float(name.split("_")[1]); sp=D["sp"]; qs=b.norm_inv(sp)
    target=norm(np.exp((1-a)*np.log(np.maximum(D["q"],1e-6))+a*np.log(np.maximum(qs,1e-6))))
if name=="pastmkt":
    X,nm=past_market(); F=np.column_stack([F,X]); names=names+nm; np.save("pastmkt.npy",X); open("pastmkt_names.txt","w").write("\n".join(nm))
if name=="leaves31": params.update(num_leaves=31,min_data_in_leaf=60)
if name=="leaves7": params.update(num_leaves=7,min_data_in_leaf=150)
if name=="lr03": params.update(learning_rate=0.03)
if name=="ff01": params.update(feature_fraction=0.1)
t0=time.time()
s,it,bst=lab.valid_score(F,names,target=target,params=params,rounds=10000,seed=seed)
p=b.softmax_races(bst.predict(F,num_iteration=it)); np.save(f"valid_{name0}.npy",p)
open("xp.log","a").write(b.fmt(f"{name0} it{it}",s)+f" {time.time()-t0:.0f}s\n")
