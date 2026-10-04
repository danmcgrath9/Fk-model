"""Value bets on first-uppers: down in distance, after a poor trial (holdout from 6 May, stage-2 v4 prices, BSP)."""
import numpy as np, bench as b
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; dates=D["date"]
P=D["P"].astype(float); f={n:i for i,n in enumerate(D["past_fields"])}
tr=P[:,:,f["trial"]]==1; fin=P[:,:,f["finish"]]; days=P[:,:,f["days_before"]]; run=P[:,:,f["runners"]]
real=~tr&np.isfinite(fin)&(fin>0)
fs=real.sum(1)==0
ar=np.arange(len(ri)); j=np.argmax(real,1); has=real[ar,j]
last_days=np.where(has,days[ar,j],np.nan)
pd_=[k for k in f if k in("distance","dist","distance_m")]; dk=f[pd_[0]]
last_dist=np.where(has,P[ar,j,dk],np.nan); today=D["distance"][ri].astype(float)
firstup=has&(last_days>=60)
# trial since the last race start: the most recent trial with days_before < last race's days_before
tri=tr&np.isfinite(fin)&(fin>0)&(days<last_days[:,None]); tj=np.argmax(tri,1); hast=tri[ar,tj]
trel=np.where(hast,(fin[ar,tj]-1)/np.maximum(run[ar,tj]-1,1),np.nan)
p=np.load("pp_hold_v4.npy"); op=D["open"].astype(float); bsp=D["bsp"].astype(float); won=D["finish"]==1; q=D["q"]
hm=np.isin(ri,np.where(dates>="2026-05-06")[0])
fsb=np.bincount(ri,weights=(fs&np.isfinite(op)&(op<=6)).astype(float),minlength=nR)[ri]>0
v=hm&np.isfinite(op)&(op>1)&np.isfinite(bsp)&(bsp>1)&(p*op-1>=0.2)&~fs&~fsb&(1/p<50)&(op<3/p)
prof=np.where(won,(bsp-1)*0.92,-1.0)
def g(nm,m):
    m=v&m; print(f"{nm:52s} bets {m.sum():5d} wins {won[m].sum():4d}  BSP ROI {prof[m].mean()*100:+6.1f}%  wins/model {won[m].sum()/p[m].sum():.2f}  wins/BSP {won[m].sum()/q[m].sum():.2f}")
g("all value bets (rules applied)",np.ones(len(ri),bool))
g("first-up (60+ days since last race start)",firstup)
g("not first-up",~firstup)
g("first-up, down 200m+ from last start",firstup&(last_dist-today>=200))
g("first-up, same or up in distance",firstup&(last_dist-today<200))
g("first-up, last trial in the bottom half",firstup&hast&(trel>0.5))
g("first-up, last trial top half",firstup&hast&(trel<=0.5))
g("first-up, no trial",firstup&~hast)
bad=firstup&((last_dist-today>=200)|(hast&(trel>0.5)))
g("BLOCK: first-up AND (down 200m+ OR poor trial)",bad)
g("everything else",~bad)
newer=np.isin(ri,np.where(dates>="2026-07-20")[0])
g("  newer half: blocked group",bad&newer); g("  newer half: everything else",~bad&newer)
g("  older half: blocked group",bad&~newer); g("  older half: everything else",~bad&~newer)
c=D["colidx"]; X=D["X"].astype(float); bsh=X[:,c["raw_barrier_share"]]; ssh=X[:,c["raw_settle_share"]]
fld=np.bincount(ri,minlength=nR)[ri]
print("--- ridden-back profile: first-up, drawn in the wide half, usually settles midfield or back")
wideh=bsh>=0.5; midback=ssh>=0.3; down=(last_dist-today>=200)
g("first-up, wide half, midfield-or-back settler",firstup&wideh&midback)
g("  ... and short of last trip 200m+",firstup&wideh&midback&down)
g("  ... same trip or longer",firstup&wideh&midback&~down)
g("first-up, inside half",firstup&~wideh)
gb=firstup&wideh&midback&down
g("  newer half: ridden-back + short",gb&newer); g("  older half: ridden-back + short",gb&~newer)
