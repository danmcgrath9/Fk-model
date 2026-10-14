import numpy as np, collections
exec(open('t_m3.py').read().split('import sys')[0])
c=[str(x) for x in D['cols']]; X=D['X']; fsv=np.asarray(X[:,c.index('first_starter')],float); st=np.where(fsv>0.5,0,1)
print('first starters', int((st==0).sum()), 'of', len(st))
pm,ins=samples['HOLD']
r=run(pm,ins,1.2)
races=len(np.unique(ri[ins&race_ok[ri]&np.isfinite(bs)]))
idx=np.array([x[0] for x in r]); stk=np.array([x[1] for x in r]); pl=np.array([x[2] for x in r])
print(f'holdout: {races} races, {len(r)} bets ({len(r)/races:.2f}/race), {stk.sum():.0f}u ({stk.sum()/races:.2f}u/race), {pl.sum():+.0f}u')
fs=(st==0)
fs_short=np.zeros(nR,bool)
for i in np.where(fs&okp&(o<=6))[0]: fs_short[ri[i]]=True
keep=~fs[idx]&~fs_short[ri[idx]]
print(f'after no first starters + first-starter race rule: {keep.sum()} bets ({keep.sum()/races:.2f}/race), {stk[keep].sum():.0f}u, {pl[keep].sum():+.0f}u ({100*pl[keep].sum()/stk[keep].sum():+.1f}%)')
print('races with a short-opening first starter:', fs_short[np.unique(ri[ins])].sum())
# first-up / bounce blocks (fu_json.py logic) on the bench
P=np.asarray(D['P'],float); f={str(n):i for i,n in enumerate(D['past_fields'])}
tr=P[:,:,f['trial']]==1; fin=P[:,:,f['finish']]; days=P[:,:,f['days_before']]; run_=P[:,:,f['runners']]; dist=P[:,:,f['distance']]; rat=P[:,:,f['rating']]; prep=P[:,:,f['prep']]; mg=P[:,:,f['margin']]
real=~tr&np.isfinite(fin)&(fin>0); rd=np.asarray(D['distance'],float)
block=np.zeros(len(ri),bool); early=np.zeros(len(ri),bool)
for k in range(len(ri)):
    jj=np.where(real[k])[0]
    if not len(jj): continue
    j=jj[0]; gap=days[k,j]; rs=False
    if len(jj)>1 and np.isfinite(rat[k,j]):
        best=np.nanmax(rat[k,jj[1:]])
        if np.isfinite(best) and rat[k,j]>=best+3: rs=True
    e = prep[k,j]==1 and (fin[k,j]<=3 or (np.isfinite(mg[k,j]) and mg[k,j]<=2))
    if gap>=60:
        rdk = rd[ri[k]] if len(rd)==nR else rd[k]
        if dist[k,j]-rdk>=200: rs=True
        t=np.where(tr[k]&np.isfinite(fin[k])&(fin[k]>0)&(days[k]<gap))[0]
        if len(t) and (fin[k,t[0]]-1)/max(run_[k,t[0]]-1,1)>0.5: rs=True
    block[k]=rs; early[k]=(not rs) and e
k2=keep & ~block[idx] & ~(early[idx] & (o[idx]>8))
print(f'blocked runners: {block.sum()} of {len(ri)} ({100*block.mean():.0f}%)')
print(f'after ALL live rules (fs, fs race, first-up/bounce blocks, EARLY over $8): {k2.sum()} bets ({k2.sum()/races:.2f}/race), {stk[k2].sum():.0f}u ({stk[k2].sum()/races:.2f}u/race), {pl[k2].sum():+.0f}u ({100*pl[k2].sum()/stk[k2].sum():+.1f}%), {pl[k2].sum()/races:.2f}u/race')
# month by month with every live rule, $50 a unit, expenses $359 (14 Oct 2026, founder: "update the back test")
U=50; COST=359; m=collections.OrderedDict(); rm=collections.Counter(); seen=set()
for i in np.where(ins&race_ok[ri]&np.isfinite(bs))[0]:
    if ri[i] not in seen: seen.add(ri[i]); rm[dates[i][:7]]+=1
for j in np.argsort(dates[idx]):
    if not k2[j]: continue
    k=dates[idx[j]][:7]; a=m.setdefault(k,[0,0.0,0.0,0]); a[0]+=1; a[1]+=stk[j]; a[2]+=pl[j]; a[3]+=won[idx[j]]
print("\n| month | races | bets | won | staked | profit | net of $359 | ROI |")
for k,(n,s,p,w) in m.items(): print(f"| {k} | {rm[k]} | {n} | {w} | ${s*U:,.0f} | ${p*U:+,.0f} | ${p*U-COST:+,.0f} | {100*p/s:+.0f}% |")
T=np.array([v for v in m.values()]).sum(0); print(f"| total | {sum(rm.values())} | {T[0]:.0f} | {T[3]:.0f} | ${T[1]*U:,.0f} | ${T[2]*U:+,.0f} | ${T[2]*U-COST*len(m):+,.0f} | {100*T[2]/T[1]:+.0f}% |")
order=np.argsort(dates[idx]); cum=np.cumsum(np.where(k2,pl,0)[order]); print(f"worst drawdown ${(np.maximum.accumulate(cum)-cum).max()*U:,.0f}")
wk=collections.defaultdict(float)
import datetime
for j in np.where(k2)[0]: wk[datetime.date.fromisoformat(dates[idx[j]]).isocalendar()[:2]]+=pl[j]*U
w=np.array(list(wk.values())); print(f"weeks {len(w)}, losing weeks {(w<0).sum()}, median week ${np.median(w):,.0f}, worst week ${w.min():,.0f}, best ${w.max():,.0f}")
