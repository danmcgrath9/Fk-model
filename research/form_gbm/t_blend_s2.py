import numpy as np, bench as b, sys, stage2
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; dates=D["date"]
cut="2026-05-06"; dev=np.where(dates<cut)[0]; hold=np.where(dates>=cut)[0]; allr=np.arange(nR)
pt=np.load("p_oof.npy"); pn=np.load("p_oof_nn.npy"); comps=[pt,pn]; labels=["trees","net"]
import os
if os.path.exists("p_oof_cb.npy"): comps.append(np.load("p_oof_cb.npy")); labels.append("cb")
Ls=[np.log(np.maximum(x,1e-12)) for x in comps]
best=None
import itertools
grid=[w for w in itertools.product(*[np.arange(0,1.01,0.05)]*len(comps)) if abs(sum(w)-1)<1e-9]
for w in grid:
    s=b.score(b.softmax_races(sum(wi*l for wi,l in zip(w,Ls))),dev)[0]
    if best is None or s<best[0]: best=(s,w)
w=best[1]; pb=b.softmax_races(sum(wi*l for wi,l in zip(w,Ls)))
print("weights",dict(zip(labels,np.round(w,2))))
for n_,x in zip(labels,comps): print(b.fmt(f"{n_} OOF hold",b.score(x,hold)))
print(b.fmt("blend OOF hold",b.score(pb,hold))); print(b.fmt("blend OOF all",b.score(pb,allr)))
np.save("p_oof_blend.npy",pb)
