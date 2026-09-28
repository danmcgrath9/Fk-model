import numpy as np, bench as b
exec(open("t_drift_enc.py").read().split("drift=")[0])
exec("def part"+open("t_drift_enc.py").read().split("def part")[1].split("for nm,X")[0])
F=np.load("F7.npy"); nm_=open("F7_names.txt").read().split("\n"); c={n:i for i,n in enumerate(nm_)}
res=np.clip(np.log(np.maximum(D["q"],1e-4))-np.log(np.maximum(p,1e-4)),-3,3)
S=lambda a:a.astype(str)
tr_,jo,ho=S(D["trainer"]),S(D["jockey"]),S(D["horse_id"]); trk=S(D["track"][ri]); dist=S((D["distance"][ri]//200)*200)
fu=np.where(np.nan_to_num(F[:,c["daysSinceLastRace"]],nan=999)>=60,"FU","RU")
new={"jockey_trainer":np.char.add(jo,tr_),"horse_track":np.char.add(ho,trk),"horse_dist":np.char.add(ho,dist),"trainer_firstup":np.char.add(tr_,fu)}
Xn=np.stack([enc(v,res,10) for v in new.values()],1); print("encoded",flush=True)
E=np.load("renc_oof.npy"); cnt=np.bincount(ri,minlength=nR)
cen=lambda v: v-(np.bincount(ri,weights=v,minlength=nR)/cnt)[ri]
L=np.log(np.maximum(p,1e-12)); Lc=L-(np.bincount(ri,weights=L,minlength=nR)/cnt)[ri]
base=np.column_stack([E,np.stack([cen(E[:,j]) for j in range(E.shape[1])],1),Lc,np.log(cnt[ri]),p])
cut="2026-05-06"; dev=np.where(dates<cut)[0]; hold=np.where(dates>=cut)[0]; inner,val=b.split(0.8,dev)
X=np.column_stack([base,Xn,np.stack([cen(Xn[:,j]) for j in range(Xn.shape[1])],1)])
bst,bi=run(X,inner,val_races=val); bst,_=run(X,dev,rounds=int(bi*1.1))
print(b.fmt(f"hold stage-2 + 4 more encodings r{bi}",b.score(b.softmax_races(L+bst.predict(X)),hold)))
