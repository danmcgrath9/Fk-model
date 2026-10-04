"""The whole backtest of the live betting rules on the holdout (races from 6 May 2026 the model never trained on):
value 20c+ on our stage-2 v4 price, our price $2-$15, caps, first-starter rules, first-up block, bounce, weight-down,
second-up early-only at $8 or shorter; staked Kelly x75 on a 50/50 blend of our chance and the market's, cap 4u, $100 a unit. Settled at the back-filled
opening price (no deductions available) and at BSP less 8% commission."""
import numpy as np, json, os, html
exec(open("t_surcharge.py").read().split("def row(")[0])
early_ok=secup&(op<=8); blockset=fs|fsb|fu_block|bounce|wdown|(secup&(op>8))
live=caps&(v>=0.2)&~blockset&(1/p>=2)&(1/p<=15)
pbl=(p/op)**0.5; stake=np.where(live,np.minimum(4.0,75*np.clip((pbl*op-1)/(op-1),0,None)),0.0)   # final plan: Kelly x75 on the 50/50 blend, cap 4
edge=np.load("edge_mask.npy").astype(bool) if os.path.exists("edge_mask.npy") else None
if edge is not None and edge.shape[0]!=n: edge=None
rd=dates[ri].astype(str); mk=np.char.add(rd,D["track"][ri].astype(str))
po=np.where(won,op-1,-1.0); pb=np.where(won,(bsp-1)*0.92,-1.0)
def st(m,s=None):
    s=stake[m] if s is None else s[m]; inv=100*s.sum(); ro=100*(s*(po[m]+1)).sum(); rb=100*(s*(pb[m]+1)).sum(); w=won[m].sum()
    return dict(bets=int(m.sum()),wins=int(w),invested=inv,ret_open=ro,ret_bsp=rb,roi_open=(ro-inv)/inv*100 if inv else 0,roi_bsp=(rb-inv)/inv*100 if inv else 0,strike=w/max(m.sum(),1)*100,avg=float(np.mean(op[m])) if m.any() else 0,avgw=float(np.mean(op[m&won])) if (m&won).any() else 0)
rows=[]
def add(section,label,m,s=None): r=st(m,s); r.update(section=section,label=label); rows.append(r); return r
add("Overall","Live rules, Kelly on the 50/50 blend (final plan)",live)
add("Overall","Live rules, flat $100",live,np.ones(n))
add("Overall","Top pick (model favourite), flat $100",hm&np.isfinite(op)&(op>1)&np.isfinite(bsp)&(bsp>1)&(p==np.array([p[ri==r].max() for r in range(nR)])[ri]),np.ones(n))
if edge is not None: add("Overall","EDGE only (an angle as well)",live&edge)
pj=np.load("ds/model_ds.npz",allow_pickle=True)["pre_jump"]; add("Overall","Live-pulled races only (real opening prices)",live&pj[ri])
for mth in sorted(set(rd[live])):
    m=live&(rd==mth[:7]) if False else live&np.char.startswith(rd,mth[:7])
    if mth[:7] not in [r["label"] for r in rows if r["section"]=="By month"]: add("By month",mth[:7],m)
for lo,hi in ((2,4),(4,6),(6,9),(9,12),(12,15)): add("By our price",f"${lo} to ${hi}",live&(1/p>=lo)&(1/p<hi))
for lo,hi in ((1,5),(5,10),(10,20),(20,45)): add("By opening price",f"${lo} to ${hi}",live&(op>=lo)&(op<hi))
for lo,hi in ((0.2,0.3),(0.3,0.5),(0.5,1.0),(1.0,9)): add("By overlay",f"{int(lo*100)}c to {int(hi*100)}c over" if hi<9 else "100c+ over",live&(v>=lo)&(v<hi))
add("By type","Early-only (second-up, $8 or shorter)",live&early_ok); add("By type","Everything else",live&~early_ok)
for g,lab in ((1,"Good / firm"),(2,"Soft"),(3,"Heavy"),(4,"Synthetic")):
    m=live&(D["going"][ri]==g)
    if m.sum(): add("By going",lab,m)
# bank path: cumulative profit in date order, drawdown
idx=np.where(live)[0]; order=idx[np.argsort(rd[idx],kind="stable")]
cum=np.cumsum(100*stake[order]*po[order]); peak=np.maximum.accumulate(np.concatenate([[0],cum]))[1:]; dd=(peak-cum).max()
cumb=np.cumsum(100*stake[order]*pb[order]); peakb=np.maximum.accumulate(np.concatenate([[0],cumb]))[1:]; ddb=(peakb-cumb).max()
run=best=0
for k in order:
    run=0 if won[k] else run+1; best=max(best,run)
meets=len(np.unique(mk[live])); allm=len(np.unique(mk[hm]))
summary=dict(races=int(len(np.unique(ri[hm]))),meetings=int(allm),meetings_with_bet=int(meets),bets_per_meeting=float(live.sum()/allm),max_drawdown_open=float(dd),max_drawdown_bsp=float(ddb),longest_losing_run=int(best),
             worst_month_open=min((r for r in rows if r["section"]=="By month"),key=lambda r:r["ret_open"]-r["invested"])["label"])
json.dump(dict(rows=rows,summary=summary),open("backtest_full.json","w"),indent=1)
for r in rows: print(f"{r['section']:16s} {r['label']:40s} bets {r['bets']:5d} inv ${r['invested']:>9,.0f} open ${r['ret_open']-r['invested']:>+9,.0f} ({r['roi_open']:+5.1f}%) BSP ${r['ret_bsp']-r['invested']:>+9,.0f} ({r['roi_bsp']:+5.1f}%) strike {r['strike']:4.1f}% avg ${r['avg']:5.2f}")
print(summary)
