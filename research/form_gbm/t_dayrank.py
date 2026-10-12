"""Rating of the day (12 Oct 2026, founder: "look at runs that rate well on the day, ie 3rd best rating of the day
carries more weight, especially for younger horses"). Same harness as t_mapwrong (base = live v6), KL to BSP on the
holdout, lower is better.
For each past run: where its rating sat among every run we hold from that MEETING (track + date, from the past race
id) and from that whole DAY (every track): rank, share of the field of runs, top-3 of the meeting. Ratings are
compared raw and weight-for-age adjusted (wfaRat), because a young horse's raw rating understates it against older
horses on the same card. Per runner: the last run, the best of the last three, and how many of the last five were a
top-3 rating of their meeting; then the same multiplied by a young-horse flag (age 3 or under, or 5 starts or fewer).
CAVEATS stated up front: (1) a meeting's runs are the ones we hold, i.e. runs by horses that started again inside our
data, so coverage is partial and the count is an input; (2) Form King ratings can be recalculated after the race (the
known leak), and this feature inherits that exactly as every rating feature does."""
import numpy as np, collections
exec(open("t_v6_check.py").read().split('evaluate(V4,')[0])
V6=np.column_stack([V4,TV,CO])
pid=D["past_race_ids"].astype(str); hid=np.broadcast_to(D["horse_id"][:,None].astype(str),pid.shape)
ok=race&(pid!="")
meet=np.char.rpartition(pid,"_")[:,:,0]; day=np.array([[x.split("_")[1] if "_" in x else "" for x in row] for row in pid])
def ranks(field, key):
    v=P[:,:,f[field]]; good=ok&np.isfinite(v)
    seen={}
    for k_,h_,x_,g_ in zip(key[good],hid[good],v[good],pid[good]): seen[(g_,h_)]=(k_,x_)
    by=collections.defaultdict(list)
    for (k_,x_) in seen.values(): by[k_].append(x_)
    srt={k_:np.sort(np.array(xs)) for k_,xs in by.items()}
    rk=np.full(v.shape,np.nan); nn=np.full(v.shape,np.nan)
    for (a,c) in zip(*np.where(good)):
        s=srt[key[a,c]]; rk[a,c]=1+len(s)-np.searchsorted(s,v[a,c],side="right"); nn[a,c]=len(s)
    pct=np.where(nn>=8,(rk-1)/np.maximum(nn-1,1),np.nan)   # 0 = best run of the meeting; under 8 runs held = unknown
    top3=np.where(nn>=8,(rk<=3).astype(float),np.nan)
    return rk,nn,pct,top3
def per_runner(rk,nn,pct,top3):
    has=np.isfinite(pct); j=np.argmax(has,1); okj=has[ar,j]
    last=np.where(okj,pct[ar,j],np.nan); lastn=np.where(okj,nn[ar,j],np.nan); lastt=np.where(okj,top3[ar,j],np.nan)
    order=np.cumsum(has,1)
    b3=np.where((has&(order<=3)).any(1),np.nanmin(np.where(has&(order<=3),pct,9),1),np.nan)
    t5=np.where(has.any(1),np.nansum(np.where(has&(order<=5),top3,0),1),np.nan)
    return np.column_stack([last,lastt,b3,t5,lastn,rrel(last),rrel(b3)])
cols=[]
for fld in ("rating","wfaRat"):
    cols.append(per_runner(*ranks(fld,meet))); cols.append(per_runner(*ranks(fld,day))[:,:4])
DAY=np.column_stack(cols)
Xr=D["X"].astype(float); cr=D["colidx"]
age=Xr[:,cr["age"]]; starts=Xr[:,cr["f_careerForm_s"]]   # career starts before today
young=((np.nan_to_num(age,nan=9)<=3)|(np.nan_to_num(starts,nan=99)<=5)).astype(float)
YNG=np.column_stack([young]+[DAY[:,i]*young for i in (0,1,2,3,7,8,9,10)])
print(f"coverage: last run ranked at its meeting {np.isfinite(DAY[:,0]).mean():.2f}, young runners {young.mean():.2f}",flush=True)
med_age=np.array([np.nanmedian(age[ri==r]) if np.isfinite(age[ri==r]).any() else 9 for r in range(nR)])
hold_y=np.array([r for r in hold if med_age[r]<=3]); print(f"holdout races {len(hold)}, of them young-horse races (median age 3 or under) {len(hold_y)}",flush=True)
for X_,lab in ((V6,"live v6"),(np.column_stack([V6,DAY]),"v6 + rating of the day"),(np.column_stack([V6,DAY,YNG]),"v6 + rating of the day + young")):
    pp=evaluate(X_,lab); print(b.fmt("   young-horse races only",b.score(pp,hold_y)),flush=True)
