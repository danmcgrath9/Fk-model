exec(open("t_s2feat.py").read().split("evaluate(base,")[0])
X1=np.column_stack([base,A,Bk,C])
# time-forward stage-2 predictions: for each month from 2026-01, fit on races before the month, predict the month
months=sorted(set(str(d)[:7] for d in dates)); p2=p.copy()
for mth in months:
    if mth<"2026-01": continue
    fit_r=np.where(dates<mth+"-01")[0]; tgt=np.where(np.array([str(d)[:7] for d in dates])==mth)[0]
    inn,vl=b.split(0.8,fit_r); bst,bi=run(X1,inn,val_races=vl); bst,_=run(X1,fit_r,rounds=int(bi*1.1))
    m=np.isin(ri,tgt); pr=b.softmax_races(L+bst.predict(X1)); p2[m]=pr[m]; print(mth,bi,flush=True)
np.save("p_s2_forward.npy",p2)
res2=np.clip(np.log(np.maximum(D["q"],1e-4))-np.log(np.maximum(p2,1e-4)),-3,3)
def enc(key,r,k=10,last=False):
    s={};n={};out=np.zeros(len(ri))
    for ix in byd:
        for i in ix:
            if key[i] in s: out[i]=s[key[i]]/(n[key[i]]+k)
        for i in ix:
            if last: s[key[i]]=r[i]; n[key[i]]=1
            else: s[key[i]]=s.get(key[i],0)+r[i]; n[key[i]]=n.get(key[i],0)+1
    return out
E2=np.column_stack([enc(H,res2,1,True),enc(H,res2,5),enc(tr,res2,5),enc(D["jockey"].astype(str),res2,5)])
E2=np.column_stack([E2,np.stack([cen(E2[:,j]) for j in range(4)],1)])
# stage-3 on top of the forward stage-2 price, only races from 2026-01 have a forward price: fit on 2026-01..05-05, test hold
L2=np.log(np.maximum(p2,1e-12)); L2c=cen(L2)
X3=np.column_stack([E2,L2c,np.log(cnt[ri]),p2])
dev3=np.where((dates>="2026-01")&(dates<cut))[0]; inn3,val3=b.split(0.8,dev3)
Lsave=L; L=L2
bst,bi=run(X3,inn3,val_races=val3); bst,_=run(X3,dev3,rounds=int(bi*1.1)); p3=b.softmax_races(L2+bst.predict(X3))
print(b.fmt("hold forward stage-2",b.score(p2,hold))); print(b.fmt(f"hold stage-3 (r{bi})",b.score(p3,hold)))
