"""Where our price is still far from BSP (holdout, live stage-2 v6 price p2), and how much of BSP's lead the opening
market already shares: KL to BSP per race, ours / open, by slice."""
import numpy as np, bench as b
D=b.load(); z=np.load('blend_hold.npz'); ri=D['race_idx']; nR=D['n_races']; old,new=b.split(0.7); hold=np.zeros(nR,bool); hold[new]=True
q=D['q']; mk=D['mkt']; p=z['p2']; c={n:i for i,n in enumerate(D['cols'])}
okr=hold&(np.bincount(ri,weights=(q>0)&(mk>0),minlength=nR)==np.bincount(ri,minlength=nR))
def kl_r(p):
    return np.bincount(ri,weights=np.where(q>0,q*np.log(np.maximum(q,1e-300)/np.maximum(p,1e-12)),0),minlength=nR)
ko,km=kl_r(p),kl_r(mk)
fld=np.bincount(ri,minlength=nR); dist=np.asarray(D['distance'],float); trk=D['track'].astype(str)
fs=np.asarray(D['X'][:,c['first_starter']],float)>0.5; nfs=np.bincount(ri,weights=fs,minlength=nR)
METRO={'Flemington','Caulfield','Moonee Valley','Sandown Lakeside','Sandown Hillside','The Valley','Caulfield Heath','Sandown'}
met=np.array([t in METRO for t in trk])
def row(lbl,m):
    m=m&okr; print(f'| {lbl} | {m.sum()} | {ko[m].mean():.3f} | {km[m].mean():.3f} |')
print('| slice | races | ours KL to BSP | opening market |\n|---|---|---|---|')
row('all holdout races',np.ones(nR,bool))
for lo,hi in ((1,8),(8,11),(11,14),(14,99)): row(f'field {lo}-{hi-1}',(fld>=lo)&(fld<hi))
for lo,hi,l in ((0,1201,'sprint to 1200m'),(1201,1601,'1300-1600m'),(1601,2001,'1700-2000m'),(2001,9999,'2100m+')): row(l,(dist>=lo)&(dist<hi))
row('no first starter',nfs==0); row('1 first starter',nfs==1); row('2+ first starters',nfs>=2)
row('metro',met); row('non-metro',~met)
