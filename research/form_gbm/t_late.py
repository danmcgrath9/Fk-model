import numpy as np, bench as b
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; won=D["won"]==1; q=D["q"]
p=np.load("p_oof_blend3.npy")
P=D["P"].astype(float); f={n:i for i,n in enumerate(D["past_fields"])}; pid=D["past_race_ids"].astype(str)
tr=P[:,:,f["trial"]]==1
# the last RACE run per runner
j=np.argmax(~tr & np.isfinite(P[:,:,f["last600"]]),1); has=(~tr & np.isfinite(P[:,:,f["last600"]]))[np.arange(len(ri)),j]
g=lambda n: P[np.arange(len(ri)),j,f[n]]
L6,E6,dist,settle,vs=g("last600"),g("to600"),g("distance"),g("settle"),g("vsClass")
lastid=pid[np.arange(len(ri)),j]
# race tempo of that past race: mean to600 of every runner we have from it (any row, any slot)
from collections import defaultdict
acc=defaultdict(list)
for i in range(len(ri)):
    for s in range(10):
        if not tr[i,s] and np.isfinite(P[i,s,f["to600"]]) and pid[i,s]: acc[(pid[i,s])].append((D["horse_id"][i],P[i,s,f["to600"]]))
tempo=np.full(len(ri),np.nan); ntempo=np.zeros(len(ri))
for i in np.where(has)[0]:
    v=dict(acc.get(lastid[i],[])); 
    if len(v)>=3: tempo[i]=np.mean(list(v.values())); ntempo[i]=len(v)
ok=has&np.isfinite(tempo)&np.isfinite(L6)
print("runners with a last run + its race tempo:",ok.sum(),"of",len(ri))
# late speed beyond what the tempo explains (fit on all; tempo only, a linear adjustment)
A=np.column_stack([np.ones(ok.sum()),tempo[ok]]); coef=np.linalg.lstsq(A,L6[ok],rcond=None)[0]
lres=np.full(len(ri),np.nan); lres[ok]=L6[ok]-A@coef
print("last600 = %.2f + %.2f x race tempo  (slower early -> faster late)"%tuple(coef))
def ae(m,label):
    n=m.sum(); w=won[m].sum()
    print(f"{label:48s} n {n:5d} wins {w:4d}  A/E model {w/p[m].sum():.2f}  A/E BSP {w/q[m].sum():.2f}  BSP vs model {np.exp(np.mean(np.log(np.maximum(q[m],1e-6)/p[m])))-1:+.1%}")
tq=np.nanquantile(tempo[ok],[1/3,2/3]); slow=ok&(tempo<=tq[0]); fast=ok&(tempo>=tq[1])
print("\n-- raw last 600 (top fifth) by the tempo of that race")
top=ok&(L6>=np.nanquantile(L6[ok],0.8))
ae(top&slow,"big raw last600, SLOW tempo"); ae(top&~slow&~fast,"big raw last600, even tempo"); ae(top&fast,"big raw last600, FAST tempo")
print("\n-- tempo-adjusted late speed, quintiles")
qs=np.nanquantile(lres[ok],[.2,.4,.6,.8])
for k,(lo,hi) in enumerate(zip([-np.inf,*qs],[*qs,np.inf])):
    ae(ok&(lres>lo)&(lres<=hi),f"late beyond tempo Q{k+1}")
print("\n-- the springboard: big tempo-adjusted late speed but rating capped (vs class <= 0)")
ae(ok&(lres>=qs[3])&(vs<=0),"top fifth late-beyond-tempo, ran below class")
ae(ok&(lres>=qs[3])&(vs>0),"top fifth late-beyond-tempo, ran above class")
ae(ok&(lres>=qs[3])&slow&(settle>=5),"...and slow tempo, settled 5th or worse")
np.save("late_feats.npy",np.column_stack([tempo,lres,L6,E6]))
