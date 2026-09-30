"""Mid-race move then fade (last race run) vs how the horse runs next: A/E against our price and BSP."""
import numpy as np, bench as b
D=b.load(); ri=D["race_idx"]; won=D["won"]==1; q=D["q"]; dates=D["date"] if "date" in D else None
p=np.load("p_oof_blend3.npy")
P=D["P"].astype(float); f={n:i for i,n in enumerate(D["past_fields"])}
tr=P[:,:,f["trial"]]==1
ok_run=~tr & np.isfinite(P[:,:,f["pos400"]]) & np.isfinite(P[:,:,f["finish"]]) & (P[:,:,f["finish"]]>0)
j=np.argmax(ok_run,1); has=ok_run[np.arange(len(ri)),j]
g=lambda n: P[np.arange(len(ri)),j,f[n]]
settle,p8,p4,fin,run,L6,E6,dist,days=g("settle"),g("pos800"),g("pos400"),g("finish"),g("runners"),g("last600"),g("to600"),g("distance"),g("days_before")
start=np.where(np.isfinite(settle)&(settle>0),settle,p8)
ok=has&np.isfinite(start)&(start>0)&(run>=6)
move=start-p4          # places gained settle -> 400m
fade=fin-p4            # places lost 400m -> finish
mv=move/run; fd=fade/run
print("runners with a last run we can read:",ok.sum(),"of",len(ri))
# newer/older split by race order (bench keeps races in date order)
newer=ri>=np.quantile(ri,0.6)
def ae(m,label):
    n=m.sum(); w=won[m].sum()
    if n<40: print(f"{label:52s} n {n}"); return
    se=np.sqrt(w)/max(q[m].sum(),1e-9)
    print(f"{label:52s} n {n:5d} wins {w:4d}  A/E ours {w/p[m].sum():.2f}  A/E BSP {w/q[m].sum():.2f} (±{se:.2f})"
          f"   newer A/E BSP {won[m&newer].sum()/max(q[m&newer].sum(),1e-9):.2f} n {(m&newer).sum()}")
big=ok&(move>=4); fad=fade>=2
ae(ok,"all with a last run")
ae(ok&(move<=0),"no move (held or lost ground settle->400)")
ae(ok&(move>=1)&(move<=3),"moved 1-3 places")
ae(big,"big move: gained 4+ places settle->400")
ae(big&fad,"  big move then FADED (lost 2+ places 400->finish)")
ae(big&(fade<=0),"  big move and HELD or kept going")
ae(ok&(mv>=0.3)&(fd>=0.15),"move 30%+ of field then fade 15%+")
# where did they finish: faded but still in the first half?
ae(big&fad&(fin<=run/2),"  big move, faded, still first half")
ae(big&fad&(fin>run/2),"  big move, faded, second half")
# the late speed of the faders: a slow last600 relative to their own to600
ae(big&fad&(days<=35),"  big move, faded, back within 35 days")
ae(big&fad&(days>35),"  big move, faded, back after 35+ days")
# next start distance vs that run
dnow=D["X"][:,list(D["cols"]).index("distance")] if "distance" in list(D["cols"]) else None
if dnow is not None:
    ae(big&fad&(dnow<dist-50),"  big move, faded, SHORTER trip next")
    ae(big&fad&(np.abs(dnow-dist)<=50),"  big move, faded, same trip next")
    ae(big&fad&(dnow>dist+50),"  big move, faded, LONGER trip next")
