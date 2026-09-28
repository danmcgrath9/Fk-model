import numpy as np, bench as b, lab, nn, lightgbm as lgb
D=lab.D; F=np.load("F7.npy"); names=open("F7_names.txt").read().split("\n"); ri=lab.ri0; nR=D["n_races"]
# network variants, 3 seeds each averaged
res={}
for lab_,kw in (("h128 d0.2",dict(h=128,drop=0.2)),("h256 d0.3",dict(h=256,drop=0.3)),("h64 d0.1 wd1e-3",dict(h=64,drop=0.1,wd=1e-3))):
    ps=[nn.fit(F,names,lab.INNER,lab.VALID,epochs=80,seed=s,**kw)[0] for s in range(3)]
    p=b.softmax_races(np.mean([np.log(np.maximum(x,1e-12)) for x in ps],0)); res[lab_]=p
    print(b.fmt(f"net {lab_}, 3 seeds",b.score(p,lab.VALID)),flush=True)
best_nn=min(res,key=lambda k:b.score(res[k],lab.VALID)[0]); p_nn=res[best_nn]; np.save("valid_nn3.npy",p_nn)
s,it,bst=lab.valid_score(F,names,params=dict(feature_fraction=0.2,extra_trees=True),rounds=8000,seed=0); p_sm=b.softmax_races(bst.predict(F,num_iteration=it))
lq=np.log(D["q"]); mean=np.bincount(ri,weights=lq,minlength=nR)/np.bincount(ri,minlength=nR); y=lq-mean[ri]
Fa=lab.augmented(F,names,seed=2); mi,mv=np.isin(ri,lab.INNER),np.isin(ri,lab.VALID)
rp=dict(objective="l2",learning_rate=0.05,num_leaves=31,min_data_in_leaf=100,feature_fraction=0.2,extra_trees=True,bagging_fraction=0.8,bagging_freq=1,lambda_l2=10,verbose=-1,num_threads=4)
rg=lgb.train(rp,lgb.Dataset(np.vstack([F[mi],Fa[mi]]),np.concatenate([y[mi],y[mi]])),6000,valid_sets=[lgb.Dataset(F[mv],y[mv])],callbacks=[lgb.early_stopping(200,verbose=False)])
p_rg=b.softmax_races(rg.predict(F,num_iteration=rg.best_iteration))
L=[np.log(p_sm),np.log(p_rg),np.log(np.maximum(p_nn,1e-12))]
print("best net:",best_nn)
for w in ((0.7,0.3,0),(0.5,0.2,0.3),(0.45,0.15,0.4),(0.4,0.25,0.35),(0.55,0.1,0.35),(0.35,0.3,0.35)):
    bl=b.softmax_races(sum(wi*li for wi,li in zip(w,L))); print(b.fmt(f"trees {w[0]} / regression {w[1]} / net {w[2]}",b.score(bl,lab.VALID)))
