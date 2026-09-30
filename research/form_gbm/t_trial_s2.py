"""Trial form for horses with little or no race form: does it sharpen stage 2 (with sections)?"""
import numpy as np, bench as b, stage2
src=open("t_s2feat.py").read().split("evaluate(base,")[0]
src=src.replace('p=np.load("p_oof.npy")','p=np.load("p_oof_blend3.npy")').replace('E=np.load("renc_oof.npy")','E=stage2.encodings(rd,D["horse_id"],D["trainer"],D["jockey"],D["sire"],D["track"][ri],res)')
exec(src)
SEC=stage2.sections(np.load("S_hist.npy"),np.load("S_fields.npy",allow_pickle=True),D["P"],D["past_fields"],ri,nR)
X2=np.column_stack([base,A,Bk,C,SEC])
t_P=D["P"].astype(float); t_f={n:i for i,n in enumerate(D["past_fields"])}
t_tr=t_P[:,:,t_f["trial"]]==1; t_days=t_P[:,:,t_f["days_before"]]; t_fin=t_P[:,:,t_f["finish"]]; t_run=t_P[:,:,t_f["runners"]]
t_real=~t_tr & np.isfinite(t_fin) & (t_fin>0)
# collapse duplicate trial records (same days_before)
t_seen=np.zeros_like(t_tr)
for t_s in range(t_P.shape[1]):
    t_dup=np.zeros(len(ri),bool)
    for t_t in range(t_s): t_dup|= t_tr[:,t_t]&(t_days[:,t_t]==t_days[:,t_s])
    t_seen[:,t_s]=t_tr[:,t_s]&np.isfinite(t_fin[:,t_s])&(t_fin[:,t_s]>0)&~t_dup
nraces=t_real.sum(1); ntr=t_seen.sum(1)
twins=(t_seen&(t_fin==1)).sum(1); tplace=(t_seen&(t_fin<=3)).sum(1)
# last three trials
t_rank=np.cumsum(t_seen,1); t_last3=t_seen&(t_rank<=3)
t3wins=(t_last3&(t_fin==1)).sum(1)
t_j=np.argmax(t_seen,1); t_ar=np.arange(len(ri)); t_has=t_seen[t_ar,t_j]
lfin=np.where(t_has,t_fin[t_ar,t_j],np.nan); lrel=np.where(t_has,(t_fin[t_ar,t_j]-1)/np.maximum(t_run[t_ar,t_j]-1,1),np.nan); ldays=np.where(t_has,t_days[t_ar,t_j],np.nan)
lrun=np.where(t_has,t_run[t_ar,t_j],np.nan)
few=(nraces<=1).astype(float)
TR=np.column_stack([nraces,ntr,twins,tplace,t3wins,lfin,lrel,ldays,lrun,few*twins,few*t3wins,few*np.nan_to_num(1-lrel,nan=0.5),twins/np.maximum(ntr,1)])
evaluate(X2,"stage-2 v3 (sections)")
evaluate(np.column_stack([X2,TR]),"+ trial form")
