"""Benter DP6A: distance preference as a standardised slope of past residuals (vsClass) on distance similarity; plus the
two features that moved the holdout (travel, collateral), alone and together."""
import numpy as np, bench as b, stage2
src=open("t_research.py").read().split("# 1. Accardi")[0]
exec(src)
vc=np.where(race,P[:,:,f["vsClass"]],np.nan); pd_=np.where(race,P[:,:,f["distance"]],np.nan); today=D["distance"][ri].astype(float)
sim=-np.abs(np.log(np.maximum(pd_,100))-np.log(np.maximum(today,100))[:,None])    # 0 = same trip, more negative = further away
z=np.zeros(n); slope=np.zeros(n); cnt=np.zeros(n)
for k in range(n):
    m=np.isfinite(vc[k])&np.isfinite(sim[k])
    if m.sum()<4: continue
    x=sim[k,m]; y=vc[k,m]
    if x.std()<1e-6: continue
    A=np.column_stack([np.ones(m.sum()),x]); beta,res,_,_=np.linalg.lstsq(A,y,rcond=None)
    resid=y-A@beta; s2=(resid**2).sum()/max(m.sum()-2,1); se=np.sqrt(s2/((x-x.mean())**2).sum()) if ((x-x.mean())**2).sum()>0 else np.nan
    slope[k]=beta[1]; z[k]=beta[1]/se if se and np.isfinite(se) and se>0 else 0; cnt[k]=m.sum()
z=np.clip(z,-4,4)
# a positive slope means it runs better the closer the trip is to today's: preference for today's distance
DP=np.column_stack([z,slope*(cnt>=6),cnt,rrel(z)])
GC=np.load("G_collateral.npy"); GT=np.load("G_travel.npy")
evaluate(V4,"live (blend9 + stage-2 v4)")
evaluate(np.column_stack([V4,DP]),"live + Benter distance preference (z)")
evaluate(np.column_stack([V4,GT,GC]),"live + travel + collateral")
evaluate(np.column_stack([V4,GT,GC,DP]),"live + travel + collateral + distance pref")
