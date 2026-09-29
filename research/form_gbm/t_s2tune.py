import numpy as np, bench as b, stage2
src=open("t_s2feat.py").read().split("evaluate(base,")[0]
src=src.replace('p=np.load("p_oof.npy")','p=np.load("p_oof_blend.npy")').replace('E=np.load("renc_oof.npy")','E=stage2.encodings(rd,D["horse_id"],D["trainer"],D["jockey"],D["sire"],D["track"][ri],res)').replace("num_threads=4","num_threads=2")
exec(src)
X=np.column_stack([base,A,Bk,C])
import lightgbm as lgb, gbm
def run2(X,races_fit,P2,rounds=None,val_races=None,seed=0):
    m,rr,n=part(races_fit)
    P=dict(learning_rate=0.03,num_leaves=7,min_data_in_leaf=200,feature_fraction=0.7,bagging_fraction=0.8,bagging_freq=1,lambda_l2=10,verbose=-1,objective="none",num_threads=2,seed=seed); P.update(P2)
    bst=lgb.Booster(params=P,train_set=lgb.Dataset(X[m],init_score=L[m])); f=gbm.make_obj(rr,n,D["q"][m]); best,bi=9,0
    for it in range(1,(rounds or 3000)+1):
        bst.update(fobj=f)
        if val_races is not None and it%25==0:
            s=b.score(b.softmax_races(L+bst.predict(X)),val_races)[0]
            if s<best-1e-5: best,bi=s,it
            elif it-bi>=150: break
    return bst,bi
for P2 in (dict(),dict(num_leaves=15,min_data_in_leaf=100),dict(num_leaves=3,min_data_in_leaf=300),dict(learning_rate=0.015),dict(lambda_l2=50),dict(feature_fraction=0.4)):
    ks=[]
    for sd in (0,1):
        bst,bi=run2(X,inner,P2,val_races=val,seed=sd); bst,_=run2(X,dev,P2,rounds=int(bi*1.1),seed=sd); ks.append(np.log(b.softmax_races(L+bst.predict(X))))
    print(b.fmt(f"{P2} r{bi}",b.score(b.softmax_races(np.mean(ks,0)),hold)),flush=True)
