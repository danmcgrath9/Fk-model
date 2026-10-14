"""The races the models never trained on (backfilled 14 Oct 2026: 1 Jul to 7 Oct 2025, Sep and Oct 2026 gaps), priced
through the live day pipeline (price_day3 -> apply_stage2f -> shade_back, on the final field), then the same BetMatic
live-rules backtest as t_vol.py / t_daily75.py. Writes daily_new.json in t_daily75.py's format ($75 a unit)."""
import json, numpy as np
src=open('t_m3.py').read().split('import sys')[0]
src=src.replace('D=b.load();','D=b.load("up_new.npz");').replace('z=np.load("blend_hold.npz")','z=None')
src=src.replace('old,new=b.split(0.7); hold_r=np.zeros(nR,bool); hold_r[new]=True\n','')
src=src.replace('samples={"HOLD":(z["p2"],hold_r[ri]),"OLD":(norm(np.load("p_oof_blend9.npy")),~hold_r[ri])}','samples={}')
g={}; exec(src,g); D=g['D']; ri=g['ri']
rid=np.asarray(D['race_id']).astype(str); hid=np.asarray(D['horse_id']).astype(str)
key={(rid[ri[i]],hid[i]):i for i in range(len(ri))}
PM=np.zeros(len(ri))
for r in json.load(open('new_v6.json')):
    k=(r['race_id'],r['horse_id'])
    if k in key: PM[key[k]]=r['p']
print('priced runners',int((PM>0).sum()),'of',len(ri))
g['samples']['NEW']=(PM,np.ones(len(ri),bool))
vol=open('t_vol.py').read().split("print(f'after ALL live rules")[0]
vol=vol.replace("exec(open('t_m3.py').read().split('import sys')[0])\n","").replace("pm,ins=samples['HOLD']","pm,ins=samples['NEW']")
exec(vol,g)
k2,idx,stk,pl,o,won,dates,track,ins,race_ok,bs=(g[x] for x in 'k2 idx stk pl o won dates track ins race_ok bs'.split())
METRO={'Flemington','Caulfield','Moonee Valley','Sandown Lakeside','Sandown Hillside','The Valley','Caulfield Heath','Sandown'}
U=75; days={}
for i in np.where(ins&race_ok[ri]&np.isfinite(bs))[0]:
    d=days.setdefault(str(dates[i]),{'tracks':set(),'races':set()}); d['tracks'].add(str(track[i])); d['races'].add(int(ri[i]))
bets=[]
for j in np.where(k2)[0]:
    i=idx[j]; lim=2000 if track[i] in METRO else 1000; s=stk[j]*U; od=float(o[i]); sc=min(s,lim/(od-1)); w=bool(won[i])
    bets.append(dict(d=str(dates[i]),t=str(track[i]),r=int(rid[ri[i]].split('_')[-1]),s=round(s,2),o=od,w=w,
        ret=round(s+s*(od-1)*0.84,2) if w else 0.0, sc=round(sc,2), retc=round(sc+sc*(od-1)*0.84,2) if w else 0.0))
json.dump(dict(NEW=dict(days={k:dict(tracks=sorted(v['tracks']),races=len(v['races'])) for k,v in days.items()},bets=bets)),open('daily_new.json','w'))
st=sum(b['s'] for b in bets); p=sum(b['ret']-b['s'] for b in bets)
print(f"NEW: {len(days)} days, {sum(len(v['races']) for v in days.values())} races, {len(bets)} bets, staked ${st:,.0f}, profit ${p:+,.0f} ({100*p/st:+.1f}%) at $75")
