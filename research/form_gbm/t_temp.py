"""Our model gives favourites 27% of the mass where BSP gives 32%: is it a fixed bias or drift? Fit a sharpening
exponent (p^a renormalised) on different periods and test on others; then a rolling version (trailing 8 weeks)."""
import numpy as np, bench as b
from scipy.optimize import minimize_scalar
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; dates=D["date"].astype(str); q=D["q"]; p=np.load("pp_hold_v4.npy"); p0=np.load("p_oof_blend9.npy")
def sharpen(pr,a): z=a*np.log(np.maximum(pr,1e-12)); mx=np.full(nR,-np.inf); np.maximum.at(mx,ri,z); e=np.exp(z-mx[ri]); return e/np.bincount(ri,weights=e,minlength=nR)[ri]
def kl(pr,races): m=np.isin(ri,races); return np.where(q[m]>0,q[m]*np.log(np.maximum(q[m],1e-300)/np.maximum(pr[m],1e-12)),0).sum()/len(races)
def best_a(pr,races): return minimize_scalar(lambda a: kl(sharpen(pr,a),races),bounds=(0.6,1.6),method="bounded").x
hold=np.where(dates>="2026-05-06")[0]; dev=np.where(dates<"2026-05-06")[0]
print("stage-2 holdout prices: best sharpening exponent by period (1.0 = no change)")
for nm,r in (("May",hold[(dates[hold]>="2026-05")&(dates[hold]<"2026-06")]),("Jun",hold[(dates[hold]>="2026-06")&(dates[hold]<"2026-07")]),("Jul",hold[(dates[hold]>="2026-07")&(dates[hold]<"2026-08")]),("Aug",hold[(dates[hold]>="2026-08")&(dates[hold]<"2026-09")]),("Sep-Oct",hold[dates[hold]>="2026-09"])):
    a=best_a(p,r); print(f"  {nm:8s} races {len(r):4d}  best a {a:.3f}  KL {kl(p,r):.4f} -> {kl(sharpen(p,a),r):.4f}")
print("stage-1 OOF prices on dev (pre-May):", f"best a {best_a(p0,dev):.3f}")
# honest test: a fitted on the trailing 8 weeks, applied to the next week
import datetime as dt
d0=dt.date(2026,5,6); weeks=[(d0+dt.timedelta(days=7*k)) for k in range(0,23)]
tot_b=tot_a=0; nrace=0; adj=p.copy()
for k in range(8,len(weeks)-1):
    tr_=np.where((dates>=str(weeks[k-8]))&(dates<str(weeks[k])))[0]; te=np.where((dates>=str(weeks[k]))&(dates<str(weeks[k+1])))[0]
    if len(te)==0: continue
    a=best_a(p,tr_); m=np.isin(ri,te); adj[m]=sharpen(p,a)[m]; tot_b+=kl(p,te)*len(te); tot_a+=kl(adj,te)*len(te); nrace+=len(te)
print(f"rolling 8-week sharpening, applied forward over {nrace} races: KL {tot_b/nrace:.4f} -> {tot_a/nrace:.4f}")
np.save("pp_hold_rolling.npy",adj)
