"""First-up block (4 Oct 2026, t_firstup.py): runners resuming 60+ days after their last race start that are 200m+
short of that start's trip, or whose trial since it finished in the bottom half of the field. Value bets on them lost
25.6% at BSP (198 holdout bets) against -3.2% for the rest. Writes {"race|horse": reason}.
python fu_json.py UP_NPZ OUT_JSON"""
import numpy as np, json, sys
U=np.load(sys.argv[1],allow_pickle=True); P=U["P"].astype(float); f={str(n):i for i,n in enumerate(U["past_fields"])}; ri=U["race_idx"]
tr=P[:,:,f["trial"]]==1; fin=P[:,:,f["finish"]]; days=P[:,:,f["days_before"]]; run=P[:,:,f["runners"]]; dist=P[:,:,f["distance"]]
real=~tr&np.isfinite(fin)&(fin>0)
out={}
for k in range(len(ri)):
    idx=np.where(real[k])[0]
    if not len(idx): continue                      # first-starters have their own rule
    j=idx[0]; gap=days[k,j]
    if not (gap>=60): continue
    reasons=[]
    drop=dist[k,j]-float(U["distance"][ri[k]])
    if drop>=200: reasons.append(f"resuming {int(gap)} days, {int(drop)}m short of last start")
    t=np.where(tr[k]&np.isfinite(fin[k])&(fin[k]>0)&(days[k]<gap))[0]
    if len(t):
        rel=(fin[k,t[0]]-1)/max(run[k,t[0]]-1,1)
        if rel>0.5: reasons.append(f"resuming {int(gap)} days off a {int(fin[k,t[0]])}/{int(run[k,t[0]])} trial")
    if reasons: out[f"{int(U['race_number'][ri[k]])}|{U['name'][k]}"]="; ".join(reasons)
json.dump(out,open(sys.argv[2],"w"),indent=0); print("first-up blocks:",len(out)); [print(" ",a,"-",b) for a,b in out.items()]
