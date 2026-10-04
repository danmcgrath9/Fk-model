"""First-up block (4 Oct 2026, t_firstup.py): runners resuming 60+ days after their last race start that are 200m+
short of that start's trip, or whose trial since it finished in the bottom half of the field. Value bets on them lost
25.6% at BSP (198 holdout bets) against -3.2% for the rest. Writes {"race|horse": reason}.
Also (4 Oct 2026, t_pros.py, round-2 pro ideas), each a no-bet rule for value bets:
  bounce (Ragozin/Thoro-Graph): last start a new career-best rating by 3+ points  (190 bets, -40% at BSP)
  second-up after a first-up run that placed or was within 2L: EARLY-ONLY tag, see below (not a block)
  down 2kg+ in weight on the last start                                          (340 bets, -32%)
Value bets clear of all three made +8.2% at BSP (1,500 bets; +8.5% older half, +7.8% newer).
python fu_json.py UP_NPZ OUT_JSON"""
import numpy as np, json, sys
U=np.load(sys.argv[1],allow_pickle=True); cols={str(x):i for i,x in enumerate(U["cols"])}; P=U["P"].astype(float); f={str(n):i for i,n in enumerate(U["past_fields"])}; ri=U["race_idx"]
tr=P[:,:,f["trial"]]==1; fin=P[:,:,f["finish"]]; days=P[:,:,f["days_before"]]; run=P[:,:,f["runners"]]; dist=P[:,:,f["distance"]]; rat=P[:,:,f["rating"]]; wt=P[:,:,f["weight"]]; mg=P[:,:,f["margin"]]; prep=P[:,:,f["prep"]]
real=~tr&np.isfinite(fin)&(fin>0)
out={}
for k in range(len(ri)):
    idx=np.where(real[k])[0]
    if not len(idx): continue                      # first-starters have their own rule
    j=idx[0]; gap=days[k,j]; reasons=[]; early=[]
    if len(idx)>1 and np.isfinite(rat[k,j]):
        best=np.nanmax(rat[k,idx[1:]])
        if np.isfinite(best) and rat[k,j]>=best+3: reasons.append(f"bounce: last start a new peak ({rat[k,j]:.1f} vs best {best:.1f})")
    # second-up after a good first-up: EARLY-ONLY, not a block (4 Oct 2026, t_secup_open.py). The open under-rates them
    # (14% implied vs 19.5% winners) and they firm 21% to the jump: +17% at the open, -32% at BSP. Allowed at $8 or
    # shorter at the open (short ones +79%/+36%), blocked above $8 (-10% at the open, -58% at BSP). Bet at the open or not at all.
    if prep[k,j]==1 and (fin[k,j]<=3 or (np.isfinite(mg[k,j]) and mg[k,j]<=2)): early.append(f"second-up after a good first-up ({int(fin[k,j])}th, {mg[k,j]:.1f}L): firms about 20% to the jump, bet at the open or not at all; no bet over $8".replace("1th","1st").replace("2th","2nd").replace("3th","3rd"))
    w=float(U["X"][k,cols["weight"]])-wt[k,j]
    if np.isfinite(w) and w<=-2: reasons.append(f"down {abs(w):.1f}kg on last start")
    key=f"{int(U['race_number'][ri[k]])}|{U['name'][k]}"
    if not (gap>=60):
        if reasons: out[key]="; ".join(reasons)
        elif early: out[key]="EARLY: "+"; ".join(early)
        continue
    drop=dist[k,j]-float(U["distance"][ri[k]])
    if drop>=200: reasons.append(f"resuming {int(gap)} days, {int(drop)}m short of last start")
    t=np.where(tr[k]&np.isfinite(fin[k])&(fin[k]>0)&(days[k]<gap))[0]
    if len(t):
        rel=(fin[k,t[0]]-1)/max(run[k,t[0]]-1,1)
        if rel>0.5: reasons.append(f"resuming {int(gap)} days off a {int(fin[k,t[0]])}/{int(run[k,t[0]])} trial")
    if reasons: out[key]="; ".join(reasons)
    elif early: out[key]="EARLY: "+"; ".join(early)
json.dump(out,open(sys.argv[2],"w"),indent=0); print("first-up blocks:",len(out)); [print(" ",a,"-",b) for a,b in out.items()]
