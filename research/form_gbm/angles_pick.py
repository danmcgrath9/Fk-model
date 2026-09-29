import numpy as np, bench as b
exec(open("angles.py").read().split("def roi(s,pr):")[0])
def roi(s,pr):
    n=s.sum(); return (pr[s&won].sum()/n-1) if n else np.nan
names=list(A.keys()); M=[np.asarray(A[k],bool) for k in names]
picked=[k for k,m in zip(names,M) if (v20&m&dev).sum()>=60 and roi(v20&m&dev,bsp)>0.05 and not k.startswith("26")]
print("picked on OLDER races only (value 20c + angle, BSP ROI > +5%, 60+ bets):"); [print("  ",k) for k in picked]
U=np.zeros(len(ri),bool)
for k in picked: U|=np.asarray(A[k],bool)
cnt=sum(np.asarray(A[k],bool).astype(int) for k in picked)
for lab,s in (("value 20c + any picked angle",v20&U),("value 20c + 2 or more picked angles",v20&(cnt>=2)),("value 20c, no picked angle",v20&~U)):
    se=lambda m: np.std(np.where(won[m],bsp[m],0))/np.sqrt(max(m.sum(),1))
    print(f"{lab:40s} older: {(s&dev).sum():5d} bets BSP {roi(s&dev,bsp):+.1%} | NEWER (untouched): {(s&hold).sum():5d} bets BSP {roi(s&hold,bsp):+.1%} ±{se(s&hold):.0%}, open {roi(s&hold,op):+.1%}  | {s.sum()/456:.1f} bets/meeting")
np.save("edge_mask.npy",U); np.save("edge_count.npy",cnt); open("edge_picked.txt","w").write("\n".join(picked))
