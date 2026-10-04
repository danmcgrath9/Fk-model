"""One trust layer instead of rules: bet price = log-linear blend of our chance and the opening market's, where the
weight on ours depends on risk factors. Fit on one half of the holdout, tested on the other (both ways)."""
import numpy as np
from scipy.optimize import minimize
exec(open("t_pros.py").read().split("def gr(")[0])
prior_best=np.array([np.nanmax(np.where(real[k],rat[k],np.nan)[j[k]+1:]) if has[k] and real[k,j[k]+1:].any() else np.nan for k in range(n)])
bounce=has&np.isfinite(prior_best)&(ld(rat)>=prior_best+3)
secup=has&(ld(prep)==1)&((ld(fin)<=3)|(ld(mg)<=2)); wdown=(X[:,c["weight"]]-ld(wt))<=-2
bs=X[:,c["raw_barrier_share"]]; ss=X[:,c["raw_settle_share"]]; fld=np.bincount(ri,minlength=nR)[ri]; dd=D["distance"][ri].astype(float)
widebad=(bs>=0.75)&(fld>=10)&((ss>=0.6)|(dd>=1600))
mkt=D["mkt"].astype(float)
okr=np.bincount(ri,weights=(~np.isfinite(mkt)|~np.isfinite(p)).astype(float),minlength=nR)==0
use=hm&okr[ri]&np.isfinite(bsp)
dis=np.log(np.maximum(p,1e-9))-np.log(np.maximum(mkt,1e-9))      # how far we disagree (+ = we like it more)
F=np.column_stack([np.ones(n),fs,fsb,fu_block,bounce,secup,wdown,widebad,np.clip(dis,0,3),np.log(np.maximum(1/mkt,1))]).astype(float)
names=["base","first-starter","race w/ backed FS","first-up block","bounce","second-up","weight down","wide draw","our disagreement","market price (log)"]
lp=np.log(np.maximum(p,1e-9)); lm=np.log(np.maximum(mkt,1e-9))
def pooled(beta,m):
    w=1/(1+np.exp(-(F[m]@beta))); z=w*lp[m]+(1-w)*lm[m]; r_=ri[m]
    mx=np.full(nR,-np.inf); np.maximum.at(mx,r_,z); e=np.exp(z-mx[r_]); return e/np.bincount(r_,weights=e,minlength=nR)[r_]
def loss(beta,m):
    pp=pooled(beta,m); qq=q[m]; return np.sum(np.where(qq>0,qq*np.log(np.maximum(qq,1e-300)/np.maximum(pp,1e-12)),0))/len(np.unique(ri[m]))
def kl(pp,m): qq=q[m]; return np.sum(np.where(qq>0,qq*np.log(np.maximum(qq,1e-300)/np.maximum(pp,1e-12)),0))/len(np.unique(ri[m]))
halves={"older":use&~newer,"newer":use&newer}
res={}
for tr_,te in (("older","newer"),("newer","older")):
    b0=np.zeros(F.shape[1]); b0[0]=1.0
    fit=minimize(loss,b0,args=(halves[tr_],),method="L-BFGS-B")
    beta=fit.x; m=halves[te]; pt=pooled(beta,m)
    print(f"\nfit on {tr_}, test on {te}: KL to BSP  model {kl(p[m],m):.4f}  market {kl(mkt[m],m):.4f}  trust layer {kl(pt,m):.4f}")
    print("  weight on our price (base):", f"{1/(1+np.exp(-beta[0])):.2f}", " shifts:", ", ".join(f"{nm} {b:+.2f}" for nm,b in zip(names[1:],beta[1:])))
    full=np.full(n,np.nan); full[m]=pt; res[te]=full
pt=np.where(newer,res["newer"],res["older"])
caps=use&np.isfinite(op)&(op>1)&(bsp>1)
rules=caps&(p*op-1>=0.2)&(1/p<50)&(op<3/p)&~fs&~fsb&~fu_block&~bounce&~secup&~wdown
def row(nm,m):
    a=lambda mm: f"{prof[mm].mean()*100:+6.1f}% ({mm.sum()})"
    print(f"{nm:46s} bets {m.sum():5d}  BSP {prof[m].mean()*100:+6.1f}% ({prof[m].sum():+5.0f}u)  older {a(m&~newer):>15s}  newer {a(m&newer):>15s}")
print()
row("RULES: value 20c on our price + 6 rules",rules)
for t in (0.05,0.1,0.15,0.2):
    row(f"TRUST LAYER: value {int(t*100)}c on the blended price, no rules",caps&(pt*op-1>=t)&(1/pt<50))
