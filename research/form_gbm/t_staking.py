exec(open("t_surcharge.py").read().split("def row(")[0])
prof_o=np.where(won,op-1,-1.0)
m=caps&(v>=0.2)&(flags==0)&(1/p<=15)   # the live bet set: value 20c+, all rules, our price $2-$15
ev=v[m]; o=op[m]; w=won[m]; pb=bsp[m]; pm=p[m]
kelly=np.clip((pm*o-1)/(o-1),0,1)            # full Kelly at the open
def report(nm,stake):
    s=stake/stake.mean()                      # scale so the average bet is 1 unit ($100)
    po=(np.where(w,o-1,-1.0)*s); pbp=(np.where(w,(pb-1)*0.92,-1.0)*s)
    print(f"{nm:34s} bets {m.sum():4d}  turnover {100*s.sum():>9,.0f}  open {100*po.sum():>+9,.0f} ({po.sum()/s.sum()*100:+5.1f}%)  BSP {100*pbp.sum():>+9,.0f} ({pbp.sum()/s.sum()*100:+5.1f}%)  biggest stake {100*s.max():,.0f}")
report("flat $100",np.ones(m.sum()))
report("stake x value (20c=1, 60c=3)",ev/0.2)
report("quarter Kelly",kelly*0.25)
report("Kelly capped at 3 units",np.minimum(kelly*25,3)/1.0)
report("flat, but double under $6",np.where(o<6,2.0,1.0))
