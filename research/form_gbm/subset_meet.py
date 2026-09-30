import numpy as np, sys
date,track,outp=sys.argv[1:4]
N=dict(np.load("ds/model_ds_sec.npz",allow_pickle=True)); ri=N["race_idx"]; nR=len(N["race_id"])
races=[r for r in range(nR) if str(N["date"][r])==date and str(N["track"][r])==track]
keep=np.isin(ri,races); newidx={r:i for i,r in enumerate(races)}; out={}
for k,v in N.items():
    if hasattr(v,"shape") and v.shape[:1]==(len(ri),) and k not in ("cols","past_fields","sec_fields"): out[k]=v[keep]
    elif hasattr(v,"shape") and v.shape[:1]==(nR,): out[k]=v[races]
    else: out[k]=v
out["race_idx"]=np.array([newidx[r] for r in ri[keep]],dtype=np.int32); np.savez(outp,**out); print(len(races),"races",keep.sum(),"runners")
