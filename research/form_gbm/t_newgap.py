"""Why do the backfilled Jul-Oct 2025 races return less? Accuracy against Betfair SP (KL, lower = closer) of our price
and of the opening market, by month, beside the holdout; and how much of our own history each race's features had."""
import json, numpy as np, bench as b, collections
def kl(p,q,ri):
    m=(p>0)&(q>0); return float(np.sum(q[m]*np.log(q[m]/p[m])))/len(np.unique(ri))
def norm_inv(x):
    x=np.asarray(x,float); return np.where(np.isfinite(x)&(x>1),1/np.where(np.isfinite(x)&(x>1),x,1),0)
U=np.load('up_new.npz',allow_pickle=True); ri=U['race_idx']; nR=len(U['race_id'])
rid=U['race_id'].astype(str); hid=U['horse_id'].astype(str); d=U['date'].astype(str)[ri]
key={(rid[ri[i]],hid[i]):i for i in range(len(ri))}; pm=np.zeros(len(ri))
for r in json.load(open('new_v6.json')):
    k=(r['race_id'],r['horse_id'])
    if k in key: pm[key[k]]=r['p']
def rn(v,ri,n): s=np.bincount(ri,weights=v,minlength=n); return v/np.where(s[ri]>0,s[ri],1)
q=rn(norm_inv(U['bsp']),ri,nR); mo=rn(norm_inv(U['open']),ri,nR); pmn=rn(pm,ri,nR)
ok_r=(np.bincount(ri,weights=(q>0)&(mo>0)&(pmn>0),minlength=nR)==np.bincount(ri,minlength=nR))
print('| period | races | ours KL to BSP | opening market KL | ours better by |\n|---|---|---|---|---|')
for lbl,f in [('Jul 2025',lambda x:x.startswith('2025-07')),('Aug 2025',lambda x:x.startswith('2025-08')),('Sep 2025',lambda x:x.startswith('2025-09')),('1-7 Oct 2025',lambda x:x.startswith('2025-10')),('Sep-Oct 2026 additions',lambda x:x>='2026')]:
    m=np.array([f(x) for x in d])&ok_r[ri]
    if not m.any(): continue
    a,c=kl(pmn[m],q[m],ri[m]),kl(mo[m],q[m],ri[m]); print(f'| {lbl} | {len(np.unique(ri[m]))} | {a:.4f} | {c:.4f} | {c-a:+.4f} |')
D=b.load(); z=np.load('blend_hold.npz'); hri=D['race_idx']; old,new=b.split(0.7); hold=np.zeros(D['n_races'],bool); hold[new]=True
qq=D['q']; mk=D['mkt']; p2=z['p2']; m=hold[hri]&(qq>0)&(mk>0)
print(f"| holdout (3 Jun on) | {len(np.unique(hri[m]))} | {kl(p2[m],qq[m],hri[m]):.4f} | {kl(mk[m],qq[m],hri[m]):.4f} | {kl(mk[m],qq[m],hri[m])-kl(p2[m],qq[m],hri[m]):+.4f} |")
