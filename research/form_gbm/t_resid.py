"""Where is the model far from BSP? KL by segment, model vs opening market, on the holdout (Benter: study the residuals)."""
import numpy as np, bench as b
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; dates=D["date"]; q=D["q"]; mkt=D["mkt"]; p=np.load("pp_hold_v4.npy")
P=D["P"].astype(float); f={str(n):i for i,n in enumerate(D["past_fields"])}
real=~(P[:,:,f["trial"]]==1)&np.isfinite(P[:,:,f["finish"]])&(P[:,:,f["finish"]]>0); nst=real.sum(1); fs=nst==0
hold=np.where(dates>="2026-05-06")[0]; hm=np.isin(ri,hold)
okm=np.bincount(ri,weights=(~np.isfinite(mkt)).astype(float),minlength=nR)==0
def kl(pr,races):
    m=np.isin(ri,races)&np.isfinite(pr); return np.where(q[m]>0,q[m]*np.log(np.maximum(q[m],1e-300)/np.maximum(pr[m],1e-12)),0).sum()/len(races)
def seg(nm,racemask):
    r=np.where(racemask&np.isin(np.arange(nR),hold)&okm)[0]
    if len(r)<30: return
    print(f"{nm:36s} races {len(r):5d}  model {kl(p,r):.4f}  open {kl(mkt,r):.4f}  model/open {kl(p,r)/kl(mkt,r):.2f}")
fld=np.bincount(ri,minlength=nR); dist=D["distance"]; go=D["going"]; lws=D["lws"] if "lws" in D else None
nfs=np.bincount(ri,weights=fs.astype(float),minlength=nR); minst=np.full(nR,99); np.minimum.at(minst,ri,nst); medst=np.array([np.median(nst[ri==r]) for r in range(nR)])
print("by field size"); [seg(f"  {lo}-{hi} runners",(fld>=lo)&(fld<=hi)) for lo,hi in ((4,7),(8,10),(11,13),(14,24))]
print("by distance"); [seg(f"  {lo}-{hi}m",(dist>=lo)&(dist<hi)) for lo,hi in ((900,1200),(1200,1500),(1500,1900),(1900,4000))]
print("by going"); [seg(f"  going {g}",go==g) for g in (1,2,3,4)]
print("by first-starters in the race"); [seg(f"  {n} first-starters",nfs==n) for n in (0,1,2)]; seg("  3+ first-starters",nfs>=3)
print("by field experience (median starts)"); [seg(f"  median starts {lo}-{hi}",(medst>=lo)&(medst<hi)) for lo,hi in ((0,3),(3,6),(6,12),(12,99))]
trk=D["track"].astype(str); u,c=np.unique(trk[hold],return_counts=True)
print("by track (30+ holdout races)")
for t in u[np.argsort(-c)][:12]: seg(f"  {t}",trk==t)
# and within race: is the error on the favourite, mid or roughies? mass misallocated per band
m=hm&np.isfinite(mkt)&okm[ri]
for nm,lo,hi in (("fav ($1-4)",0.25,1.01),("mid ($4-12)",1/12,0.25),("long ($12-30)",1/30,1/12),("roughies ($30+)",0,1/30)):
    mm=m&(q>=lo)&(q<hi); print(f"{nm:18s} share of BSP mass {q[mm].sum()/q[m].sum()*100:4.0f}%  model gives it {p[mm].sum()/q[m].sum()*100:4.0f}%  open gives {mkt[mm].sum()/mkt[m].sum()*100:4.0f}%")
