import numpy as np, json
exec(open("t_backtest_v6.py").read().split("rd=dates")[0])
DED=0.07    # average real TAB deduction on the bets taken so far (Pakenham 16c, 4c; Geelong 7, 0, 4, 5, 13c)
pbl=(p/op)**0.5; stake=np.where(live,np.minimum(4.0,75*np.clip((pbl*op-1)/(op-1),0,None)),0.0)
idx=np.where(live)[0]; rd=dates[ri].astype(str); order=idx[np.argsort(rd[idx],kind="stable")]
s=100*stake[order]; w=won[order]; o=op[order]; b_=bsp[order]
open_=np.where(w,s*(o-1),-s); ded=np.where(w,s*(o*(1-DED)-1),-s); bspp=np.where(w,s*((b_-1)*0.92),-s)
out=dict(dates=list(rd[order]),stake=list(np.round(s,2)),cum_open=list(np.round(np.cumsum(open_),2)),cum_ded=list(np.round(np.cumsum(ded),2)),cum_bsp=list(np.round(np.cumsum(bspp),2)))
months=sorted(set(x[:7] for x in rd[order])); mo={}
for m in months:
    k=np.array([x[:7]==m for x in rd[order]]); mo[m]=dict(open=float(open_[k].sum()),ded=float(ded[k].sum()),bsp=float(bspp[k].sum()),inv=float(s[k].sum()))
out["months"]=mo; out["totals"]=dict(inv=float(s.sum()),open=float(open_.sum()),ded=float(ded.sum()),bsp=float(bspp.sum()),bets=int(len(s)))
json.dump(out,open("curve_v6.json","w"))
t=out["totals"]; print(f"bets {t['bets']} invested ${t['inv']:,.0f}  open ${t['open']:+,.0f} ({t['open']/t['inv']*100:+.1f}%)  open less 7% avg deductions ${t['ded']:+,.0f} ({t['ded']/t['inv']*100:+.1f}%)  BSP ${t['bsp']:+,.0f} ({t['bsp']/t['inv']*100:+.1f}%)")
for m,v in mo.items(): print(m, f"inv {v['inv']:,.0f} open {v['open']:+,.0f} ded {v['ded']:+,.0f} bsp {v['bsp']:+,.0f}")
