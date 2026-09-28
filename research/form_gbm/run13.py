import numpy as np, bench as b, lab
D=lab.D; F=np.load("F7.npy"); names=open("F7_names.txt").read().split("\n")
def codes(arr, minc=30):
    u,inv,cnt=np.unique(arr,return_inverse=True,return_counts=True)
    keep=(cnt[inv]>=minc)&(arr!="")
    rank=np.cumsum(cnt>=minc)-1
    return np.where(keep, rank[inv], np.nan).astype(np.float32)
ri=D["race_idx"]
cats={"cat_jockey":D["jockey"],"cat_trainer":D["trainer"],"cat_sire":D["sire"],"cat_damsire":D["dam_sire"],"cat_track":D["track"][ri],"cat_loc":D["training_location"]}
C=np.stack([codes(v) for v in cats.values()],1)
for k,v in zip(cats,C.T): print(k, int(np.nanmax(v))+1, "categories")
Fc=np.hstack([F,C]); nc=names+list(cats); cidx=list(range(F.shape[1],Fc.shape[1]))
np.save("F8c.npy",Fc); open("F8c_names.txt","w").write("\n".join(nc))
base=dict(feature_fraction=0.2, extra_trees=True)
s,it,_=lab.valid_score(F,names,params=base,rounds=8000,seed=0); print(b.fmt(f"baseline F7 ({it})",s),flush=True)
for lab_,prm in (("+ categories (cat_smooth 20)",dict(base,cat_smooth=20,min_data_per_group=50)),("+ categories (cat_smooth 50, l2 20)",dict(base,cat_smooth=50,cat_l2=20,min_data_per_group=100))):
    s,it,_=lab.valid_score(Fc,nc,params=prm,rounds=8000,seed=0,cat_idx=cidx); print(b.fmt(f"{lab_} ({it})",s),flush=True)
