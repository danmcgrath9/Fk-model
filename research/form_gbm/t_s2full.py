import numpy as np, bench as b, os, sys, stage2
PF=sys.argv[1]
src=open("t_s2feat.py").read().split("evaluate(base,")[0]
src=src.replace('p=np.load("p_oof.npy")',f'p=np.load("{PF}")')
src=src.replace('E=np.load("renc_oof.npy")','E=stage2.encodings(rd,D["horse_id"],D["trainer"],D["jockey"],D["sire"],D["track"][ri],res)')
exec(src)
print(b.fmt("stage-1 blend hold",b.score(p,hold)))
evaluate(base,"stage-2 (encodings)")
p2=evaluate(np.column_stack([base,A,Bk,C]),"stage-2 + stable/jockey/trend")
np.save(PF.replace(".npy","_s2hold.npy"),p2)
