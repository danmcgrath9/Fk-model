"""out-of-fold network and CatBoost prices over the same 5 date blocks as p_oof (trees)"""
import numpy as np, bench as b, lab, nn, time, sys, torch
from catboost import CatBoost, Pool
torch.set_num_threads(4)
D=lab.D; F=np.load("F7.npy"); names=open("F7_names.txt").read().split("\n"); ri=lab.ri0; nR=D["n_races"]
order=np.argsort(D["date"],kind="stable"); blocks=np.array_split(order,5)
what=sys.argv[1]
oof=np.zeros(len(ri))
for k,blk in enumerate(blocks):
    t0=time.time(); train=np.sort(np.concatenate([bb for j,bb in enumerate(blocks) if j!=k])); mb=np.isin(ri,blk)
    if what=="nn":
        logs=[np.log(np.maximum(nn.fit(F,names,train,None,seed=10*k+s,fixed_epochs=14)[0],1e-12)) for s in range(3)]
        oof[mb]=np.log(b.softmax_races(np.mean(logs,0)))[mb]
    else:
        Fa=lab.augmented(F,names,seed=k+30); mt=np.isin(ri,train)
        X=np.vstack([F[mt],Fa[mt]]); y=np.concatenate([D["q"][mt]]*2); g=np.concatenate([ri[mt],ri[mt]+nR]); o=np.argsort(g,kind="stable")
        m=CatBoost(dict(loss_function="QuerySoftMax",iterations=2900,learning_rate=0.08,depth=6,l2_leaf_reg=10,rsm=0.2,thread_count=4,random_seed=k,verbose=0))
        m.fit(Pool(X[o],y[o],group_id=g[o])); oof[mb]=np.log(b.softmax_races(m.predict(F)))[mb]
    print(what,k,f"{time.time()-t0:.0f}s",flush=True)
p=b.softmax_races(oof); np.save(f"p_oof_{what}.npy",p); print(b.fmt(f"{what} OOF all",b.score(p,np.arange(nR))))
