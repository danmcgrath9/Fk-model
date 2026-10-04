"""Pro punters' ideas, round 2 (4 Oct 2026): value bets at BSP on the holdout (rules incl. first-up block applied)."""
import numpy as np, bench as b
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; dates=D["date"]; c=D["colidx"]; X=D["X"].astype(float)
P=D["P"].astype(float); f={str(n):i for i,n in enumerate(D["past_fields"])}
S=np.load("S_hist.npy").astype(float); SF={str(n):i for i,n in enumerate(np.load("S_fields.npy",allow_pickle=True))}
g=lambda k: P[:,:,f[k]]
tr=g("trial")==1; fin=g("finish"); days=g("days_before"); run=g("runners"); dist=g("distance"); rat=g("rating"); wt=g("weight"); prize=g("prize"); mg=g("margin"); prep=g("prep")
real=~tr&np.isfinite(fin)&(fin>0); n=len(ri); ar=np.arange(n)
fs=real.sum(1)==0; j=np.argmax(real,1); has=real[ar,j]
ld=lambda v: np.where(has,v[ar,j],np.nan)
gap=ld(days); today_d=D["distance"][ri].astype(float)
firstup=has&(gap>=60)
tri=tr&np.isfinite(fin)&(fin>0)&(days<gap[:,None]); tj=np.argmax(tri,1); hast=tri[ar,tj]
trel=np.where(hast,(fin[ar,tj]-1)/np.maximum(run[ar,tj]-1,1),np.nan)
fu_block=firstup&((ld(dist)-today_d>=200)|(hast&(trel>0.5)))
p=np.load("pp_hold_v4.npy"); op=D["open"].astype(float); bsp=D["bsp"].astype(float); won=D["finish"]==1; q=D["q"]
hm=np.isin(ri,np.where(dates>="2026-05-06")[0]); newer=np.isin(ri,np.where(dates>="2026-07-20")[0])
fsb=np.bincount(ri,weights=(fs&np.isfinite(op)&(op<=6)).astype(float),minlength=nR)[ri]>0
v=hm&np.isfinite(op)&(op>1)&np.isfinite(bsp)&(bsp>1)&(p*op-1>=0.2)&~fs&~fsb&(1/p<50)&(op<3/p)&~fu_block
prof=np.where(won,(bsp-1)*0.92,-1.0)
def gr(nm,m):
    m=v&m
    if m.sum()==0: print(f"{nm:58s} no bets"); return
    a=lambda mm: f"{prof[mm].mean()*100:+6.1f}% ({mm.sum()})" if mm.sum() else "   -   "
    print(f"{nm:58s} bets {m.sum():4d}  BSP {prof[m].mean()*100:+6.1f}%  older {a(m&~newer):>14s}  newer {a(m&newer):>14s}  wins/model {won[m].sum()/p[m].sum():.2f}")
gr("ALL value bets (all current rules)",np.ones(n,bool))
# 1. Bounce (Ragozin / Thoro-Graph / Mordin): last start a new career-best rating by 3+, then back quickly
prior_best=np.array([np.nanmax(np.where(real[k],rat[k],np.nan)[j[k]+1:]) if has[k] and real[k,j[k]+1:].any() else np.nan for k in range(n)])
newpeak=has&np.isfinite(prior_best)&(ld(rat)>=prior_best+3)
gr("1 bounce: last start a new peak by 3+",newpeak)
gr("1 bounce: new peak, back within 21 days",newpeak&(gap<=21))
gr("1 bounce: new peak, 22+ days",newpeak&(gap>21))
# 2. Don Scott: weight change since last start
wch=X[:,c["weight"]]-ld(wt)
gr("2 weight up 2kg+ on last start",wch>=2); gr("2 weight down 2kg+ on last start",wch<=-2)
# 4. Pace (Davis / Beyer 'lone speed'): Form King's early-speed score (higher = quicker away)
es=X[:,c["sm_early_speed"]]; ssh=X[:,c["raw_settle_share"]]
top=np.full(n,np.nan); gap2=np.full(n,np.nan); nfast=np.zeros(n)
for r in np.unique(ri):
    ix=np.where(ri==r)[0]; vv=es[ix]; ok=np.isfinite(vv)
    if ok.sum()<3: continue
    s_=np.sort(vv[ok])[::-1]; top[ix]=s_[0]; gap2[ix]=s_[0]-s_[1]; nfast[ix]=(vv[ok]>=6.5).sum()
lone=(es==top)&(gap2>=1.0)
gr("4 lone speed (quickest away by 1+ point)",lone)
gr("4 quickest away, not clear",(es==top)&(gap2<1.0))
gr("4 hot pace (3+ quick types): backmarkers",(nfast>=3)&(ssh>=0.6))
gr("4 hot pace: on-pace runners",(nfast>=3)&(ssh<=0.3))
gr("4 soft pace (0-1 quick types): backmarkers",(nfast<=1)&(ssh>=0.6))
gr("4 soft pace: on-pace runners",(nfast<=1)&(ssh<=0.3))
# 5. Second-up after a sound first-up run
sec_up=has&(ld(prep)==1)&((ld(fin)<=3)|(ld(mg)<=2))
gr("5 second-up after a first-up top 3 or within 2L",sec_up)
# 6. Up in trip after a strong last 600 (needs further)
l6=np.where(has,S[ar,j,SF["6-F|vsClass"]],np.nan)
gr("6 up 200m+ after last 600 1L+ above class",(today_d-ld(dist)>=200)&(l6>=1))
gr("6 down 200m+ after last 600 1L+ below class",(ld(dist)-today_d>=200)&(l6<=-1))
# 7. Backing up within 7 days
gr("7 backing up within 7 days",has&(gap<=7))
# 8. Apprentice claim
gr("8 apprentice claiming 2kg+",X[:,c["raw_apprentice_claim"]]>=2)
print("--- overlaps and combined")
sec=sec_up; wd=(wch<=-2); hot=(nfast>=3)&((ssh>=0.6)|(ssh<=0.3))
gr("bounce AND second-up",newpeak&sec); gr("bounce only",newpeak&~sec); gr("second-up only",sec&~newpeak)
gr("any of bounce / second-up-after-good / weight down 2kg+",newpeak|sec|wd)
gr("none of the three",~(newpeak|sec|wd))
gr("bounce or second-up-after-good",newpeak|sec)
gr("neither",~(newpeak|sec))
