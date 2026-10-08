"""Would bets we price UNDER $2 have made money? Same live rules (20c value, open under 3x ours, blocks, back-settler
shade), only the $2 floor removed. 8 Oct 2026, asked about Cranbourne R1 Kotahitanga ($1.91 ours, $2.40 market)."""
import numpy as np
exec(open("t_weightdrop.py").read().split("po_=np.load")[0])
po_=np.load("p_oof_blend9.npy"); pre=~hm&np.isfinite(po_)
def bets_any(pp,mask,blk):
    mkt_=D["mkt"].astype(float)
    okr_=np.bincount(ri,weights=(~np.isfinite(mkt_)|~np.isfinite(pp)).astype(float),minlength=nR)==0
    cp=mask&okr_[ri]&np.isfinite(bsp)&np.isfinite(op)&(op>1)&(bsp>1)&(1/pp<50)&(op<3/pp)
    lv=cp&~blk
    return lv,np.where(lv,np.minimum(4.0,75*np.clip(((pp/op)**0.5*op-1)/(op-1),0,None)),0.0)
for lab,P_,M_ in (("HOLDOUT",shade(p),hm),("BEFORE THE HOLDOUT",shade(po_),pre)):
    L_,S_=bets_any(P_,M_,block_nowd); ours=1/P_; v=P_*op-1
    print(f"\n== {lab}")
    for lo,hi,nm in ((1.0,1.6,"ours under $1.60"),(1.6,2.0,"ours $1.60-$2"),(2.0,3.0,"ours $2-$3 (live)")):
        for vlo,vhi,vn in ((0.2,9,"20c+ value"),(0.2,0.3,"20-30c"),(0.3,9,"30c+")):
            m=L_&(ours>=lo)&(ours<hi)&(v>=vlo)&(v<vhi)
            if m.sum()==0: print(f"  {nm:20s} {vn:10s} bets    0"); continue
            print(f"  {nm:20s} {vn:10s} bets {m.sum():4d}  strike {won[m].mean()*100:5.1f}%  our chance said {P_[m].mean()*100:5.1f}%  market (open) said {(1/op[m]).mean()*100:5.1f}%  open ROI {roi(m,S_,pw_o):+6.1f}%  BSP ROI {roi(m,S_,pw_b):+6.1f}%  avg open ${op[m].mean():.2f}")
