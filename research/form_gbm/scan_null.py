import numpy as np, bench as b, json, stage2
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; q=D["q"]; dates=D["date"][ri]; dev=dates<"2026-05-06"
exec(open("scan_bsp.py").read().split("ok=np.isfinite(q)&(q>0)")[0].split("D=b.load()")[1].split("\n",1)[1])
ok=np.isfinite(q)&(q>0)
cols=[k for k in range(X.shape[1]) if np.isfinite(X[ok,k]).sum()>=5000 and np.unique(X[ok&np.isfinite(X[:,k]),k]).size>=5]
B=[]
for k in cols:
    v=X[:,k]; m=ok&np.isfinite(v); edges=np.unique(np.quantile(v[m&dev],[.2,.4,.6,.8])); bins=np.digitize(v,edges)
    for bi in np.unique(bins[m]): B.append(m&(bins==bi))
rng=np.random.default_rng(0); counts=[]
st,en=D["starts"],D["ends"]
for sim in range(20):
    w=np.zeros(len(ri))
    u=rng.random(nR)
    cq=np.cumsum(q)  # sample one winner per race from BSP chances
    for r in range(nR):
        s,e=st[r],en[r]; c=np.cumsum(q[s:e]); w[s+min(np.searchsorted(c,u[r]*c[-1]),e-s-1)]=1
    n=0
    for s_ in B:
        sd,sh=s_&dev,s_&~dev; wd,wh=w[sd].sum(),w[sh].sum()
        if wd<80 or wh<40: continue
        a,bb=wd/q[sd].sum(),wh/q[sh].sum()
        if (a>1.08 and bb>1.08) or (a<0.92 and bb<0.92): n+=1
    counts.append(n); print(sim,n,flush=True)
print("null: bins passing by chance, mean",np.mean(counts),"range",min(counts),max(counts))
