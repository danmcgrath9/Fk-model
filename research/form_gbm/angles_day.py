"""The 12 picked angles for a day's runners, from the export alone. python angles_day.py UP_NPZ OUT_JSON"""
import numpy as np, json, sys, pandas as pd
up,out=sys.argv[1:3]
H=np.load("ds/model_ds.npz"); U=np.load(up); f={n:i for i,n in enumerate(H["past_fields"])}; cols=list(U["cols"])
frames=[]
for Z in (H,U):
    P=Z["P"].astype(float); pid=Z["past_race_ids"].astype(str); tr=P[:,:,f["trial"]]==1; t6=P[:,:,f["to600"]]
    hid=np.repeat(Z["horse_id"].astype(str)[:,None],10,1); m=(~tr)&np.isfinite(t6)&(pid!="")
    frames.append(pd.DataFrame({"pid":pid[m],"h":hid[m],"t":t6[m]}))
tg=pd.concat(frames).drop_duplicates(["pid","h"]).groupby("pid")["t"].agg(["mean","count"])
T=np.load("late_feats.npy"); q5=np.nanquantile(T[:,1][np.isfinite(T[:,1])],0.8)
P=U["P"].astype(float); pid=U["past_race_ids"].astype(str); n=len(U["horse_id"]); tr=(P[:,:,f["trial"]]==1)|~np.isfinite(P[:,:,f["rating"]])
R=np.full_like(P,np.nan); Rid=np.full(pid.shape,"",dtype=object)
for i in range(n):
    k=np.where(~tr[i])[0]; R[i,:len(k)]=P[i,k]; Rid[i,:len(k)]=pid[i,k]
rr=lambda c,s: R[:,s,f[c]]
x=lambda c: U["X"][:,cols.index(c)].astype(float)
ri=U["race_idx"]; lws=U["lws"][ri]; dist=U["distance"][ri].astype(float); going=U["going"][ri]
prep=x("raceInPrep"); wt=x("weight")
with np.errstate(invalid="ignore", all="ignore"):
    r0,r1,r2=rr("rating",0),rr("rating",1),rr("rating",2); prev_best=np.nanmax(R[:,1:,f["rating"]],1); best=np.nanmax(R[:,:,f["rating"]],1)
    fin0,mgn0,d0=rr("finish",0),rr("margin",0),rr("days_before",0); sp=R[:,:,f["sp"]]
    wet=lambda gb: np.isin(gb,[2,3])
    wetbest=np.nanmax(np.where(wet(R[:,:,f["going_band"]]),R[:,:,f["rating"]],np.nan),1); goodbest=np.nanmax(np.where(R[:,:,f["going_band"]]==1,R[:,:,f["rating"]],np.nan),1)
    # Accardi's "above the average in every section": early (start-800), middle (800-400) and late (400-finish)
    # all faster than the field in the last race run with sections. Value 20c+ bets with it: -0.5% at BSP over 713
    # (+1.2% over 310 newer races) against -14% for all value bets (4 Oct 2026).
    SF={str(k):j for j,k in enumerate(U["sec_fields"])}; S=U["S"].astype(float); Ptr=(P[:,:,f["trial"]]==1)
    hs=~Ptr&np.isfinite(S[:,:,SF["8-4|vsField"]]); js=np.argmax(hs,1); oks=hs[np.arange(n),js]
    cnt=sum((S[np.arange(n),js,SF[k]]>0).astype(int) for k in ("S-8|vsField","8-4|vsField","4-F|vsField"))
    all3=oks&(cnt==3)
    # wet-track indicator (Accardi WTI / O'Sullivan): mean vsClass on soft/heavy runs minus on good runs
    vc=R[:,:,f["vsClass"]]; gbR=R[:,:,f["going_band"]]
    wmean=np.nanmean(np.where(wet(gbR),vc,np.nan),1); dmean=np.nanmean(np.where(gbR==1,vc,np.nan),1)
    weakwet=wet(going)&np.isfinite(wmean)&np.isfinite(dmean)&(wmean-dmean<=-1)
    # Kingsley Bartholomew (The King Zone): a wide barrier costs more than people think. Value 20c+ bets drawn in the
    # outer quarter of a 10+ field that usually race back (settle in the back 40%) lost 48% at BSP over 358 (41% newer);
    # drawn wide at 1600m+ lost 22% (29% newer). Neither can be an EDGE bet (4 Oct 2026).
    fld=np.bincount(ri)[ri]; bsh=x("raw_barrier_share"); ssh=x("raw_settle_share")
    widebad=(bsh>=0.75)&(fld>=10)&((ssh>=0.6)|(dist>=1600))
    lres=np.full(n,np.nan)
    for i in range(n):
        if np.isfinite(R[i,0,f["last600"]]) and Rid[i,0] in tg.index and tg.loc[Rid[i,0],"count"]>=3:
            lres[i]=R[i,0,f["last600"]]-(-3.94-0.35*tg.loc[Rid[i,0],"mean"])
    A={
     "Beaten by the pace last start":((rr("settle",0)>=8)&(mgn0<=3)&(rr("last600",0)>=2))|((rr("pos800",0)==1)&(mgn0<=3)&(fin0>1)),
     "Already run to today's class":np.nanmax(R[:,:4,f["rating"]],1)>=lws,
     "New career-best last start":(r0>=prev_best+3)&(d0<=21),
     "Third-up, improving":(prep==3)&(r0>r1)&(d0>=14)&(d0<=28),
     "Declining deep in prep":(r0<r1)&(r1<r2)&(prep>=6),
     "Well backed before a bad last run":((sp[:,:3]<=5).sum(1)>=2)&((fin0>=6)|(mgn0>=5)),
     "Back in trip after being handy":(dist<=rr("distance",0)-200)&(rr("pos400",0)<=3)&(mgn0<=4),
     "Proven wet on a wet track":wet(going)&(wetbest>=goodbest),
     "Class drop (rating)":np.isfinite(rr("raceRating",0))&(rr("raceRating",0)>=lws+3),
     "Late 600 beyond the tempo":np.isfinite(lres)&(lres>=q5),
     "Above the field in all three sections":all3,
     # first-time blinkers: value 20c+ bets +9% at BSP over 476 (+27% over 179 newer races), 4 Oct 2026
     "Blinkers first time":x("blinkers_first")==1,
    }
res={}
for i in range(n):
    # Wet today and the horse rates 1L+ worse (vs class) on soft/heavy than on good: value bets on these lost 28% at BSP
    # (887 bets; 32% on the newer races), so no angle can make one an EDGE bet (4 Oct 2026).
    if bool(weakwet[i]) or bool(widebad[i]): res[f"{int(U['race_number'][ri[i]])}|{str(U['name'][i])}"]=[]; continue
    tags=[k for k,m in A.items() if bool(m[i])]
    res[f"{int(U['race_number'][ri[i]])}|{str(U['name'][i])}"]=tags
json.dump(res,open(out,"w"),indent=0); print(sum(1 for v in res.values() if v),"of",n,"runners carry an angle")
