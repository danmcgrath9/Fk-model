import numpy as np, bench as b, lab, nn, lightgbm as lgb
D=lab.D; F=np.load("F7.npy"); names=open("F7_names.txt").read().split("\n")
sm=b.softmax_races(np.mean([np.log(b.softmax_races(lgb.Booster(model_file=f"f2_sm{s}.txt").predict(F))) for s in range(5)],0))
rg=b.softmax_races(np.mean([np.log(b.softmax_races(lgb.Booster(model_file=f"f2_rg{s}.txt").predict(F))) for s in range(5)],0))
nets=[]
for s in range(5):
    _,ep=nn.fit(F,names,lab.INNER,lab.VALID,epochs=80,seed=s)
    p,_=nn.fit(F,names,lab.TR,None,seed=s,fixed_epochs=max(1,int(round(ep*1.2)))); nets.append(np.log(np.maximum(p,1e-12))); print("net",s,"epochs",int(round(ep*1.2)),flush=True)
pn=b.softmax_races(np.mean(nets,0)); np.save("te_nn.npy",pn)
old=np.load("p_final2.npy"); new=b.softmax_races(0.4*np.log(sm)+0.25*np.log(rg)+0.35*np.log(pn)); np.save("p_final3.npy",new)
te,pre=lab.TE,D["pre_jump"]
for label,rs in (("all 1,093 unseen",te),("78 live-pulled",te[pre[te]])):
    print("---",label)
    for n,q in (("opening market",D["mkt"]),("previous: trees + regression",old),("network alone",pn),("new: trees + regression + network",new)): print(b.fmt(n,b.score(q,rs)))
