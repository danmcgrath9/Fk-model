"""Ideas from Vince Accardi (Race Speed Profiles) and Dan O'Sullivan, tested in stage 2 on the
holdout races, same harness as t_b9_s2 (base = blend9 + stage-2 v4 = live)."""
import numpy as np, bench as b, stage2
src=open("t_s2feat.py").read().split("def evaluate")[0]
src=src.replace('p=np.load("p_oof.npy")','p=np.load("p_oof_blend9.npy")').replace('E=np.load("renc_oof.npy")','E=stage2.encodings(rd,D["horse_id"],D["trainer"],D["jockey"],D["sire"],D["track"][ri],res)')
exec(src)
S=np.load("S_hist.npy").astype(float); SF={str(n):i for i,n in enumerate(np.load("S_fields.npy",allow_pickle=True))}
P=D["P"].astype(float); f={str(n):i for i,n in enumerate(D["past_fields"])}
SEC=stage2.sections(S,np.load("S_fields.npy",allow_pickle=True),D["P"],D["past_fields"],ri,nR)
TR=stage2.trials(D["P"],D["past_fields"],ri)
pass
n=len(ri); ar=np.arange(n); trial=P[:,:,f["trial"]]==1; race=~trial&np.isfinite(P[:,:,f["finish"]])&(P[:,:,f["finish"]]>0)
def rrel(v):
    fin=np.isfinite(v); m=np.bincount(ri,weights=np.where(fin,v,0),minlength=nR)/np.maximum(np.bincount(ri,weights=fin,minlength=nR),1); return np.where(fin,v-m[ri],np.nan)
# 1. Accardi: early / middle / late each above the field (last race run with sections; best of last three)
hs=race&np.isfinite(S[:,:,SF["8-4|vsField"]])
cnt=np.nansum([(S[:,:,SF[k]]>0) for k in ("S-8|vsField","8-4|vsField","4-F|vsField")],0).astype(float); cnt=np.where(hs,cnt,np.nan)
j=np.argmax(hs,1); ok=hs[ar,j]; last_cnt=np.where(ok,cnt[ar,j],np.nan)
rk=np.cumsum(hs,1); best3=np.where((hs&(rk<=3)).any(1),np.nanmax(np.where(hs&(rk<=3),cnt,-1),1),np.nan)
X1=np.column_stack([last_cnt,best3,(last_cnt==3).astype(float),rrel(last_cnt)])
# 2. Accardi BTP: best rating this preparation vs the last run (vsClass), and the gap
vc=np.where(race,P[:,:,f["vsClass"]],np.nan); prep=P[:,:,f["prep"]]
jr=np.argmax(race,1); okr=race[ar,jr]; lastprep=np.where(okr,prep[ar,jr],np.nan)
same=race&(prep==lastprep[:,None])&np.isfinite(vc)
btp=np.where(same.any(1),np.nanmax(np.where(same,vc,-99),1),np.nan); lastvc=np.where(okr,vc[ar,jr],np.nan)
X2b=np.column_stack([btp,btp-lastvc,rrel(btp)])
# 3. Accardi WTI / O'Sullivan wet: rating on wet (soft/heavy) runs minus on good runs, overall and last 600, x wet today
gb=P[:,:,f["going_band"]]; wet=race&((gb==2)|(gb==3)); dry=race&(gb==1)
def avg(m,v): c=(m&np.isfinite(v)).sum(1); return np.where(c>0,np.nansum(np.where(m,v,0),1)/np.maximum(c,1),np.nan),c
wv,wc=avg(wet,vc); dv,dc=avg(dry,vc)
l6=np.where(race,S[:,:,SF["6-F|vsClass"]],np.nan); wl,_=avg(wet,l6); dl,_=avg(dry,l6)
wti=wv-dv; wti6=wl-dl; today_wet=np.isin(D["going"][ri],[2,3]).astype(float)
X3=np.column_stack([wti,wti6,wc,today_wet*np.nan_to_num(wti,nan=0),today_wet*np.nan_to_num(wti6,nan=0),rrel(today_wet*np.nan_to_num(wti,nan=0))])
# 4. Accardi best zone: where winners sat at the 800 at this track and going (training races only), vs the horse's usual spot
p8=P[:,:,f["pos800"]]/np.maximum(P[:,:,f["runners"]],1); fin=P[:,:,f["finish"]]
TRK=D["track"][ri]; GO=D["going"][ri]; rdate=D["date"][ri]
train_mask=np.isin(ri,dev)   # zone table from the development races only, never the holdout
key=np.char.add(TRK.astype(str),np.char.add("|",GO.astype(str)))
win_today=(D["finish"]==1)&train_mask&np.isfinite(D["X"][:,D["colidx"]["sm_predicted_position"]]) if "sm_predicted_position" in D["colidx"] else None
habit=np.where(race&np.isfinite(p8)&(rk<=3) if False else race&np.isfinite(p8),p8,np.nan); habit=np.nanmean(np.where(np.cumsum(race&np.isfinite(p8),1)<=3,habit,np.nan),1)
zone={}
for k in np.unique(key[train_mask]):
    m=(key==k)&train_mask&(D["finish"]==1)&np.isfinite(habit)
    if m.sum()>=15: zone[k]=float(np.median(habit[m]))
zv=np.array([zone.get(k,np.nan) for k in key]); dz=habit-zv
X4=np.column_stack([zv,dz,np.abs(dz),rrel(np.abs(dz))])

pb=np.load("p_oof_blend9.npy"); op=D["open"].astype(float); bsp=D["bsp"].astype(float); won=D["finish"]==1
val=np.isfinite(op)&(op>1)&np.isfinite(bsp)&(bsp>1)&(pb*op-1>=0.2)
newer=np.isin(ri,hold)
prof=np.where(won,(bsp-1)*0.92,-1.0)
def rep(m,lab):
    for nm,mm in (("all",m),("newer",m&newer)):
        n=mm.sum(); print(f"  {lab:42s} {nm:5s} bets {n:5d}  BSP ROI {prof[mm].mean()*100 if n else float('nan'):+6.1f}%")
rep(val,"value 20c+ (all)")
rep(val&(last_cnt==3),"+ all three sections above field last run")
rep(val&(last_cnt<=1),"+ at most one section above field")
rep(val&np.isfinite(btp)&(btp-lastvc<=0.5),"+ last run within 0.5L of best this prep")
rep(val&np.isfinite(btp)&(btp-lastvc>=3),"+ last run 3L+ below best this prep")
rep(val&(today_wet==1)&(wti>=1),"+ wet today, rates 1L+ better wet")
rep(val&(today_wet==1)&(wti<=-1),"+ wet today, rates 1L+ worse wet")
rep(val&np.isfinite(dz)&(np.abs(dz)<=0.1),"+ usual spot inside the winners' zone")
rep(val&np.isfinite(dz)&(np.abs(dz)>=0.3),"+ usual spot far from the zone")
