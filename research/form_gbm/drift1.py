import numpy as np, bench as b
D=b.load(); p=np.load("p_oof.npy"); ri=D["race_idx"]; F=np.load("F7.npy"); names=open("F7_names.txt").read().split("\n"); c={n:i for i,n in enumerate(names)}
op=D["open"]; bsp=D["bsp"]; won=D["won"]==1
ok=np.isfinite(op)&(op>1)&np.isfinite(bsp)&(bsp>1); fair=1/np.maximum(p,1e-9); ev=p*op-1
val=ok&(fair<50)&(ev>0.2)&(op<3*fair)
drift=bsp/op>=1.25; firm=bsp/op<0.8
def seg(label, m):
    s=val&m
    if s.sum()<60: return
    n=s.sum(); ro=(op[s&won].sum()-n)/n
    print(f"| {label} | {n} | {drift[s].mean():.0%} | {firm[s].mean():.0%} | {won[s].sum()/p[s].sum():.2f} | {ro:+.0%} |")
print("| value bets at the open, split by | bets | drifted 25%+ | firmed 20%+ | actual/model winners | return at open |")
print("|---|---|---|---|---|---|")
seg("all", np.ones(len(ri),bool))
g=lambda n: F[:,c[n]]
for lab,m in (("open under $5",op<5),("open $5-10",(op>=5)&(op<10)),("open $10-20",(op>=10)&(op<20)),("open $20+",op>=20)):seg(lab,m)
for lab,m in (("model value 20-50c",ev<0.5),("model value 50-100c",(ev>=0.5)&(ev<1)),("model value 100c+",ev>=1)):seg(lab,m)
fs=np.nan_to_num(g("f_careerForm_s"),nan=-1)
seg("first starter",fs==0); seg("1-3 starts",(fs>=1)&(fs<=3)); seg("4-10 starts",(fs>=4)&(fs<=10)); seg("11+ starts",fs>=11)
d=g("daysSinceLastRace"); seg("first-up (60+ days)",np.nan_to_num(d)>=60); seg("backing up (under 60 days)",np.nan_to_num(d,nan=999)<60)
t=g("e_days_trial"); seg("trialled in last 30 days",np.nan_to_num(t,nan=999)<=30)
spd=np.isnan(g("e_speedRating_last")); seg("no speed figures",spd); seg("has speed figures",~spd)
jw=g("jockey_wr"); q=np.nanquantile(jw[val],[0.33,0.67]); seg("jockey strike rate low third",jw<q[0]); seg("jockey strike rate top third",jw>q[1])
tw=g("trainer_wr"); q=np.nanquantile(tw[val],[0.33,0.67]); seg("trainer strike rate low third",tw<q[0]); seg("trainer strike rate top third",tw>q[1])
js=g("j_same_as_last"); seg("same jockey as last start",js==1); seg("jockey change",js==0)
mk=g("raw_mkt_class"); mf=np.exp(-mk); seg("past BSP average under $8",mf<8); seg("past BSP average $8-20",(mf>=8)&(mf<20)); seg("past BSP average $20+",mf>=20)
gear=g("gear_first_time"); seg("first-time gear",gear>0)
fld=D["field"][ri]; seg("field 8 or fewer",fld<=8); seg("field 9-12",(fld>9)&(fld<=12)); seg("field 13+",fld>=13)
age=g("age"); seg("2yo",age==2); seg("3yo",age==3); seg("4yo+",age>=4)
dc=g("e_dist_change"); seg("up 200m+ in trip",dc>=200); seg("back 200m+ in trip",dc<=-200)
bar=g("barrier_share") if "barrier_share" in c else None
lws=D["lws"][ri]; seg("class LWS under 80",lws<80); seg("class LWS 90+",lws>=90)
