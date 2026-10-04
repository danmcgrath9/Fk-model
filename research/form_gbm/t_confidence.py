"""Ideas from outside racing on the live bet set (holdout, all rules, our price $2-$15):
(a) ensemble disagreement as confidence: do bets where trees, net and CatBoost agree do better?
(b) Kelly across runners in a race (mutually exclusive outcomes) vs independent stakes;
(c) shrink our price toward the open before sizing (Kelly under estimation error);
(d) stake by overlay x confidence."""
import numpy as np
exec(open("t_surcharge.py").read().split("def row(")[0])
early_ok=secup&(op<=8); blockset=fs|fsb|fu_block|bounce|wdown|(secup&(op>8))
live=caps&(v>=0.2)&~blockset&(1/p>=2)&(1/p<=15)
pt=np.load("p_oof_f9.npy"); pn_=np.load("p_oof9_nn.npy"); pc=np.load("p_oof9_cb.npy")
comp=np.log(np.stack([pt,pn_,pc]))            # stage-1 parts (OOF); stage-2 moves prices a little but the disagreement is a stage-1 property
spread=comp.std(0)                            # log-odds spread between the three models
po=np.where(won,op-1,-1.0); pb=np.where(won,(bsp-1)*0.92,-1.0)
def rep(nm,m,s=None):
    s=np.ones(n) if s is None else s; s=s[m]; inv=s.sum(); ro=(s*po[m]).sum(); rb=(s*pb[m]).sum()
    print(f"{nm:52s} bets {m.sum():5d}  open {ro/inv*100:+6.1f}%  BSP {rb/inv*100:+6.1f}%  strike {won[m].mean()*100:4.1f}%  wins/model {won[m].sum()/p[m].sum():.2f}  older {np.sum(s*po[m]*~newer[m])/max(np.sum(s*~newer[m]),1e-9)*100:+6.1f}%/{np.sum(s*pb[m]*~newer[m])/max(np.sum(s*~newer[m]),1e-9)*100:+6.1f}%  newer {np.sum(s*po[m]*newer[m])/max(np.sum(s*newer[m]),1e-9)*100:+6.1f}%/{np.sum(s*pb[m]*newer[m])/max(np.sum(s*newer[m]),1e-9)*100:+6.1f}%")
print("(a) ensemble disagreement, live bet set split into thirds by spread:")
qs=np.quantile(spread[live],[1/3,2/3])
rep("models agree (lowest third)",live&(spread<=qs[0])); rep("middle third",live&(spread>qs[0])&(spread<=qs[1])); rep("models disagree (top third)",live&(spread>qs[1]))
# does the component that is longest matter? the bet is value only if the blend is; check the most conservative component
pmin=np.exp(comp.min(0)); 
rep("all three parts say value (min part x open >= 1.2)",live&(pmin*op-1>=0.2)); rep("only the blend says value",live&(pmin*op-1<0.2))
print("\n(c) Kelly sizing after shrinking our chance toward the open (w = weight on ours):")
stake_over=np.minimum(3.0,v/0.2)
rep("stake by overlay, cap 3 (current)",live,stake_over)
for w in (1.0,0.75,0.5):
    ps=np.exp(w*np.log(p)+(1-w)*np.log(1/op)); k=np.clip((ps*op-1)/(op-1),0,1); s=np.minimum(3.0,k*25)
    rep(f"Kelly (x25) on ours shrunk {int(w*100)}% toward open, cap 3",live,s)
print("\n(d) overlay x confidence (agree=1.25, middle=1, disagree=0.75):")
conf=np.where(spread<=qs[0],1.25,np.where(spread<=qs[1],1.0,0.75))
rep("stake by overlay x confidence",live,stake_over*conf)
print("\n(b) races with 2+ live bets: independent stakes vs Kelly across the race:")
r_ids=np.unique(ri[live]); multi=np.array([ (ri==r)&live for r in r_ids if (live&(ri==r)).sum()>=2])
if len(multi):
    mm=np.any(multi,0); rep("races with 2+ bets, independent overlay stakes",mm,stake_over)
    rep("races with 1 bet",live&~mm,stake_over)
    # simple Kelly across runners: for mutually exclusive bets the optimal is to size by (p_i - q_i/(sum of chosen q)) approx; use iterative Thorp-style: f_i = p_i - (1-sum p_S)/(1-sum 1/o_S) * (1/o_i)
    s2=np.zeros(n)
    for m in multi:
        idx=np.where(m)[0]; pi=p[idx]; oi=op[idx]; R=1-pi.sum(); Sg=1-(1/oi).sum()
        fi=pi-(R/Sg)*(1/oi) if Sg>0 else pi-1/oi; fi=np.clip(fi,0,None); s2[idx]=np.minimum(3.0,fi*25)
    rep("races with 2+ bets, Kelly across the race",mm,s2)
