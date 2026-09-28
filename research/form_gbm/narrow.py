import numpy as np, bench as b
D=b.load(); p=np.load("p_oof.npy"); dp=np.load("drift_pred.npy"); ri=D["race_idx"]; F=np.load("F7.npy")
names=open("F7_names.txt").read().split("\n"); c={n:i for i,n in enumerate(names)}; g=lambda n: F[:,c[n]]
op=D["open"]; bsp=D["bsp"]; won=D["won"]==1; dates=D["date"][ri]
ok=np.isfinite(op)&(op>1)&np.isfinite(bsp)&(bsp>1); fair=1/np.maximum(p,1e-9); ev=p*op-1
base=ok&(fair<50)&(op<3*fair)
udates=np.array(sorted(set(D["date"]))); cut=udates[int(len(udates)*0.6)]
dev=dates<cut; hold=dates>=cut
ndays={"dev":len(set(dates[dev])),"hold":len(set(dates[hold]))}
fs=np.nan_to_num(g("f_careerForm_s"),nan=-1); spd=~np.isnan(g("e_speedRating_last")); age=g("age"); fld=D["field"][ri]
solid=(fs>=1)&spd&(age!=2)
dq=np.quantile(dp[base&(ev>0.2)&dev],0.6)
# best value bet per race
best=np.zeros(len(ri),bool)
for r in range(D["n_races"]):
    s,e=D["starts"][r],D["ends"][r]; m=base[s:e]&(ev[s:e]>0)
    if m.any(): j=np.argmax(np.where(m,ev[s:e],-9)); best[s+j]=True
def stats(sel,part):
    s=sel&part; n=s.sum()
    if n<30: return f"{n:5d} bets (too few)"
    ro=(op[s&won].sum()-n)/n; rt=((op[s&won]/1.10).sum()-n)/n; rb=(bsp[s&won].sum()-n)/n
    se=np.std(np.where(won[s],op[s],0)-1)/np.sqrt(n); key="dev" if part is dev else "hold"
    return f"{n:5d} bets {n/ndays[key]:4.1f}/day  strike {won[s].mean():5.1%}  open {ro:+6.1%} ±{se:3.0%}  open-10% {rt:+6.1%}  BSP {rb:+6.1%}"
rules={
 "A all value 20c+":           base&(ev>0.2),
 "B value 50c+":               base&(ev>0.5),
 "C value 100c+":              base&(ev>1.0),
 "D 20c+ solid (raced, speed figs, not 2yo)": base&(ev>0.2)&solid,
 "E 50c+ solid":               base&(ev>0.5)&solid,
 "F 20c+ not a predicted drifter": base&(ev>0.2)&(dp<dq),
 "G 50c+ solid, not predicted drifter": base&(ev>0.5)&solid&(dp<dq),
 "H 50c+ solid, open $3-$20":  base&(ev>0.5)&solid&(op>=3)&(op<=20),
 "I 50c+ solid, $3-$20, field 12 or fewer": base&(ev>0.5)&solid&(op>=3)&(op<=20)&(fld<=12),
 "J best bet per race, 50c+ solid": base&best&(ev>0.5)&solid,
 "K best bet per race, 50c+ solid, not drifter, $3-$20": base&best&(ev>0.5)&solid&(dp<dq)&(op>=3)&(op<=20),
 "L 100c+ solid, $3-$30":      base&(ev>1.0)&solid&(op>=3)&(op<=30),
}
print(f"dev: {ndays['dev']} race days to {cut}; holdout: {ndays['hold']} race days from {cut}\n")
for k,sel in rules.items():
    print(k); print("   dev    ", stats(sel,dev)); print("   holdout", stats(sel,hold))
