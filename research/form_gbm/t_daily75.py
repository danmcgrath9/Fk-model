"""Day by day at $75 a unit with every live rule (14 Oct 2026, founder: "Do back test with $75 forward so I know what to
expect... every day per month with how much is bet / returned"). Same method as t_vol.py / t_live_monthly.py: pre-open
orders (3 steps), filled at Form King's open, 16c deduction on winners, live rules on. Also the worst case where TAB cuts
every bet to its guaranteed win ($1,000 non-metro, $2,000 metro)."""
import json, numpy as np
src=open('t_vol.py').read().split("print(f'after ALL live rules")[0]
METRO={'Flemington','Caulfield','Moonee Valley','Sandown Lakeside','Sandown Hillside','The Valley','Caulfield Heath','Sandown'}
U=75; out={}
for S_ in ('HOLD','OLD'):
    g={}; exec(src.replace("pm,ins=samples['HOLD']",f"pm,ins=samples['{S_}']"), g)
    k2,idx,stk,pl,o,won,dates,track,ri,ins,race_ok,bs=(g[x] for x in 'k2 idx stk pl o won dates track ri ins race_ok bs'.split())
    rid=np.asarray(g['D']['race_id']).astype(str)
    days={}
    for i in np.where(ins&race_ok[ri]&np.isfinite(bs))[0]:
        d=days.setdefault(dates[i],{'tracks':set(),'races':set()}); d['tracks'].add(track[i]); d['races'].add(int(ri[i]))
    bets=[]
    for j in np.where(k2)[0]:
        i=idx[j]; lim=2000 if track[i] in METRO else 1000; s=stk[j]*U; od=float(o[i])
        sc=min(s, lim/(od-1)); w=bool(won[i])
        bets.append(dict(d=str(dates[i]),t=str(track[i]),r=int(rid[ri[i]].split('_')[-1]),s=round(s,2),o=od,w=w,
            ret=round(s+s*(od-1)*0.84,2) if w else 0.0, sc=round(sc,2), retc=round(sc+sc*(od-1)*0.84,2) if w else 0.0))
    out[S_]=dict(days={k:dict(tracks=sorted(v['tracks']),races=len(v['races'])) for k,v in days.items()},bets=bets)
    print(S_, len(bets), 'bets', round(sum(b['s'] for b in bets)), 'staked', round(sum(b['ret']-b['s'] for b in bets)), 'profit')
json.dump(out,open('daily75.json','w'))
