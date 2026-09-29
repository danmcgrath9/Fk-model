import numpy as np, bench as b, lab
from catboost import CatBoost, Pool
D=lab.D; F=np.load("F7.npy"); names=open("F7_names.txt").read().split("\n"); ri=lab.ri0; nR=D["n_races"]
Fa=lab.augmented(F,names,seed=31); X=np.vstack([F,Fa]); y=np.concatenate([D["q"]]*2); g=np.concatenate([ri,ri+nR]); o=np.argsort(g,kind="stable")
m=CatBoost(dict(loss_function="QuerySoftMax",iterations=3200,learning_rate=0.08,depth=6,l2_leaf_reg=10,rsm=0.2,thread_count=3,random_seed=0,verbose=0))
m.fit(Pool(X[o],y[o],group_id=g[o])); m.save_model("cb_all.cbm"); print("saved")
