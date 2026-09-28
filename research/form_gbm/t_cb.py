import numpy as np, bench as b, lab, time
from catboost import CatBoost, Pool
D=lab.D; F=np.load("F7.npy"); names=open("F7_names.txt").read().split("\n"); ri=D["race_idx"]
Fa=lab.augmented(F,names,seed=1)
mi=np.isin(ri,lab.INNER); mv=np.isin(ri,lab.VALID)
X=np.vstack([F[mi],Fa[mi]]); y=np.concatenate([D["q"][mi]]*2); g=np.concatenate([ri[mi],ri[mi]+D["n_races"]])
o=np.argsort(g,kind="stable"); X,y,g=X[o],y[o],g[o]
tr=Pool(X,y,group_id=g); va=Pool(F[mv],D["q"][mv],group_id=ri[mv])
t0=time.time()
m=CatBoost(dict(loss_function="QuerySoftMax",iterations=4000,learning_rate=0.08,depth=6,l2_leaf_reg=10,rsm=0.2,thread_count=4,random_seed=0,od_type="Iter",od_wait=200,verbose=500))
m.fit(tr,eval_set=va,use_best_model=True)
s=m.predict(F); p=b.softmax_races(s); np.save("valid_cb.npy",p)
print(b.fmt(f"catboost it{m.get_best_iteration()}",b.score(p,lab.VALID)),f"{time.time()-t0:.0f}s")
base=np.load("valid_base_sm.npy")
for w in (0.2,0.35,0.5):
    bl=b.softmax_races((1-w)*np.log(base)+w*np.log(np.maximum(p,1e-12))); print(b.fmt(f"trees+cb {w:.0%}",b.score(bl,lab.VALID)))
