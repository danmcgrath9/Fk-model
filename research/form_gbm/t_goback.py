"""Do resuming horses drawn wide and short of their trip get ridden back? And do backed ones of that kind win?"""
import numpy as np, bench as b
D=b.load(); P=D["P"].astype(float); f={n:i for i,n in enumerate(D["past_fields"])}; pid=D["past_race_ids"].astype(str); hid=D["horse_id"].astype(str)
g=lambda k: P[:,:,f[k]]
tr=g("trial")==1; fin=g("finish"); run=g("runners"); bar=g("barrier"); st=g("settle"); dist=g("distance"); days=g("days_before"); bsp=g("bsp")
real=~tr&np.isfinite(fin)&(fin>0)&np.isfinite(run)&(run>=6)
ss=(st-1)/np.maximum(run-1,1); bs=(bar-1)/np.maximum(run-1,1)
rows=[]; seen=set(); N,K=P.shape[:2]
for i in range(N):
    idx=[k for k in range(K) if real[i,k]]
    for a,k in enumerate(idx):
        older=idx[a+1:a+5]
        if len(older)<2: continue
        key=(hid[i],pid[i,k])
        if key in seen: continue
        seen.add(key)
        us=np.nanmean(ss[i,older]); 
        if not(np.isfinite(us) and np.isfinite(ss[i,k]) and np.isfinite(bs[i,k])): continue
        rows.append((days[i,older[0]]-days[i,k], bs[i,k], dist[i,older[0]]-dist[i,k], us, ss[i,k], fin[i,k]==1, bsp[i,k]))
A=np.array(rows,float); gap,bs0,drop,us,act,win,bp=A.T
mid=(us>=0.3)&(us<=0.7); fu=gap>=60; wide=bs0>=0.5; short=drop>=200
def rep(nm,m):
    m=m&mid; ok=m&np.isfinite(bp)&(bp>1)
    print(f"{nm:46s} runs {m.sum():6d}  settled {np.nanmean(act[m]-us[m])*100:+5.1f} pts vs usual  back third {np.mean(act[m]>=0.67)*100:4.1f}%  won {win[m].mean()*100:4.1f}%  wins/BSP {win[ok].sum()/np.sum(1/bp[ok]):.2f}")
print("Usual midfield settlers (settle share 0.3-0.7 over their previous runs). 'back third' = settled in the rear third.")
rep("all", np.ones(len(A),bool))
rep("not first-up", ~fu)
rep("first-up", fu)
rep("first-up, drawn inside half", fu&~wide)
rep("first-up, drawn wide half", fu&wide)
rep("first-up, wide, short of last trip 200m+", fu&wide&short)
rep("first-up, wide, same trip or longer", fu&wide&~short)
rep("not first-up, wide, short of last trip 200m+", ~fu&wide&short)
