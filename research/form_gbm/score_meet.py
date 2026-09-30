import numpy as np, json, re, collections, sys
norm=lambda s: re.sub(r"[^a-z0-9]","",s.lower())
N=np.load("ds/model_ds_sec.npz",allow_pickle=True); ri=N["race_idx"]; rid=N["race_id"]
date,track=sys.argv[1],sys.argv[2]
sel=[i for i in range(len(ri)) if str(N["date"][ri[i]])==date and str(N["track"][ri[i]])==track]
res={(str(rid[ri[i]]),norm(str(N["name"][i]))):(int(N["finish"][i]),float(N["bsp"][i]),float(N["open"][i])) for i in sel}
def score(path,key="p"):
    M=json.load(open(path)); by=collections.defaultdict(dict)
    for r in M: by[r["race_id"]][norm(r["horse"])]=r[key]
    kl=[];ko=[];ll=[];lo=[]
    for race in sorted(by):
        run=[(h,p) for h,p in by[race].items() if (race,h) in res]
        q=np.array([1/res[(race,h)][1] if res[(race,h)][1]>1 else np.nan for h,_ in run]); o=np.array([1/res[(race,h)][2] if res[(race,h)][2]>1 else np.nan for h,_ in run])
        if len(run)<3 or np.isnan(q).any() or np.isnan(o).any(): continue
        p=np.array([p for _,p in run]); p/=p.sum(); q/=q.sum(); o/=o.sum()
        w=[i for i,(h,_) in enumerate(run) if res[(race,h)][0]==1]
        kl.append(np.sum(q*np.log(q/p))); ko.append(np.sum(q*np.log(q/o)))
        if w: ll.append(-np.log(p[w[0]])); lo.append(-np.log(o[w[0]]))
    return len(kl),np.mean(kl),np.mean(ko),np.mean(ll),np.mean(lo)
for path,key in [(a.split(":")[0],a.split(":")[1] if ":" in a else "p") for a in sys.argv[3:]]:
    n,k,ko,l,lo=score(path,key); print(f"{path.split('/')[-1]:34s} {key:8s} races {n}  KL to BSP {k:.4f} (open {ko:.4f})  winner logloss {l:.3f} (open {lo:.3f})")
