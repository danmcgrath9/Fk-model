import numpy as np, bench as b, lightgbm as lgb, gbm
D=b.load(); p=np.load("p_oof.npy"); ri=D["race_idx"]; nR=D["n_races"]; dates=D["date"]; rd=dates[ri]
res=np.clip(np.log(np.maximum(D["q"],1e-4))-np.log(np.maximum(p,1e-4)),-3,3)
ud=np.unique(rd); byd=[np.where(rd==d)[0] for d in ud]
E=np.load("renc_oof.npy"); cnt=np.bincount(ri,minlength=nR)
cen=lambda v: v-(np.bincount(ri,weights=v,minlength=nR)/cnt)[ri]
L=np.log(np.maximum(p,1e-12)); Lc=L-(np.bincount(ri,weights=L,minlength=nR)/cnt)[ri]
base=np.column_stack([E,np.stack([cen(E[:,j]) for j in range(E.shape[1])],1),Lc,np.log(cnt[ri]),p])
cut="2026-05-06"; dev=np.where(dates<cut)[0]; hold=np.where(dates>=cut)[0]; inner,val=b.split(0.8,dev)
def part(races):
    m=np.isin(ri,races); _,rr=np.unique(ri[m],return_inverse=True); return m,rr,rr.max()+1
def run(X,races_fit,rounds=None,val_races=None,seed=0):
    m,rr,n=part(races_fit)
    P=dict(learning_rate=0.03,num_leaves=7,min_data_in_leaf=200,feature_fraction=0.7,bagging_fraction=0.8,bagging_freq=1,lambda_l2=10,verbose=-1,objective="none",num_threads=4,seed=seed)
    bst=lgb.Booster(params=P,train_set=lgb.Dataset(X[m],init_score=L[m])); f=gbm.make_obj(rr,n,D["q"][m]); best,bi=9,0
    for it in range(1,(rounds or 2000)+1):
        bst.update(fobj=f)
        if val_races is not None and it%25==0:
            s=b.score(b.softmax_races(L+bst.predict(X)),val_races)[0]
            if s<best-1e-5: best,bi=s,it
            elif it-bi>=150: break
    return bst,bi
def evaluate(X,label):
    ks=[]
    for sd in (0,1):
        bst,bi=run(X,inner,val_races=val,seed=sd); bst,_=run(X,dev,rounds=int(bi*1.1),seed=sd)
        ks.append(b.softmax_races(L+bst.predict(X)))
    pp=b.softmax_races(np.mean([np.log(k) for k in ks],0))
    print(b.fmt(f"{label}",b.score(pp,hold)),flush=True); return pp
# --- A: stablemates
tr=D["trainer"].astype(str); key=np.char.add(ri.astype(str),np.char.add("|",tr))
_,inv,cnts=np.unique(key,return_inverse=True,return_counts=True)
nstab=cnts[inv].astype(float)
rank_stab=np.zeros(len(ri)); 
for k in np.where(cnts>1)[0]:
    ix=np.where(inv==k)[0]; o=np.argsort(-p[ix]); rank_stab[ix[o]]=np.arange(1,len(ix)+1)
F7=np.load("F7.npy"); nm=open("F7_names.txt").read().split("\n"); c={n:i for i,n in enumerate(nm)}
jw=np.nan_to_num(F7[:,c["jockeyForm_lastTwelveMonthWinPercentage"]],nan=0)
jrank_stab=np.zeros(len(ri))
for k in np.where(cnts>1)[0]:
    ix=np.where(inv==k)[0]; o=np.argsort(-jw[ix]); jrank_stab[ix[o]]=np.arange(1,len(ix)+1)
A=np.column_stack([nstab,rank_stab,jrank_stab,(rank_stab==1)&(nstab>1),(jrank_stab==1)&(nstab>1)]).astype(float)
# --- B: jockey market-gap: today's jockey vs the horse's last jockey
pj=D["past_jockeys"].astype(str); lastj=np.array([next((x for x in row if x),"") for row in pj])
s={};n={};todayv=np.zeros(len(ri)); lastv=np.zeros(len(ri))
for ix in byd:
    for i in ix:
        j=str(D["jockey"][i]); todayv[i]=s.get(j,0)/(n.get(j,0)+5); lastv[i]=s.get(lastj[i],0)/(n.get(lastj[i],0)+5)
    for i in ix:
        j=str(D["jockey"][i]); s[j]=s.get(j,0)+res[i]; n[j]=n.get(j,0)+1
chg=(lastj!=D["jockey"].astype(str))&(lastj!="")
Bk=np.column_stack([todayv-lastv,chg.astype(float),np.where(chg,todayv-lastv,0)])
# --- C: horse residual second-last and trend
H=D["horse_id"].astype(str); hist={};second=np.zeros(len(ri)); nruns=np.zeros(len(ri))
for ix in byd:
    for i in ix:
        h=hist.get(H[i],[]); second[i]=h[-2] if len(h)>=2 else 0; nruns[i]=len(h)
    for i in ix: hist.setdefault(H[i],[]).append(res[i])
C=np.column_stack([second,nruns,E[:,0]-second])
evaluate(base,"stage-2 base (2 seeds)")
evaluate(np.column_stack([base,A]),"+ stablemates")
evaluate(np.column_stack([base,Bk,cen(Bk[:,0])]),"+ jockey gap vs last jockey")
evaluate(np.column_stack([base,C]),"+ horse second-last gap, runs, trend")
evaluate(np.column_stack([base,A,Bk,C]),"+ all three")
