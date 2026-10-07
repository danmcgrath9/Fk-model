"""Does the plan work better or worse at particular tracks? (7 Oct 2026, founder.) The plan as it stands, by track and
by track type, holdout and before the holdout. A track only counts as a pattern if it shows in BOTH samples."""
import numpy as np, collections
exec(open("t_plan_now.py").read().split("for lab,P_,M_ in")[0])
trk=D["track"][ri].astype(str)
base=np.array([t.replace(" Synthetic","").replace(" Hillside","").replace(" Lakeside","").replace(" Heath","").replace(" Park","").strip() for t in trk])
metro={"Flemington","Caulfield","Moonee Valley","Sandown"}
prov={"Geelong","Ballarat","Bendigo","Cranbourne","Pakenham","Mornington","Sale","Kilmore","Seymour","Moe","Werribee","Warrnambool","Kyneton","Echuca","Wangaratta","Wodonga","Traralgon","Benalla","Hamilton","Colac","Stawell","Horsham","Ararat","Swan Hill","Mildura","Bairnsdale","Tatura","Yarra Valley","Yarra Glen","Donald","Murtoa","Gunbower","Edenhope"}
synth=np.char.find(trk,"Synthetic")>=0
typ=np.where(np.isin(base,list(metro)),"Metro",np.where(synth,"Synthetic","Provincial & country"))
pwd=np.where(won,op*0.93-1,-1.0)
res={}
for lab,P_,M_ in (("hold",shade(p),hm),("pre",shade(po_),pre)):
    L_,S_=bets2(P_,M_,block_nowd); res[lab]=(L_,S_,P_)
def line(nm,m):
    out=[]
    for lab in ("hold","pre"):
        L_,S_,P_=res[lab]; mm=L_&m
        out.append(f"{mm.sum():4d} bets {roi(mm,S_,pwd):+6.1f}% open-ded {roi(mm,S_,pw_b):+6.1f}% BSP  w/e {won[mm].sum()/max(P_[mm].sum(),1e-9):.2f}" if mm.sum() else "   -")
    print(f"  {nm:22s} HOLDOUT {out[0]}   |   BEFORE {out[1]}")
print("BY TRACK TYPE (open-ded = at the open less 7% deductions; w/e = wins / what our price expected)")
for t in ("Metro","Provincial & country","Synthetic"): line(t,typ==t)
print("\nBY TRACK (30+ bets in the holdout)")
L_,S_,_=res["hold"]; cnt=collections.Counter(base[L_])
for t,k in sorted(cnt.items(),key=lambda x:-x[1]):
    if k>=30: line(t,base==t)

print("\nMETRO FIXES (whole plan, $100 a unit; profit at the open less 7% deductions / at BSP)")
ismet=typ=="Metro"
qo=np.where(np.isfinite(op)&(op>1),1/np.where(np.isfinite(op)&(op>1),op,2),np.nan); tq=np.bincount(ri,weights=np.nan_to_num(qo),minlength=nR)[ri]; qo=qo/np.where(tq>0,tq,1)
def bets3(pp,mask,thr_met):
    mkt_=D["mkt"].astype(float)
    okr_=np.bincount(ri,weights=(~np.isfinite(mkt_)|~np.isfinite(pp)).astype(float),minlength=nR)==0
    cp=mask&okr_[ri]&np.isfinite(bsp)&np.isfinite(op)&(op>1)&(bsp>1)&(1/pp<50)&(op<3/pp)
    thr=np.where(ismet,thr_met,0.2)
    lv=cp&(pp*op-1>=thr)&~block_nowd&(1/pp>=2)&(1/pp<=15)
    return lv,np.where(lv,np.minimum(4.0,75*np.clip(((pp/op)**0.5*op-1)/(op-1),0,None)),0.0)
for lab,P0,M_ in (("holdout",shade(p),hm),("before",shade(po_),pre)):
    for nm,a,thr in (("as now",1.0,0.2),("metro needs 30c+",1.0,0.3),("metro needs 40c+",1.0,0.4),("metro: 70% ours / 30% market",0.7,0.2),("metro: 50/50 with market",0.5,0.2),("no metro bets",1.0,99)):
        P_=np.where(ismet,np.exp(a*np.log(np.maximum(P0,1e-9))+(1-a)*np.log(np.maximum(np.nan_to_num(qo,nan=1e-9),1e-9))),P0)
        tt=np.bincount(ri,weights=np.nan_to_num(P_),minlength=nR)[ri]; P_=P_/np.where(tt>0,tt,1)
        L_,S_=bets3(P_,M_,thr); mm=L_&ismet
        print(f"  {lab:8s} {nm:30s} all: {L_.sum():4d} bets ${100*(S_*pwd)[L_].sum():>+9,.0f} / ${100*(S_*pw_b)[L_].sum():>+8,.0f}   metro: {mm.sum():3d} bets ${100*(S_*pwd)[mm].sum():>+8,.0f} / ${100*(S_*pw_b)[mm].sum():>+8,.0f}")
