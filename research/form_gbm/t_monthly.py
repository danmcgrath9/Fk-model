"""Month by month at $100 a unit with expenses, and a stricter edge on long ones (14 Oct 2026, founder: "Can you give me a month by month with expenses"; "rate it" on a 30%+ edge for $8-15 horses). BetMatic 8 steps sized at the next step, 5%-shaded minimum, 16c deduction; expenses $359 a month (BetMatic $199 + Form King $160)."""
import numpy as np, bench as b, collections, stake_rule
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; z=np.load("blend_hold.npz")
o=np.asarray(D["open"],float); bs=np.asarray(D["bsp"],float); won=np.asarray(D["finish"],float)==1
okp=np.isfinite(o)&(o>1); fld=np.bincount(ri,minlength=nR)[ri]; race_ok=np.bincount(ri,weights=~okp,minlength=nR)==0
track=D["track"][ri].astype(str); dates=D["date"][ri].astype(str); meet=np.char.add(track,np.char.add("|",dates)); jk=D["jockey"].astype(str)
cnt=collections.Counter(zip(meet,jk)); only=np.array([cnt[(m,x)]==1 for m,x in zip(meet,jk)])
def norm(v):
    s=np.bincount(ri,weights=v,minlength=nR); return v/np.where(s[ri]>0,s[ri],1)
old,new=b.split(0.7); hold_r=np.zeros(nR,bool); hold_r[new]=True
samples={"HOLD":(z["p2"],hold_r[ri]),"OLD":(norm(np.load("p_oof_blend9.npy")),~hold_r[ri])}
DED=0.16; STEPS=(1,1.1,1.2,1.3,1.45,1.6,1.8,2.0); COST=359
def run(pm,ins,long_edge=1.2):
    base=ins&race_ok[ri]&np.isfinite(bs)&(pm>0); q=1/np.maximum(pm,1e-9)
    E=np.where(q>=8,long_edge,1.2); mo=0.95*(E/np.maximum(pm,1e-9)**0.82)**(1/0.78)
    out=[]
    for i in np.where(base&(q>=1.6)&(q<=15)&(o>=mo)&(o<3*q))[0]:
        ch=lambda t: pm[i]**0.82*t**-0.22
        tiers=[mo[i]*s for s in STEPS if mo[i]*s<3*q[i]]; tot=prev=0.0
        for k,t in enumerate(tiers):
            tp=tiers[k+1] if k+1<len(tiers) else t
            s_=stake_rule.stake(ch(tp),tp,only[i],fld[i]); add=max(0.0,s_-prev); prev=max(prev,s_)
            if o[i]>=t: tot+=add
        if tot>0: out.append((i,tot,tot*(o[i]-1)*(1-DED) if won[i] else -tot, q[i]))
    return out
import sys
for name,(pm,ins) in samples.items():
    print(f"\n## {name}: stricter edge on long ones (our price $8-15)")
    print("| long-one edge | bets | staked u | profit u | ROI | long bets | long profit u |\n|---|---|---|---|---|---|---|")
    for E in (1.2,1.3,1.4,1.5):
        r=run(pm,ins,E); st=sum(x[1] for x in r); pl=sum(x[2] for x in r); lg=[x for x in r if x[3]>=8]
        print(f"| {int(round((E-1)*100))}% | {len(r)} | {st:.0f} | {pl:+.0f} | {100*pl/st:+.1f}% | {len(lg)} | {sum(x[2] for x in lg):+.0f} |")
    r=run(pm,ins,1.2); m=collections.OrderedDict()
    allraces=collections.Counter(dates[ri==ri][:0])
    for i,st,pl,_ in sorted(r,key=lambda x: dates[x[0]]):
        k=dates[i][:7]; a=m.setdefault(k,[0,0.0,0.0,0]); a[0]+=1; a[1]+=st; a[2]+=pl; a[3]+=won[i]
    rmonth=collections.Counter(d[:7] for d in dates[np.unique(ri[ins&race_ok[ri]&np.isfinite(bs)],return_index=True)[1]]) if False else None
    races_m=collections.Counter(); seen=set()
    for i in np.where(ins&race_ok[ri]&np.isfinite(bs))[0]:
        if ri[i] not in seen: seen.add(ri[i]); races_m[dates[i][:7]]+=1
    print(f"\n### {name} month by month, $100 a unit, BetMatic 8 steps, expenses ${COST} a month (BetMatic $199 + Form King $160)")
    print("| month | races | bets | won | staked | profit before costs | expenses | net | ROI |\n|---|---|---|---|---|---|---|---|---|")
    T=[0,0,0.0,0.0,0]
    for k,(n,st,pl,w) in m.items():
        print(f"| {k} | {races_m[k]} | {n} | {w} | ${st*100:,.0f} | ${pl*100:+,.0f} | -${COST} | ${pl*100-COST:+,.0f} | {100*pl/st:+.0f}% |")
        T[0]+=races_m[k]; T[1]+=n; T[2]+=st; T[3]+=pl; T[4]+=w
    print(f"| total | {T[0]} | {T[1]} | {T[4]} | ${T[2]*100:,.0f} | ${T[3]*100:+,.0f} | -${COST*len(m):,} | ${T[3]*100-COST*len(m):+,.0f} | {100*T[3]/T[2]:+.0f}% |")
    # worst run
    cum=np.cumsum([x[2] for x in sorted(r,key=lambda x: dates[x[0]])]); dd=(np.maximum.accumulate(cum)-cum).max()
    print(f"biggest drawdown along the way: {dd:.0f}u (${dd*100:,.0f})")
