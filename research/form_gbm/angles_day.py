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
    }
res={}
for i in range(n):
    tags=[k for k,m in A.items() if bool(m[i])]
    res[f"{int(U['race_number'][ri[i]])}|{str(U['name'][i])}"]=tags
json.dump(res,open(out,"w"),indent=0); print(sum(1 for v in res.values() if v),"of",n,"runners carry an angle")
