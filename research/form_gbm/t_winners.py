"""How our price, the opening market and Betfair SP each do at picking WINNERS (holdout, and the 2025 races the models
never trained on): log loss (lower = better), favourite strike rate, and calibration by price band."""
import json, numpy as np, bench as b, collections
def norm_inv(x):
    x=np.asarray(x,float); ok=np.isfinite(x)&(x>1); return np.where(ok,1/np.where(ok,x,1),0)
def rn(v,ri,n): s=np.bincount(ri,weights=v,minlength=n); return v/np.where(s[ri]>0,s[ri],1)
def report(lbl,ri,won,P):
    n=int(ri.max())+1; ok=np.ones(n,bool)
    for p in P.values(): ok&=np.bincount(ri,weights=p>0,minlength=n)==np.bincount(ri,minlength=n)
    ok&=np.bincount(ri,weights=won,minlength=n)==1
    m=ok[ri]; races=ok.sum()
    print(f'\n### {lbl}: {races} races\n| price | log loss vs winners | favourite won | winners at $1.01-3 / 3-6 / 6-12 / 12+ (expected vs actual) |\n|---|---|---|---|')
    for k,p in P.items():
        pw=p[m&won]; ll=-np.mean(np.log(np.maximum(pw,1e-9)))
        fav=0
        for r in np.where(ok)[0]:
            ii=np.where(ri==r)[0]; fav+=won[ii[np.argmax(p[ii])]]
        bands=[]
        for lo,hi in ((1,3),(3,6),(6,12),(12,1e9)):
            mm=m&(1/np.maximum(p,1e-9)>=lo)&(1/np.maximum(p,1e-9)<hi); bands.append(f'{p[mm].sum():.0f} / {won[mm].sum():.0f}')
        print(f'| {k} | {ll:.4f} | {fav} ({100*fav/races:.1f}%) | {" · ".join(bands)} |')
D=b.load(); z=np.load('blend_hold.npz'); ri=D['race_idx']; old,new=b.split(0.7); hold=np.zeros(D['n_races'],bool); hold[new]=True
m=hold[ri]; rim=np.unique(ri[m],return_inverse=True)[1]; won=(D['finish'][m]==1)
report('Holdout, 3 Jun to 9 Oct 2026', rim, won, {'Our price':z['p2'][m], 'Opening market':rn(D['mkt'][m],rim,rim.max()+1), 'Betfair SP':D['q'][m]})
U=np.load('up_new.npz',allow_pickle=True); uri=U['race_idx']; rid=U['race_id'].astype(str); hid=U['horse_id'].astype(str)
key={(rid[uri[i]],hid[i]):i for i in range(len(uri))}; pm=np.zeros(len(uri))
for r in json.load(open('new_v6.json')):
    k=(r['race_id'],r['horse_id'])
    if k in key: pm[key[k]]=r['p']
mm=U['date'].astype(str)[uri]<'2026'; r2=np.unique(uri[mm],return_inverse=True)[1]; n2=r2.max()+1
report('Jul to 7 Oct 2025, races the models never trained on', r2, U['finish'].astype(float)[mm]==1,
       {'Our price':rn(pm[mm],r2,n2),'Opening market':rn(norm_inv(U['open'][mm]),r2,n2),'Betfair SP':rn(norm_inv(U['bsp'][mm]),r2,n2)})
