"""What makes our value bets drift? (13 Oct 2026, founder: "on our bets that drift, what are we finding that we are
backing that makes it drift?"). Value-at-open bets under the live rules, HOLD (live stage-2 blend) and OLD (stage-1
OOF blended the same way). DRIFT = BSP at least 1.25x the open, FIRM = BSP at most 0.8x. For each feature group:
drift rate and firm rate against all our value bets, and flat ROI at the open after a 16c deduction."""
import numpy as np, bench as b, collections, datetime as dt
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; n=len(ri); z=np.load("blend_hold.npz")
o=np.asarray(D["open"],float); bs=np.asarray(D["bsp"],float); won=np.asarray(D["finish"],float)==1
Xr=D["X"].astype(float); c=D["colidx"]; col=lambda k: Xr[:,c[k]] if k in c else np.full(n,np.nan)
okp=np.isfinite(o)&(o>1)
old,new=b.split(0.7); hr=np.zeros(nR,bool); hr[np.where(new)[0] if new.dtype==bool else new]=True
def blend(p):
    out=np.zeros(n)
    for r in range(nR):
        ix=np.where(ri==r)[0]
        if not okp[ix].all(): continue
        v=np.exp(0.82*np.log(np.maximum(p[ix],1e-9))+0.22*np.log(1/o[ix])); out[ix]=v/v.sum()
    return out
S_={"HOLD":(z["bl_bsp"],hr[ri]),"OLD":(blend(np.load("p_oof_blend9.npy")),~hr[ri])}
BET={}
for name,(pp,mk) in S_.items():
    BET[name]=(np.array([i for i in range(n) if mk[i] and okp[i] and pp[i]>0 and np.isfinite(bs[i]) and bs[i]>1 and 1.6<=1/pp[i]<=15 and o[i]>=1.2/pp[i] and o[i]<3/pp[i]]),pp)
mv=bs/np.where(okp,o,np.nan)
edge=lambda i,pp: o[i]*pp[i]-1
track=D["track"][ri].astype(str); METRO={"Flemington","Caulfield","Caulfield Heath","Moonee Valley","Sandown Hillside","Sandown Lakeside"}
meet=np.char.add(track,np.char.add("|",D["date"][ri].astype(str))); jk=D["jockey"].astype(str)
cnt=collections.Counter(zip(meet,jk)); only=np.array([cnt[(m,x)]==1 for m,x in zip(meet,jk)])
orank=np.zeros(n)
for r in range(nR):
    ix=np.where(ri==r)[0]; orank[ix[np.argsort(np.where(okp[ix],o[ix],999))]]=np.arange(1,len(ix)+1)
base={k:(np.mean(mv[ix]>=1.25),np.mean(mv[ix]<=0.8)) for k,(ix,pp) in BET.items()}
print("value bets:", {k:len(v[0]) for k,v in BET.items()}, " base drift / firm rate:", {k:f"{a:.0%} / {f:.0%}" for k,(a,f) in base.items()})
rows=[]
def grp(lab,fn):
    out=[]; ok=True; d=[]
    for name in ("HOLD","OLD"):
        ix,pp=BET[name]; g=ix[np.array([bool(fn(i,pp)) for i in ix])] if len(ix) else ix
        if len(g)<40: ok=False; out.append(f"{len(g)} (few)"); continue
        dr=np.mean(mv[g]>=1.25); fr=np.mean(mv[g]<=0.8); roi=np.mean(np.where(won[g],(o[g]-1)*0.84,-1))
        d.append(dr-base[name][0]); out.append(f"{len(g):4d} drift {dr:.0%} firm {fr:.0%} ROI {100*roi:+.0f}%")
    rows.append((lab,out,d if ok else None))
def q(k):
    v=col(k); return np.nanpercentile(v[np.isfinite(v)],[33,67]) if np.isfinite(v).any() else (np.nan,np.nan)
for k,lab in (("raw_days_log","days since last run (log)"),("raw_run_in_prep","run in preparation"),("raw_barrier","barrier"),("raw_dist_change","distance change"),
              ("raw_last","last start finish"),("raw_last_vs_lws","last start rating vs today's standard"),("raw_best_vs_lws","best rating vs today's standard"),
              ("raw_speed","speed rating"),("raw_settle_share","usual settling position (0 lead, 1 back)"),("raw_jockey_win","jockey win %"),("raw_trainer_win","trainer win %"),
              ("raw_weight_rel","weight vs field"),("raw_starts","career starts"),("raw_age","age"),("raw_field_strength","field strength"),("raw_mkt_class","market class"),
              ("raw_neural","Neural rating"),("raw_late_gain","late gain"),("raw_trend_slope","rating trend"),("raw_apprentice_claim","apprentice claim")):
    if k not in c: continue
    lo,hi=q(k); v=col(k)
    grp(f"{lab}: low third",lambda i,pp,v=v,lo=lo: v[i]<=lo); grp(f"{lab}: high third",lambda i,pp,v=v,hi=hi: v[i]>=hi)
grp("jockey's only ride",lambda i,pp: only[i]); grp("metro",lambda i,pp: track[i] in METRO)
grp("open favourite",lambda i,pp: orank[i]==1); grp("open 4th+ in market",lambda i,pp: orank[i]>=4)
grp("edge 20-40%",lambda i,pp: edge(i,pp)<0.4); grp("edge 100%+",lambda i,pp: edge(i,pp)>=1.0)
grp("open $12+",lambda i,pp: o[i]>=12); grp("open under $5",lambda i,pp: o[i]<5)
cons=[r for r in rows if r[2] and np.sign(r[2][0])==np.sign(r[2][1]) and min(abs(r[2][0]),abs(r[2][1]))>=0.04]
cons.sort(key=lambda r: -np.mean(r[2]))
print("\nCONSISTENT in both samples (drift rate at least 4 points off our average in the same direction), most drift-prone first:")
print("| group | HOLD | OLD |\n|---|---|---|")
for lab,out,d in cons: print(f"| {lab} | {out[0]} | {out[1]} |")
