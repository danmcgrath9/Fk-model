"""Mid-race surge (then fade) from Form King's section splits, last race run -> next run.
A/E against our out-of-fold price and against BSP, overall and on the newer 40% of races."""
import numpy as np, bench as b
D=b.load(); ri=D["race_idx"]; won=D["won"]==1; q=D["q"]; p=np.load("p_oof_blend3.npy")
N=np.load("ds/model_ds_sec.npz",allow_pickle=True)
key=lambda R,H,I: [f"{R[i]}|{h}" for i,h in zip(I,H)]
old=key(D["race_id"],D["horse_id"],ri); new=key(N["race_id"],N["horse_id"],N["race_idx"])
pos={k:i for i,k in enumerate(new)}; m=np.array([pos.get(k,-1) for k in old])
print("rows matched",(m>=0).sum(),"of",len(m))
SF={n:i for i,n in enumerate(N["sec_fields"])}; S=np.full((len(m),)+N["S"].shape[1:],np.nan,np.float32); S[m>=0]=N["S"][m[m>=0]]
P=D["P"].astype(float); f={n:i for i,n in enumerate(D["past_fields"])}; tr=P[:,:,f["trial"]]==1
has=~tr & np.isfinite(S[:,:,SF["8-4|vsClass"]])
j=np.argmax(has,1); ok=has[np.arange(len(ri)),j]
g=lambda n: S[np.arange(len(ri)),j,SF[n]]
gp=lambda n: P[np.arange(len(ri)),j,f[n]]
mid,midL,midF=g("8-4|vsClass"),g("8-4|vsLeader"),g("8-4|vsField")
l2,l2F=g("2-F|vsClass"),g("2-F|vsField")
overall=gp("vsClass"); fin,run,days=gp("finish"),gp("runners"),gp("days_before")
print("runners whose last race run has sections:",ok.sum())
newer=ri>=np.quantile(ri,0.6)
def ae(mm,label):
    mm=mm&ok; n=mm.sum(); w=won[mm].sum()
    if n<40: print(f"{label:58s} n {n}"); return
    se=np.sqrt(max(w,1))/q[mm].sum(); nm=mm&newer
    print(f"{label:58s} n {n:5d} wins {w:4d}  A/E ours {w/p[mm].sum():.2f}  A/E BSP {w/q[mm].sum():.2f} (±{se:.2f})  newer BSP {won[nm].sum()/max(q[nm].sum(),1e-9):.2f} n {nm.sum()}")
qm=np.nanquantile(mid[ok],[0.2,0.8,0.9]); print("mid 800-400 vs class quantiles 20/80/90%:",np.round(qm,2))
ae(ok,"all")
ae(mid>=qm[1],"fast middle: 800-400 top 20% vs class")
ae(mid>=qm[2],"very fast middle: top 10%")
ae(mid<=qm[0],"slow middle: bottom 20%")
fade=l2F<=-1.0
ae((mid>=qm[1])&fade,"fast middle, then FADED (last 200 1L+ slower than field)")
ae((mid>=qm[1])&~fade&np.isfinite(l2F),"fast middle, and held/kept going")
ae((mid>=qm[1])&fade&(fin>1),"fast middle, faded, got beaten")
ae((mid>=qm[1])&(midL>=1.0),"middle 1L+ faster than the leader (a real move)")
ae((mid>=qm[1])&(midL>=1.0)&fade,"  real move then faded")
# the middle better than the run as a whole (the bare figure hides it)
gap=mid-overall
qg=np.nanquantile(gap[ok],0.8)
ae(gap>=qg,"middle much better than the overall figure (top 20%)")
ae((gap>=qg)&(fin>1),"  ... and did not win")
ae((mid>=qm[1])&fade&(days<=35),"fast middle, faded, back within 35 days")
