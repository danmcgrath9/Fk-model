exec(open("t_pros.py").read().split("def gr(")[0])
newpeak=None
prior_best=np.array([np.nanmax(np.where(real[k],rat[k],np.nan)[j[k]+1:]) if has[k] and real[k,j[k]+1:].any() else np.nan for k in range(n)])
bounce=has&np.isfinite(prior_best)&(ld(rat)>=prior_best+3)
secup=has&(ld(prep)==1)&((ld(fin)<=3)|(ld(mg)<=2))
wdown=(X[:,c["weight"]]-ld(wt))<=-2
mk=np.char.add(dates[ri].astype(str),D["track"][ri].astype(str)); nmeet=len(np.unique(mk[hm]))
base=hm&np.isfinite(op)&(op>1)&np.isfinite(bsp)&(bsp>1)&(p*op-1>=0.2)&(1/p<50)&(op<3/p)
def row(nm,m):
    print(f"{nm:52s} bets {m.sum():5d}  per meeting {m.sum()/nmeet:4.1f}  meetings with a bet {len(np.unique(mk[m]))/nmeet*100:3.0f}%  BSP {prof[m].mean()*100:+6.1f}% ({prof[m].sum():+.0f}u)")
print("meetings in holdout:",nmeet)
m=base.copy(); row("value 20c+, price caps only",m)
m=m&~fs&~fsb; row("+ first-starter rules",m)
m1=m&~fu_block; row("+ first-up block",m1)
row("+ first-up + bounce",m1&~bounce)
row("+ first-up + bounce + second-up",m1&~bounce&~secup)
row("+ first-up + bounce + second-up + weight-down (now)",m1&~bounce&~secup&~wdown)
row("first-up + bounce + weight-down (drop second-up)",m1&~bounce&~wdown)
for t in (0.1,0.15,0.3):
    vt=hm&np.isfinite(op)&(op>1)&np.isfinite(bsp)&(bsp>1)&(p*op-1>=t)&(1/p<50)&(op<3/p)&~fs&~fsb&~fu_block&~bounce&~secup&~wdown
    row(f"all rules, value {int(t*100)}c+",vt)
