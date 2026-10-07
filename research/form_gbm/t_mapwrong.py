"""When is the speed map wrong, and does the rail matter? (7 Oct 2026, founder.) Stage-2 inputs on the holdout,
same harness as t_v6_check (base = live v6). KL to BSP, lower is better, live v6 0.0800.
MAP: each horse's real settling history (share of field, last 5 runs, recency weighted, and its spread), the gap
between where Form King maps it and where it usually settles, genuine leaders in the race (habitual leaders),
'mapped to lead but rarely leads', and its early-speed rank. RAIL: metres out (races with a rail only) and
rail x mapped position."""
import numpy as np, csv, re
exec(open("t_v6_check.py").read().split('evaluate(V4,')[0])
V6=np.column_stack([V4,TV,CO])
st=P[:,:,f["settle"]]; rn=P[:,:,f["runners"]]
ok_=race&np.isfinite(st)&(st>0)&np.isfinite(rn)&(rn>1)
sh=np.where(ok_,(st-1)/np.maximum(rn-1,1),np.nan)
rk=np.cumsum(ok_,1); use5=ok_&(rk<=5); w=np.where(use5,0.8**(rk-1),0.0)
hs=np.where(w.sum(1)>0,np.nansum(np.nan_to_num(sh)*w,1)/np.maximum(w.sum(1),1e-9),np.nan)
hsd=np.array([np.nanstd(sh[k][use5[k]]) if use5[k].sum()>=2 else np.nan for k in range(n)])
lead_rate=np.where(use5.sum(1)>0,(np.where(use5,(st==1),False)).sum(1)/np.maximum(use5.sum(1),1),np.nan)
fld=np.bincount(ri,minlength=nR)[ri].astype(float)
Xr=D["X"].astype(float); cr=D["colidx"]
pos=Xr[:,cr["sm_predicted_position"]]; psh=(pos-1)/np.maximum(fld-1,1)
gap=psh-hs
habit_lead=(np.nan_to_num(hs,nan=1)<=0.15).astype(float)
n_lead=np.bincount(ri,weights=habit_lead,minlength=nR)[ri]
mapped_lead_rarely=((pos==1)&(np.nan_to_num(lead_rate,nan=0)<0.3)).astype(float)
es=Xr[:,cr["sm_early_speed"]]; esr=np.full(n,np.nan)
for r in range(nR):
    ix=np.where(ri==r)[0]; v=es[ix]
    if np.isfinite(v).sum()>1: o=np.argsort(-np.nan_to_num(v,nan=-1e9)); rr=np.empty(len(ix)); rr[o]=np.arange(1,len(ix)+1); esr[ix]=np.where(np.isfinite(v),rr/len(ix),np.nan)
MAP=np.column_stack([hs,hsd,gap,np.abs(gap),lead_rate,n_lead,habit_lead,mapped_lead_rarely,esr,n_lead*habit_lead])
rail={}
for r_ in csv.DictReader(l for l in open("rails.csv") if not l.startswith("#")):
    t=r_["rail"].lower(); m=re.search(r"(\d+(?:\.\d+)?)\s*m",t)
    rail[r_["race_id"]]=0.0 if "true" in t and not m else (float(m.group(1)) if m else np.nan)
rm=np.array([rail.get(x,np.nan) for x in D["race_id"].astype(str)])[ri]
RAIL=np.column_stack([rm,rm*np.nan_to_num(psh,nan=0.5),rm*np.nan_to_num(hs,nan=0.5)])
print(f"coverage: settle history {np.isfinite(hs).mean():.2f}, rail {np.isfinite(rm).mean():.2f} (holdout {np.isfinite(rm[np.isin(ri,hold)]).mean():.2f})",flush=True)
evaluate(V6,"live v6")
evaluate(np.column_stack([V6,MAP]),"v6 + speed map wrong")
evaluate(np.column_stack([V6,RAIL]),"v6 + rail")
evaluate(np.column_stack([V6,MAP,RAIL]),"v6 + map + rail")
