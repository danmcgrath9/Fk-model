"""Our own bets (live rules, BetMatic method, at the open) by rail band x Form King's predicted style: is there a
betting rule in 'rail out 9m+, on-pace runners win less than their opening price'? Holdout and earlier races."""
import numpy as np, collections
src=open('t_vol.py').read().split("print(f'after ALL live rules")[0]
rail={}
for line in open('race_rails.tsv'):
    p=line.rstrip('\n').split('\t')
    if p[0]=='R': rail[p[1]]=float(p[2])
for S_ in ('HOLD','OLD'):
    g={}; exec(src.replace("pm,ins=samples['HOLD']",f"pm,ins=samples['{S_}']"),g)
    D=g['D']; ri=g['ri']; k2,idx,stk,pl=(g[x] for x in 'k2 idx stk pl'.split())
    rid=D['race_id'].astype(str); c=D['colidx']; fld=np.bincount(ri,minlength=D['n_races'])[ri]
    pos=D['X'][:,c['sm_predicted_position']].astype(float); sh=(pos-1)/np.maximum(fld-1,1)
    sty=np.where(np.isnan(pos),'?',np.where(pos<=1,'lead',np.where(sh<0.34,'on pace',np.where(sh<0.67,'midfield','back'))))
    rm=np.array([rail.get(rid[ri[i]],np.nan) for i in range(len(ri))])
    band=np.where(np.isnan(rm),'?',np.where(rm<=0,'true',np.where(rm<=4,'out 1-4m',np.where(rm<=8,'out 5-8m','out 9m+'))))
    T=collections.defaultdict(lambda:[0,0.0,0.0])
    for j in np.where(k2)[0]:
        i=idx[j]; t=T[(band[i],sty[i])]; t[0]+=1; t[1]+=stk[j]; t[2]+=pl[j]
    print(f"\n### {S_}\n| rail | style | bets | staked u | profit u | ROI |\n|---|---|---|---|---|---|")
    for bnd in ('true','out 1-4m','out 5-8m','out 9m+'):
        for s in ('lead','on pace','midfield','back'):
            t=T[(bnd,s)]
            if t[0]>=10: print(f"| {bnd} | {s} | {t[0]} | {t[1]:.0f} | {t[2]:+.0f} | {100*t[2]/t[1]:+.0f}% |")
