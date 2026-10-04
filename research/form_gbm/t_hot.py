"""Hot form: jockey, trainer and jockey-trainer BSP-gap encodings with short half-lives (30 and 90 days) added to stage 2."""
import numpy as np, bench as b, stage2
src=open("t_research.py").read().split("# 1. Accardi")[0]
exec(src)
import importlib
rdd=D["date"][ri]
# reuse stage2's enc machinery by calling encodings with a patched return: simplest is to re-implement the loop here
def enc(key,k,half):
    dn=stage2._days(rdd); order=sorted(set(rdd.tolist())); byd={d:np.where(rdd==d)[0] for d in order}
    s,nn_,t={},{},{}; out=np.zeros(n); known=np.isfinite(res)
    for d in order:
        ix=byd[d]
        for i in ix:
            kk=key[i]
            if kk in s:
                f=0.5**((dn[i]-t[kk])/half); out[i]=s[kk]*f/(nn_[kk]*f+k)
        for i in ix:
            if not known[i]: continue
            kk=key[i]
            if kk in s: f=0.5**((dn[i]-t[kk])/half); s[kk]*=f; nn_[kk]*=f
            s[kk]=s.get(kk,0.0)+res[i]; nn_[kk]=nn_.get(kk,0.0)+1; t[kk]=dn[i]
    return out
J=D["jockey"].astype(str); T=D["trainer"].astype(str); JT=np.char.add(np.char.add(J,"|"),T)
HOT=np.column_stack([enc(J,5,30),enc(J,5,90),enc(T,5,30),enc(T,5,90),enc(JT,5,90)])
HOT=np.column_stack([HOT]+[rrel(HOT[:,j]) for j in range(HOT.shape[1])])
evaluate(V4,"live (blend9 + stage-2 v4)")
evaluate(np.column_stack([V4,HOT]),"live + hot form (30/90-day jockey, trainer, combo)")
