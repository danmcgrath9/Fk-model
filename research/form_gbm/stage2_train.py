import numpy as np, bench as b, lightgbm as lgb, gbm, stage2
D=b.load(); p=np.load("p_oof.npy"); ri=D["race_idx"]; nR=D["n_races"]; rd=D["date"][ri]
res=np.clip(np.log(np.maximum(D["q"],1e-4))-np.log(np.maximum(p,1e-4)),-3,3)
E=stage2.encodings(rd,D["horse_id"],D["trainer"],D["jockey"],D["sire"],D["track"][ri],res)
old=np.load("renc_oof.npy"); print("matches the tested encodings:",np.allclose(E,old))
X,L=stage2.design(E,p,ri,nR)
P=dict(learning_rate=0.03,num_leaves=7,min_data_in_leaf=200,feature_fraction=0.7,bagging_fraction=0.8,bagging_freq=1,lambda_l2=10,verbose=-1,objective="none",num_threads=4)
f=gbm.make_obj(ri,nR,D["q"])
for s in range(3):
    P["seed"]=s; bst=lgb.Booster(params=P,train_set=lgb.Dataset(X,init_score=L))
    for _ in range(170): bst.update(fobj=f)
    bst.save_model(f"stage2_{s}.txt")
print("saved")
