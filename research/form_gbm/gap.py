import numpy as np, bench as b
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; p2=np.load("p_stage2_hold.npy"); q=D["q"]
F=np.load("F7.npy"); nm=open("F7_names.txt").read().split("\n"); c={n:i for i,n in enumerate(nm)}; g=lambda n:F[:,c[n]]
hold=np.where(D["date"]>="2026-05-06")[0]; mh=np.isin(ri,hold)
t=np.where(q>0,q*np.log(np.maximum(q,1e-300)/np.maximum(p2,1e-12)),0)
kl_r=np.bincount(ri,weights=t,minlength=nR)
starts=np.nan_to_num(g("f_careerForm_s"),nan=0); fs=(starts<1)
nfs=np.bincount(ri,weights=fs,minlength=nR); field=np.bincount(ri,minlength=nR)
spd=np.isnan(g("e_speedRating_last")); age=g("age")
print("hold races",len(hold),"mean KL",kl_r[hold].mean())
def grp(label,mask_r):
    m=np.intersect1d(hold,np.where(mask_r)[0]); print(f"{label:40s} races {len(m):5d} share {len(m)/len(hold):5.1%} meanKL {kl_r[m].mean():.4f} share of KL {kl_r[m].sum()/kl_r[hold].sum():5.1%}")
grp("no first starters",nfs==0); grp("1-2 first starters",(nfs>=1)&(nfs<=2)); grp("3+ first starters",nfs>=3)
grp("field <=8",field<=8); grp("field 9-12",(field>=9)&(field<=12)); grp("field 13+",field>=13)
r2=np.bincount(ri,weights=(age==2),minlength=nR)>0; grp("2yo race",r2)
metro=np.isin(D["track"],["Flemington","Caulfield","Caulfield Heath","Moonee Valley","Sandown Hillside","Sandown Lakeside"]); grp("metro",metro); grp("provincial/country",~metro)
# per-runner type: contribution split
def rg(label,mask):
    mm=mask&mh; print(f"  runner {label:32s} n {mm.sum():6d} sum KL-terms share {t[mm].sum()/t[mh].sum():6.1%}  mean|log(q/p)| {np.abs(np.log(np.maximum(q[mm],1e-6)/p2[mm])).mean():.3f}")
rg("first starter",fs); rg("raced, no speed fig",(~fs)&spd); rg("raced with speed",(~fs)&~spd)
fav=np.zeros(len(ri),bool)
for r in hold:
    s,e=D["starts"][r],D["ends"][r]; fav[s+np.argmax(q[s:e])]=True
rg("BSP favourite",fav)
dsl=np.nan_to_num(g("daysSinceLastRace"),nan=0); rg("first-up (60+ days)",(~fs)&(dsl>=60))
