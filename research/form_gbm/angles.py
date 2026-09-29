"""Handicapping-book angles tested on our value bets (1 unit at the opening price) and at BSP, older vs newer races,
plus Schwartz's pool check: winners / BSP-expected winners for every runner with the angle."""
import numpy as np, bench as b
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; won=D["won"]==1; q=D["q"]; dates=D["date"][ri]; dev=dates<"2026-05-06"; hold=~dev
F=np.load("F7.npy"); nm=open("F7_names.txt").read().split("\n"); cF={n:i for i,n in enumerate(nm)}; g=lambda n:F[:,cF[n]]
X=D["X"]; cx=D["colidx"]; x=lambda n:X[:,cx[n]].astype(float)
p=np.load("p_oof_blend3.npy"); op=D["open"]; bsp=np.where(np.isfinite(D["bsp"])&(D["bsp"]>1),D["bsp"],np.nan)
fair=1/np.maximum(p,1e-9); ev=p*op-1; base=np.isfinite(op)&(op>1)&(fair<50)&(op<3*fair)&np.isfinite(bsp); v20=base&(ev>0.2)
# race runs only, newest first, compacted
P=D["P"].astype(float); f={n:i for i,n in enumerate(D["past_fields"])}; tr=(P[:,:,f["trial"]]==1)|~np.isfinite(P[:,:,f["rating"]])
R=np.full_like(P,np.nan)
for i in range(len(ri)):
    k=np.where(~tr[i])[0]; R[i,:len(k)]=P[i,k]
rr=lambda n,s: R[:,s,f[n]]
T=P  # all runs incl trials
days=P[:,:,f["days_before"]]
def field(v,fn):
    out=np.full(nR,np.nan)
    for r in range(nR):
        s,e=D["starts"][r],D["ends"][r]; y=v[s:e]; y=y[np.isfinite(y)]
        if len(y): out[r]=fn(y)
    return out
def rank_in_race(v,desc=True):
    out=np.full(len(ri),np.nan)
    for r in range(nR):
        s,e=D["starts"][r],D["ends"][r]; y=np.where(np.isfinite(v[s:e]),v[s:e],-1e9 if desc else 1e9)
        out[s:e]=(np.argsort(np.argsort(-y if desc else y))+1)
    return out
prep_today=x("raceInPrep"); wt_today=x("weight")
import pandas as pd
pid=D["past_race_ids"].astype(str); pz=P[:,:,f["prize"]]; mm=(pid!="")&np.isfinite(pz)&(pz>0)
pmap=pd.Series(pz[mm],index=pid[mm]).groupby(level=0).median()
prize_today=pd.Series(D["race_id"].astype(str)[ri]).map(pmap).to_numpy(dtype=float)
print("today's prize found for",np.isfinite(prize_today).mean().round(3),"of runners")
dist_today=D["distance"][ri].astype(float); going_today=D["going"][ri]
best_career=np.nanmax(R[:,:,f["rating"]],1)
r0,r1,r2=rr("rating",0),rr("rating",1),rr("rating",2)
prev_best=np.nanmax(R[:,1:,f["rating"]],1)
pos800_3=np.nanmean(R[:,:3,f["pos800"]],1); settle_3=np.nanmean(R[:,:3,f["settle"]],1); late_3=np.nanmean(R[:,:3,f["last600"]],1)
ok_prize=np.isfinite(rr("prize",0))&(rr("prize",0)>0)&np.isfinite(prize_today)
prize_ratio=np.where(ok_prize,prize_today/np.where(ok_prize,rr("prize",0),1),np.nan)
print("today prize median",np.nanmedian(prize_today),"last prize median",np.nanmedian(rr("prize",0)))
lead_cnt=field(np.where(pos800_3<=3,1.0,0.0),np.sum); fast_early=field(np.where(settle_3<=3,1.0,0.0),np.sum)
late_rank=rank_in_race(late_3); spd_rank=rank_in_race(rr("speedRating",0)); fs_rank=rank_in_race(rr("finishingSpeed",0))
model_rank=rank_in_race(p)
tr_last=np.array([next((k for k in range(10) if P[i,k,f["trial"]]==1),-1) for i in range(len(ri))])
trial_days=np.array([days[i,k] if k>=0 else np.nan for i,k in enumerate(tr_last)]); trial_fin=np.array([P[i,k,f["finish"]] if k>=0 else np.nan for i,k in enumerate(tr_last)]); trial_mgn=np.array([P[i,k,f["margin"]] if k>=0 else np.nan for i,k in enumerate(tr_last)])
wet=lambda gb: np.isin(gb,[2,3])
wetbest=np.nanmax(np.where(wet(R[:,:,f["going_band"]]),R[:,:,f["rating"]],np.nan),1); goodbest=np.nanmax(np.where(R[:,:,f["going_band"]]==1,R[:,:,f["rating"]],np.nan),1)
sp=R[:,:,f["sp"]]; fin0=rr("finish",0); mgn0=rr("margin",0); d0=rr("days_before",0)
T8=np.load("late_feats.npy"); lres=T8[:,1]; okl=np.isfinite(lres); q5=np.nanquantile(lres[okl],0.8)
lws=D["lws"][ri]; rrl=rr("raceRating",0)
with np.errstate(invalid="ignore"):
 A={
 "1 Lone leader (Brohamer)":(pos800_3<=2)&(lead_cnt[ri]<=1),
 "2 Closer when the pace will collapse (Brohamer)":(fast_early[ri]>=3)&(late_rank==1),
 "4 Beaten by the pace last start (Beyer/Cramer)":((rr("settle",0)>=8)&(mgn0<=3)&(rr("last600",0)>=2))|((rr("pos800",0)==1)&(mgn0<=3)&(fin0>1)),
 "5 Class drop by prize, ran OK (Quinn/Scott)":(prize_ratio<=0.7)&(rr("vsClass",0)>=-2),
 "6 Already run to today's par (Quinn)":np.nanmax(R[:,:4,f["rating"]],1)>=lws,
 "7 Riser who ran above expectation (Beyer)":(prize_ratio>=1.3)&(r0>=rr("expected",0)+2)&(spd_rank<=3),
 "8 Drop after a poor run (fade)":(prize_ratio<=0.7)&(rr("vsClass",0)<=-5),
 "9 Bounce after a new top (fade)":(r0>=prev_best+3)&(d0<=21),
 "10 Second-up quick back-up off a big first-up (fade)":(prep_today==2)&(d0<=14)&(r0>=best_career-1),
 "11 Pairing up near career best (Ragozin)":(np.abs(r0-r1)<=1)&(r0>=best_career-2)&(r1>=best_career-2),
 "12 Third-up peak (AU)":(prep_today==3)&(r0>r1)&(d0>=14)&(d0<=28),
 "13 First-up off a good trial (AU)":(prep_today==1)&(trial_days<=21)&((trial_fin==1)|(trial_mgn<=1)),
 "14 Improving while losing (Cramer)":(r0>r1)&(r1>r2)&(fin0>1),
 "14b Declining deep in prep (fade)":(r0<r1)&(r1<r2)&(prep_today>=6),
 "15 Market liked it, bad last run (Betfair AU)":((sp[:,:3]<=5).sum(1)>=2)&((fin0>=6)|(mgn0>=5)),
 "16 Weight relief 2kg+, no rise in class (Scott)":(wt_today<=rr("weight",0)-2)&(prize_ratio<=1),
 "18 Apprentice claim 2kg+, strong stable (AU)":(np.nan_to_num(x("apprentice_claim") if "apprentice_claim" in cx else g("apprentice_claim"))>=2)&(g("trainer_wr")>=0.15),
 "19 Prep step-up in trip, finished strongly (AU)":np.isin(prep_today,[2,3])&(dist_today-rr("distance",0)>=200)&(dist_today-rr("distance",0)<=400)&(fs_rank<=3),
 "20 Back in trip, was handy (Mordin)":(dist_today<=rr("distance",0)-200)&(rr("pos400",0)<=3)&(mgn0<=4),
 "21 Wet track, proven wet (Mordin)":wet(going_today)&(wetbest>=goodbest),
 "23 Quick back-up after a place (AU)":(fin0<=3)&(d0<=7)&(model_rank<=2),
 "24 Strong first-up trainer (Mordin)":(prep_today==1)&(g("trainer_fu_ae")>=1.2),
 "26 Price $30 or under (longshot cap)":op<=30,
 "OURS class drop by rating":np.isfinite(rrl)&(rrl>=lws+3),
 "OURS late 600 beyond tempo, top fifth":okl&(lres>=q5),
 }
def roi(s,pr):
    n=s.sum(); return (pr[s&won].sum()/n-1) if n else np.nan
print(f"{'angle':52s} {'bets/mtg':>8s} {'open':>7s} {'BSP old':>8s} {'BSP new':>8s}   pool A/E vs BSP old/new (all runners)")
rows=[]
for k,m in A.items():
    m=np.asarray(m,bool); s=v20&m
    a=m&np.isfinite(q)&(q>0)
    aeo=won[a&dev].sum()/q[a&dev].sum(); aen=won[a&hold].sum()/q[a&hold].sum()
    rows.append((k,s.sum()/456,roi(s,op),roi(s&dev,bsp),roi(s&hold,bsp),aeo,aen,(s&dev).sum(),(s&hold).sum()))
for r in rows:
    flag=" <<" if r[3]>0 and r[4]>0 and r[7]>=60 and r[8]>=40 else ""
    print(f"{r[0]:52s} {r[1]:8.2f} {r[2]:+7.1%} {r[3]:+8.1%} {r[4]:+8.1%}   {r[5]:.2f} / {r[6]:.2f}  (n {r[7]}/{r[8]}){flag}")
s=v20; print(f"{'reference: all value 20c':52s} {s.sum()/456:8.2f} {roi(s,op):+7.1%} {roi(s&dev,bsp):+8.1%} {roi(s&hold,bsp):+8.1%}")
np.save("angle_masks.npy",np.array([np.asarray(m,bool) for m in A.values()])); open("angle_names.txt","w").write("\n".join(A.keys()))
