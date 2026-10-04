"""Model vs opening market, KL to BSP and value-bet ROI, split by first-starter races (holdout from 6 May)."""
import sys, numpy as np, bench as b
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; dates=D["date"]
P=D["P"].astype(float); f={n:i for i,n in enumerate(D["past_fields"])}
real=~(P[:,:,f["trial"]]==1) & np.isfinite(P[:,:,f["finish"]]) & (P[:,:,f["finish"]]>0)
fs=real.sum(1)==0                                   # first starter: no race start (trials do not count)
p=np.load(sys.argv[1]); q=D["q"]; mkt=D["mkt"]; op=D["open"].astype(float); bsp=D["bsp"].astype(float)
won=D["finish"]==1; hold=np.where(dates>="2026-05-06")[0]; hm=np.isin(ri,hold)
fs_any=np.bincount(ri,weights=fs.astype(float),minlength=nR)>0
fs_backed=np.bincount(ri,weights=(fs&np.isfinite(op)&(op>1)&(op<=6)).astype(float),minlength=nR)>0
pj=D["pre_jump"] if "pre_jump" in D else np.load("ds/model_ds.npz",allow_pickle=True)["pre_jump"]
live=hold[pj[hold]]; bf=hold[~pj[hold]]
groups={"all holdout races":hold,
        "no first-starter":hold[~fs_any[hold]],
        "first-starter in race, none $6 or shorter":hold[fs_any[hold]&~fs_backed[hold]],
        "first-starter at $6 or shorter":hold[fs_backed[hold]],
        "LIVE-pulled, all":live, "LIVE-pulled, no first-starter":live[~fs_any[live]],
        "back-filled, no first-starter":bf[~fs_any[bf]]}
def kl(pr,races):
    m=np.isin(ri,races)&np.isfinite(pr); return np.where(q[m]>0,q[m]*np.log(np.maximum(q[m],1e-300)/np.maximum(pr[m],1e-12)),0).sum()/len(races)
def ll(pr,races):
    m=np.isin(ri,races)&won; return -np.log(np.maximum(pr[m],1e-12)).sum()/len(races)
okm=np.bincount(ri,weights=(~np.isfinite(mkt)).astype(float),minlength=nR)==0   # races with an opening price on every runner
print(f"{'races':44s} {'n':>5s} {'KL model':>9s} {'KL open':>8s} {'LL model':>9s} {'LL open':>8s}")
for nm,r in groups.items():
    r=r[okm[r]]
    print(f"{nm:44s} {len(r):5d} {kl(p,r):9.4f} {kl(mkt,r):8.4f} {ll(p,r):9.4f} {ll(mkt,r):8.4f}")
prof_b=np.where(won,(bsp-1)*0.92,-1.0); prof_o=np.where(won,op-1,-1.0)
v=np.isfinite(op)&(op>1)&np.isfinite(bsp)&(bsp>1)&(p*op-1>=0.2)&~fs
print("\nvalue 20c+ bets (not on first-starters), 1 unit; open ROI has no deductions")
for nm,r in groups.items():
    m=v&np.isin(ri,r)
    print(f"{nm:44s} bets {m.sum():5d}  wins {won[m].sum():4d}  open {prof_o[m].mean()*100:+6.1f}%  BSP {prof_b[m].mean()*100:+6.1f}%  ({prof_b[m].sum():+.1f}u)")
