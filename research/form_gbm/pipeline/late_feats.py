"""late_feats.npy for angles_day.py: the tempo-adjusted late-speed figure from t_late.py, without its A/E tables (which need
an old oof file). Run in the model work folder after a restart: python3.13 late_feats.py"""
import numpy as np, bench as b
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; won=D["won"]==1; q=D["q"]
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
np.save("late_feats.npy",np.column_stack([tempo,lres,L6,E6])); print("late_feats.npy saved")
