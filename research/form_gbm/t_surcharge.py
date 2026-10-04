exec(open("t_trust.py").read().split("halves={")[0])
caps=use&np.isfinite(op)&(op>1)&(bsp>1)&(1/p<50)&(op<3/p)
flags=(fs.astype(int)+fsb+fu_block+bounce+secup+wdown+widebad).astype(float)
v=p*op-1
def row(nm,m):
    a=lambda mm: f"{prof[mm].mean()*100:+6.1f}% ({mm.sum()})"
    print(f"{nm:52s} bets {m.sum():5d}  per mtg {m.sum()/172:4.1f}  BSP {prof[m].mean()*100:+6.1f}% ({prof[m].sum():+5.0f}u)  older {a(m&~newer):>15s}  newer {a(m&newer):>15s}")
print("risk flags per value bet (20c+):", np.bincount(flags[caps&(v>=0.2)].astype(int)))
row("RULES (block on any flag), 20c",caps&(v>=0.2)&(flags==0)&~widebad|caps&(v>=0.2)&(flags==0))
row("no rules at all, 20c",caps&(v>=0.2))
for base in (0.1,0.2):
    for k in (0.2,0.4,0.6,1.0):
        row(f"surcharge: need {int(base*100)}c + {int(k*100)}c per flag",caps&(v>=base+k*flags))
