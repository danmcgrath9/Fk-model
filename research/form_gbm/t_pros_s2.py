"""Round-2 pro ideas as stage-2 inputs: bounce, second-up, weight change, pace count, lone speed, backing up."""
import numpy as np, bench as b, stage2
src=open("t_research.py").read().split("# 1. Accardi")[0]
exec(src)
c=D["colidx"]; X=D["X"].astype(float)
fin=P[:,:,f["finish"]]; rat=P[:,:,f["rating"]]; wt=P[:,:,f["weight"]]; mg=P[:,:,f["margin"]]; prep=P[:,:,f["prep"]]; days=P[:,:,f["days_before"]]
jr=np.argmax(race,1); okr=race[ar,jr]; ld=lambda v: np.where(okr,v[ar,jr],np.nan)
lr=ld(rat); later=race.copy(); later[ar,jr]=False
prior_best=np.where(later.any(1),np.nanmax(np.where(later,rat,-999),1),np.nan); prior_best=np.where(prior_best<-900,np.nan,prior_best)
peak=lr-prior_best
gap=ld(days); secup=(ld(prep)==1).astype(float); good1=secup*((ld(fin)<=3)|(ld(mg)<=2)).astype(float)
wch=X[:,c["weight"]]-ld(wt)
es=X[:,c["sm_early_speed"]]; ssh=X[:,c["raw_settle_share"]]
nfast=np.bincount(ri,weights=np.nan_to_num(es,nan=0)>=6.5,minlength=nR)[ri].astype(float)
mx=np.full(nR,-np.inf); np.maximum.at(mx,ri,np.nan_to_num(es,nan=-9)); es2=np.where(np.nan_to_num(es,nan=-9)==mx[ri],-9,np.nan_to_num(es,nan=-9)); mx2=np.full(nR,-np.inf); np.maximum.at(mx2,ri,es2)
lone=((np.nan_to_num(es,nan=-9)==mx[ri])&(mx[ri]-mx2[ri]>=1)).astype(float)
G=np.column_stack([peak,(peak>=3).astype(float),np.nan_to_num(peak,nan=0)*(gap<=21),good1,wch,nfast,nfast*ssh,lone,(gap<=7).astype(float),rrel(np.nan_to_num(peak,nan=0))])
evaluate(V4,"live (blend9 + stage-2 v4)")
evaluate(np.column_stack([V4,G]),"live + round-2 pro inputs")
evaluate(np.column_stack([V4,G[:,[0,1,2,9]]]),"live + bounce only")
