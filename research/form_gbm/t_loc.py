exec(open("t_surcharge.py").read().split("def row(")[0])
def row(nm,m):
    a=lambda mm: f"{prof[mm].mean()*100:+6.1f}% ({mm.sum()})"
    print(f"{nm:56s} bets {m.sum():5d}  per mtg {m.sum()/172:4.1f}  BSP {prof[m].mean()*100:+6.1f}% ({prof[m].sum():+5.0f}u)  older {a(m&~newer):>15s}  newer {a(m&newer):>15s}")
capb=use&(bsp>1)&(1/p<50)&(bsp<3/p)
vb=p*bsp-1
for t in (0.1,0.2,0.3):
    row(f"BSP limit-on-close: back only if BSP >= {1+t:.1f}x ours, no rules",capb&(vb>=t))
    row(f"BSP limit-on-close: >= {1+t:.1f}x ours, risk flags blocked",capb&(vb>=t)&(flags==0))
