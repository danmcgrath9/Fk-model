import numpy as np, bench as b
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; won=D["won"]==1; dates=D["date"][ri]; dev=dates<"2026-05-06"
F=np.load("F7.npy"); nm=open("F7_names.txt").read().split("\n"); c={n:i for i,n in enumerate(nm)}; g=lambda n:F[:,c[n]]
p=np.load("p_oof_blend3.npy"); op=D["open"]; bsp=np.where(np.isfinite(D["bsp"])&(D["bsp"]>1),D["bsp"],np.nan)
fair=1/np.maximum(p,1e-9); ev=p*op-1; base=np.isfinite(op)&(op>1)&(fair<50)&(op<3*fair)&np.isfinite(bsp); v20=base&(ev>0.2)
T=np.load("late_feats.npy"); tempo,lres=T[:,0],T[:,1]
P=D["P"].astype(float); f={n:i for i,n in enumerate(D["past_fields"])}; tr=P[:,:,f["trial"]]==1
j=np.argmax(~tr & np.isfinite(P[:,:,f["last600"]]),1); vs=P[np.arange(len(ri)),j,f["vsClass"]]; settle_last=P[np.arange(len(ri)),j,f["settle"]]
ok=np.isfinite(lres); q5=np.nanquantile(lres[ok],0.8); spring=ok&(lres>=q5)&(vs<=0)
def rk(v):  # rank within race, 1 = highest
    out=np.zeros(len(ri)); 
    for r in range(nR):
        s,e=D["starts"][r],D["ends"][r]; x=np.nan_to_num(v[s:e],nan=-1e9); out[s:e]=np.argsort(np.argsort(-x))+1
    return out
es=g("sm_early_speed"); esr=rk(es)
es2=np.zeros(nR); es1=np.zeros(nR); nspeed=np.zeros(nR)
for r in range(nR):
    s,e=D["starts"][r],D["ends"][r]; x=np.sort(np.nan_to_num(es[s:e],nan=0))[::-1]; es1[r]=x[0]; es2[r]=x[1] if len(x)>1 else 0; nspeed[r]=(x>=7).sum()
starts=np.nan_to_num(g("f_careerForm_s"),nan=0); age=g("age"); fu=g("x_is_firstup")==1
lws=D["lws"][ri]; rr_last=g("e_raceRating_last")
C={
 "springboard":spring,
 "springboard, raw late 600 top fifth any class":ok&(lres>=q5),
 "lone leader (fastest early by 1.5+, one speed horse)":(esr==1)&((es1-es2)[ri]>=1.5)&(nspeed[ri]<=1),
 "closer in a hot-pace race (3+ speed, settles back)":(nspeed[ri]>=3)&(np.nan_to_num(settle_last)>=6),
 "on-pace in a slow-pace race (<=1 speed horse, ranked 1-2 early)":(nspeed[ri]<=1)&(esr<=2),
 "first-up, won its last trial":fu&(g("x_trial_last_fin")==1),
 "first-up, 2+ trials in 60 days":fu&(g("e_trials_60")>=2),
 "3yo, 1-3 starts (the Cavill type)":(age==3)&(starts>=1)&(starts<=3),
 "class drop: last race rated 3+ above today's standard":np.isfinite(rr_last)&(rr_last>=lws+3),
 "weight drop 2kg+":g("e_weight_change")<=-2,
 "apprentice claiming":np.nan_to_num(g("apprentice_claim"))>0,
 "second-up after a springboard first-up":spring&(g("x_runs_this_prep")==1),
 "springboard + class drop":spring&np.isfinite(rr_last)&(rr_last>=lws+3),
 "springboard + closer in hot-pace race":spring&(nspeed[ri]>=3),
}
print(f"{'condition':58s} | {'value20 AND condition':42s} | {'every runner with condition':24s}")
for k,m in C.items():
    def roi(s,pr): n=s.sum(); return (pr[s&won].sum()/n-1) if n else np.nan
    s=v20&m; sd,sh=s&dev,s&~dev
    a=base&m
    print(f"{k:58s} | n {sd.sum():4d}/{sh.sum():4d}  open {roi(s,op):+6.1%}  BSP dev {roi(sd,bsp):+6.1%} hold {roi(sh,bsp):+6.1%} | flat BSP dev {roi(a&dev,bsp):+6.1%} hold {roi(a&~dev,bsp):+6.1%}")
s=v20; print(f"{'(reference) value 20c all':58s} | n {(s&dev).sum():4d}/{(s&~dev).sum():4d}  open {op[s&won].sum()/s.sum()-1:+6.1%}  BSP dev {bsp[s&dev&won].sum()/(s&dev).sum()-1:+6.1%} hold {bsp[s&~dev&won].sum()/(s&~dev).sum()-1:+6.1%}")
print()
cd=np.isfinite(rr_last)&(rr_last>=lws+3); late=ok&(lres>=q5)
for k,m in (("class drop",cd),("late top fifth (any class)",late),("springboard",spring),("class drop OR late top fifth",cd|late),("class drop OR springboard",cd|spring)):
    s=v20&m; months={}
    for mo,x,y in zip([d[:7] for d in dates[s]],np.where(won[s],bsp[s],0)-1,np.where(won[s],op[s],0)-1): a=months.setdefault(mo,[0,0,0]); a[0]+=x; a[1]+=y; a[2]+=1
    upb=sum(v[0]>0 for v in months.values()); upo=sum(v[1]>0 for v in months.values())
    n=s.sum(); rb=bsp[s&won].sum()/n-1; ro=op[s&won].sum()/n-1
    se=np.std(np.where(won[s],bsp[s],0))/np.sqrt(n)
    print(f"value20 + {k:32s} bets {n:5d} ({n/456:.1f}/meeting)  open {ro:+.1%}  BSP {rb:+.1%} ±{se:.0%}  months up: BSP {upb}/{len(months)} open {upo}/{len(months)}")
