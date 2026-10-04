exec(open("t_surcharge.py").read().split("def row(")[0])
def row(nm,m):
    a=lambda mm: f"{prof[mm].mean()*100:+6.1f}% ({mm.sum()})" if mm.sum() else "-"
    print(f"{nm:40s} bets {m.sum():5d}  per mtg {m.sum()/172:4.1f}  BSP {prof[m].mean()*100:+6.1f}% ({prof[m].sum():+5.0f}u)  older {a(m&~newer):>14s}  newer {a(m&newer):>14s}  wins/model {won[m].sum()/p[m].sum():.2f}")
base=caps&(v>=0.2)&(flags==0); ours=1/p
print("value bets (20c+, all rules) by OUR price:")
for lo,hi in ((1,3),(3,6),(6,10),(10,15),(15,25),(25,50)):
    row(f"ours ${lo}-${hi}",base&(ours>=lo)&(ours<hi))
print(); row("ours $2-$15 only",base&(ours>=2)&(ours<=15)); row("ours over $15",base&(ours>15)); row("open $30+",base&(op>=30))
print("\nvalue bets by our-price band at 10c+ (looser bar inside the band):")
for lo,hi in ((2,6),(6,10),(10,15)):
    row(f"ours ${lo}-${hi}, 10c+",caps&(v>=0.1)&(flags==0)&(ours>=lo)&(ours<hi))
