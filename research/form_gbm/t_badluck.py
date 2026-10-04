"""Benter's two adjustments we lack: (1) past barrier: each past run's vsClass adjusted for the barrier it drew, with the
barrier effect learned from training races only; (2) bad luck: runs where the horse closed far faster than its overall
rating implies (fastest late section vs class much better than vsClass), the pros' 'unlucky, too far back' read."""
import numpy as np, bench as b, stage2
src=open("t_research.py").read().split("# 1. Accardi")[0]
exec(src)
vc=np.where(race,P[:,:,f["vsClass"]],np.nan); bar=P[:,:,f["barrier"]]; nrun=P[:,:,f["runners"]]; days=P[:,:,f["days_before"]]
bsh=np.where(race,(bar-1)/np.maximum(nrun-1,1),np.nan)
# barrier effect: mean vsClass by barrier-share decile, from past runs of TRAINING-race runners only
trm=np.isin(ri,dev)
dec=np.clip((bsh*10).astype(int),0,9)
eff=np.zeros(10)
for d_ in range(10):
    m=trm[:,None]&race&(dec==d_)&np.isfinite(vc); eff[d_]=np.nanmean(vc[m]) if m.any() else 0
eff-=np.nanmean(eff); print("barrier effect by decile (lengths vs class):",eff.round(2))
adj=vc-eff[dec]                                   # performance with the draw taken out
w=np.where(race,0.8**np.arange(P.shape[1])[None,:],0)    # recency weights
def wmean(v):
    ok=np.isfinite(v)&(w>0); return np.where(ok.sum(1)>0,np.nansum(np.where(ok,v*w,0),1)/np.maximum((w*ok).sum(1),1e-9),np.nan)
A1=wmean(adj); A0=wmean(vc)
# bad luck: late section (6-F vsClass) minus overall vsClass, last run and best of last three
l6=np.where(race,S[:,:,SF["6-F|vsClass"]],np.nan); gap6=l6-vc
jr=np.argmax(race,1); okr=race[ar,jr]
last_gap=np.where(okr,gap6[ar,jr],np.nan); rk=np.cumsum(race,1); b3=np.where((race&(rk<=3)&np.isfinite(gap6)).any(1),np.nanmax(np.where(race&(rk<=3),gap6,-99),1),np.nan); b3=np.where(b3<-90,np.nan,b3)
pos8=np.where(race,P[:,:,f["pos800"]]/np.maximum(nrun,1),np.nan); last_back=np.where(okr,pos8[ar,jr],np.nan)
unlucky=np.nan_to_num(last_gap,nan=0)*(np.nan_to_num(last_back,nan=0)>=0.6)     # closed hard from the back
BL=np.column_stack([np.nan_to_num(A1-A0,nan=0),np.nan_to_num(A1,nan=0),np.nan_to_num(last_gap,nan=0),np.nan_to_num(b3,nan=0),unlucky,rrel(np.nan_to_num(A1,nan=0)),rrel(unlucky)])
np.save("G_badluck.npy",BL)
evaluate(V4,"live (blend9 + stage-2 v4)")
evaluate(np.column_stack([V4,BL[:,[0,1,5]]]),"live + past-barrier adjustment")
evaluate(np.column_stack([V4,BL[:,[2,3,4,6]]]),"live + bad-luck (closed from the back)")
evaluate(np.column_stack([V4,BL]),"live + both")
