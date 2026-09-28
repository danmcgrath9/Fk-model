import numpy as np, bench as b, lightgbm as lgb
D=b.load(); p=np.load("p_oof.npy"); ri=D["race_idx"]; F=np.load("F7.npy"); names=open("F7_names.txt").read().split("\n")
op=D["open"]; bsp=D["bsp"]; won=D["won"]==1
ok=np.isfinite(op)&(op>1)&np.isfinite(bsp)&(bsp>1); fair=1/np.maximum(p,1e-9); ev=p*op-1
X=np.hstack([F, np.log(p)[:,None], np.log(np.where(op>1,op,np.nan))[:,None], ev[:,None], (np.log(fair)-np.log(np.where(op>1,op,np.nan)))[:,None]]).astype(np.float32)
xn=names+["model_logp","log_open","model_value","model_vs_open"]
y=np.log(bsp/op)   # + = drifted
order=np.argsort(D["date"],kind="stable"); blocks=np.array_split(order,5)
pred=np.full(len(ri),np.nan); gains=np.zeros(X.shape[1])
prm=dict(objective="l2",learning_rate=0.03,num_leaves=31,min_data_in_leaf=100,feature_fraction=0.3,bagging_fraction=0.8,bagging_freq=1,lambda_l2=10,verbose=-1,num_threads=4)
for k,blk in enumerate(blocks):
    tr=np.isin(ri,np.concatenate([bb for j,bb in enumerate(blocks) if j!=k]))&ok; te=np.isin(ri,blk)
    m=lgb.train(prm,lgb.Dataset(X[tr],y[tr]),1500)
    pred[te]=m.predict(X[te]); gains+=m.feature_importance("gain")
np.save("drift_pred.npy",pred)
val=ok&(fair<50)&(ev>0.2)&(op<3*fair)
print("drift predictor, out of sample: correlation with the actual move", np.corrcoef(pred[ok],y[ok])[0,1].round(3), "| among value bets", np.corrcoef(pred[val],y[val])[0,1].round(3))
o=np.argsort(-gains); tot=gains.sum()
print("what predicts a drift (share of the model's learning):"); print(", ".join(f"{xn[i]} {gains[i]/tot:.0%}" for i in o[:20]))
def roi(s): n=s.sum(); return n,(op[s&won].sum()-n)/n, won[s].sum()/p[s].sum(), np.std(np.where(won[s],op[s],0)-1)/np.sqrt(n)
print("\nvalue bets (20c+ at open), cut by predicted drift:")
q=np.quantile(pred[val],[0.2,0.4,0.6,0.8])
for lab,s in (("predicted to firm most (bottom fifth)",val&(pred<q[0])),("2nd fifth",val&(pred>=q[0])&(pred<q[1])),("middle fifth",val&(pred>=q[1])&(pred<q[2])),("4th fifth",val&(pred>=q[2])&(pred<q[3])),("predicted to drift most (top fifth)",val&(pred>=q[3]))):
    n,r,ae,se=roi(s); dr=((bsp/op)[s]>=1.25).mean(); print(f"  {lab:40s} bets {n:5d}  drifted 25%+ {dr:4.0%}  actual/model {ae:.2f}  return at open {r:+.1%} ±{se:.0%}")
for cut in (0.8,0.6):
    s=val&(pred<np.quantile(pred[val],cut)); n,r,ae,se=roi(s); print(f"  skip the top {1-cut:.0%} predicted drifters: bets {n} return at open {r:+.1%} ±{se:.0%}")
n,r,ae,se=roi(val); print(f"  all value bets: {n} return at open {r:+.1%} ±{se:.0%}")
