"""Do Form King's section splits (last race runs) sharpen stage 2? Holdout KL to BSP."""
import numpy as np, bench as b, stage2
src=open("t_s2feat.py").read().split("evaluate(base,")[0]
src=src.replace('p=np.load("p_oof.npy")','p=np.load("p_oof_blend3.npy")').replace('E=np.load("renc_oof.npy")','E=stage2.encodings(rd,D["horse_id"],D["trainer"],D["jockey"],D["sire"],D["track"][ri],res)')
exec(src)
X1=np.column_stack([base,A,Bk,C])
N=np.load("ds/model_ds_sec.npz",allow_pickle=True)
key=lambda R,H,I: [f"{R[i]}|{h}" for i,h in zip(I,H)]
old=key(D["race_id"],D["horse_id"],ri); pos={k:i for i,k in enumerate(key(N["race_id"],N["horse_id"],N["race_idx"]))}
m=np.array([pos.get(k,-1) for k in old]); SF={n:i for i,n in enumerate(N["sec_fields"])}
S=np.full((len(m),)+N["S"].shape[1:],np.nan,np.float32); S[m>=0]=N["S"][m[m>=0]]
P=D["P"].astype(float); f={n:i for i,n in enumerate(D["past_fields"])}; tr=P[:,:,f["trial"]]==1
has=~tr & np.isfinite(S[:,:,SF["8-4|vsClass"]])
# last race run with sections, and the mean over up to three
j=np.argmax(has,1); ok=has[np.arange(len(ri)),j]
g=lambda n: np.where(ok,S[np.arange(len(ri)),j,SF[n]],np.nan)
def mean3(n):
    v=np.where(has,S[:,:,SF[n]],np.nan); out=np.full(len(ri),np.nan)
    for i in range(len(ri)):
        w=v[i][np.isfinite(v[i])][:3]
        if len(w): out[i]=w.mean()
    return out
mid,midL,l2F,e8,f6=g("8-4|vsClass"),g("8-4|vsLeader"),g("2-F|vsField"),g("S-8|vsClass"),g("6-F|vsClass")
overall=np.where(ok,P[np.arange(len(ri)),j,f["vsClass"]],np.nan)
gap=mid-overall
movefade=((midL>=1.0)&(l2F<=-1.0)).astype(float); movefade[~ok]=np.nan
mid3=mean3("8-4|vsClass"); f63=mean3("6-F|vsClass")
def rrel(v):
    v2=np.where(np.isfinite(v),v,np.nan); mm=np.bincount(ri,weights=np.nan_to_num(v2),minlength=nR)/np.maximum(np.bincount(ri,weights=np.isfinite(v2),minlength=nR),1)
    return v2-mm[ri]
SEC=np.column_stack([mid,midL,l2F,e8,f6,gap,movefade,mid3,f63,rrel(mid),rrel(mid3),rrel(f63),ok.astype(float)])
evaluate(X1,"stage-2 current")
evaluate(np.column_stack([X1,SEC]),"+ section splits (middle, late, early, move-then-fade)")
evaluate(np.column_stack([X1,mid,midL,l2F,movefade,rrel(mid)]),"+ middle and fade only")
