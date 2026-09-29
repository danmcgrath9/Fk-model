"""Where is BSP wrong? For every input, split runners into fifths; winners vs BSP-expected winners, on the older
races (dev, to 2026-05-06) and the newer ones (hold). Keep bins wrong in the same direction on both."""
import numpy as np, bench as b, stage2
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; won=(D["won"]==1).astype(float); q=D["q"]; dates=D["date"][ri]
dev=dates<"2026-05-06"; hold=~dev
F=np.load("F7.npy"); names=open("F7_names.txt").read().split("\n")
p=np.load("p_oof_blend3.npy"); res=np.clip(np.log(np.maximum(q,1e-4))-np.log(np.maximum(p,1e-4)),-3,3)
E=stage2.encodings(D["date"][ri],D["horse_id"],D["trainer"],D["jockey"],D["sire"],D["track"][ri],res)
T=np.load("late_feats.npy")
X=np.column_stack([F,E,T,np.log(p/np.maximum(q,1e-9))*0+np.log(np.maximum(p,1e-9))])
nm=names+["gap_horse_last","gap_horse_mean","gap_trainer","gap_jockey","gap_sire","gap_trainer_track","tempo_last","late_beyond_tempo","late600_last","to600_last","log_our_price_chance"]
ok=np.isfinite(q)&(q>0)
out=[]
for k in range(X.shape[1]):
    v=X[:,k]; m=ok&np.isfinite(v)
    if m.sum()<5000 or np.unique(v[m]).size<5: continue
    edges=np.unique(np.quantile(v[m&dev],[.2,.4,.6,.8]))
    bins=np.digitize(v,edges)
    for bi in np.unique(bins[m]):
        s=m&(bins==bi)
        sd,sh=s&dev,s&hold
        wd,wh=won[sd].sum(),won[sh].sum()
        if wd<80 or wh<40: continue
        aed,aeh=wd/q[sd].sum(),wh/q[sh].sum()
        out.append((nm[k],int(bi),aed,aeh,int(wd),int(wh),int(sd.sum()),int(sh.sum())))
import json; json.dump(out,open("scan_bsp.json","w"))
both=[o for o in out if (o[2]>1.08 and o[3]>1.08) or (o[2]<0.92 and o[3]<0.92)]
print("bins tested",len(out),"| wrong the same way on both periods (>8%):",len(both))
for o in sorted(both,key=lambda o:-min(abs(o[2]-1),abs(o[3]-1)))[:40]:
    print(f"{o[0]:40s} fifth {o[1]+1}  A/E vs BSP dev {o[2]:.2f} hold {o[3]:.2f}  wins {o[4]}/{o[5]}")
