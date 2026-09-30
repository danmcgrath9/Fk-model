"""second stage v3: v2 plus Form King section splits (stage2.sections). python stage2c_train.py P_OOF ROUNDS"""
import numpy as np, bench as b, lightgbm as lgb, gbm, stage2, sys
PF,R=sys.argv[1],int(sys.argv[2])
D=b.load(); p=np.load(PF); ri=D["race_idx"]; nR=D["n_races"]; rd=D["date"][ri]
res=np.clip(np.log(np.maximum(D["q"],1e-4))-np.log(np.maximum(p,1e-4)),-3,3)
jw=np.nan_to_num(D["X"][:,D["colidx"]["jockeyForm_lastTwelveMonthWinPercentage"]].astype(float),nan=0)
lastj=np.array([next((x for x in row if x),"") for row in D["past_jockeys"].astype(str)])
E=stage2.encodings(rd,D["horse_id"],D["trainer"],D["jockey"],D["sire"],D["track"][ri],res)
A,Bk,C=stage2.extras(rd,ri,D["horse_id"],D["trainer"],D["jockey"],lastj,p,jw,res)
X,L=stage2.design(E,p,ri,nR); SEC=stage2.sections(np.load("S_hist.npy"),np.load("S_fields.npy",allow_pickle=True),D["P"],D["past_fields"],ri,nR); X=np.column_stack([X,A,Bk,C,SEC])
P=dict(learning_rate=0.03,num_leaves=7,min_data_in_leaf=200,feature_fraction=0.7,bagging_fraction=0.8,bagging_freq=1,lambda_l2=10,verbose=-1,objective="none",num_threads=4)
f=gbm.make_obj(ri,nR,D["q"])
for s in range(3):
    P["seed"]=s; bst=lgb.Booster(params=P,train_set=lgb.Dataset(X,init_score=L))
    for _ in range(R): bst.update(fobj=f)
    bst.save_model(f"stage2c_{s}.txt")
print("saved",X.shape)
