import numpy as np, bench as b, stage2
src=open("t_s2feat.py").read().split("evaluate(base,")[0]
src=src.replace('p=np.load("p_oof.npy")','p=np.load("p_oof_blend3.npy")').replace('E=np.load("renc_oof.npy")','E=stage2.encodings(rd,D["horse_id"],D["trainer"],D["jockey"],D["sire"],D["track"][ri],res)')
exec(src)
X1=np.column_stack([base,A,Bk,C])
T=np.load("late_feats.npy")  # tempo, late beyond tempo, raw last600, raw to600 (last race run)
tempo,lres=T[:,0],T[:,1]
def rrel(v):
    v2=np.where(np.isfinite(v),v,np.nan); m=np.bincount(ri,weights=np.nan_to_num(v2),minlength=nR)/np.maximum(np.bincount(ri,weights=np.isfinite(v2),minlength=nR),1)
    mx=np.full(nR,-np.inf); np.maximum.at(mx,ri,np.where(np.isfinite(v2),v2,-np.inf))
    return v2-m[ri], v2-mx[ri]
a1,a2=rrel(lres)
LT=np.column_stack([tempo,lres,a1,a2,np.isfinite(lres).astype(float)])
evaluate(X1,"stage-2 current")
evaluate(np.column_stack([X1,LT]),"+ late speed beyond tempo (last run)")
