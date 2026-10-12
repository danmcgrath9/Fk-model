"""Where the value is (13 Oct 2026, founder: "testing on what bets are good and bad, where we have the most value, and
what markets underrate at timing"). Value-at-open bets under the live rules, split by segment, in TWO samples:
HOLD = the holdout (live stage-2 blend), OLD = the races before it (stage-1 out-of-fold blended with the open the same
way). Per segment: bets, strike, flat ROI at the open raw and after a 16c deduction (the measured average for a bet
struck at the open), flat ROI at BSP, and the median BSP/open (how far the market moved against the open by the jump:
under 1 means it firmed, i.e. the open underrated the horse)."""
import numpy as np, bench as b, datetime as dt, collections
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; z=np.load("blend_hold.npz")
o=np.asarray(D["open"],float); bs=np.asarray(D["bsp"],float); won=np.asarray(D["finish"],float)==1
Xr=D["X"].astype(float); c=D["colidx"]; age=Xr[:,c["age"]]; bar=Xr[:,c["raw_barrier"]]; starts=Xr[:,c["f_careerForm_s"]]
P=D["P"].astype(float); f={str(n):i for i,n in enumerate(D["past_fields"])}; tr=P[:,:,f["trial"]]==1
real=~tr&np.isfinite(P[:,:,f["finish"]])&(P[:,:,f["finish"]]>0); j=np.argmax(real,1); has=real[np.arange(len(ri)),j]
days=np.where(has,P[np.arange(len(ri)),j,f["days_before"]],np.nan)
track=D["track"][ri].astype(str); dist=D["distance"][ri].astype(float); going=D["going"][ri].astype(float); fld=np.bincount(ri,minlength=nR)[ri]
rid=D["race_id"].astype(str)[ri]; rno=np.array([int(x.rsplit("_",1)[1]) for x in rid]); wd=np.array([dt.date.fromisoformat(str(d)[:10]).weekday() for d in D["date"][ri]])
METRO={"Flemington","Caulfield","Caulfield Heath","Moonee Valley","Sandown Hillside","Sandown Lakeside"}
PROV={"Ballarat","Ballarat Synthetic","Bendigo","Cranbourne","Geelong","Kilmore","Mornington","Moe","Pakenham Park","Pakenham Synthetic","Sale","Seymour","Warrnambool","Werribee","Yarra Valley"}
meet=np.char.add(track,np.char.add("|",D["date"][ri].astype(str))); jk=D["jockey"].astype(str)
cnt=collections.Counter(zip(meet,jk)); only=np.array([cnt[(m,x)]==1 for m,x in zip(meet,jk)])
okp=np.isfinite(o)&(o>1); orank=np.zeros(len(ri))
for r in range(nR):
    ix=np.where(ri==r)[0]; v=np.where(okp[ix],o[ix],999); orank[ix[np.argsort(v)]]=np.arange(1,len(ix)+1)
old,new=b.split(0.7)
def blend(p):
    out=np.zeros(len(ri)); 
    for r in range(nR):
        ix=np.where(ri==r)[0]
        if not okp[ix].all(): continue
        v=np.exp(0.82*np.log(np.maximum(p[ix],1e-9))+0.22*np.log(1/o[ix])); out[ix]=v/v.sum()
    return out
samples={"HOLD":z["bl_bsp"],"OLD":blend(np.load("p_oof_blend9.npy"))}
hold_r=set(np.where(new)[0]) if new.dtype==bool else set(new); 
B={}
for name,pp in samples.items():
    rows=[]
    for i in range(len(ri)):
        inh=ri[i] in hold_r
        if (name=="HOLD")!=inh or not okp[i] or pp[i]<=0 or not np.isfinite(bs[i]): continue
        pr=pp[i]; op=o[i]
        if 1.6<=1/pr<=15 and op>=1.2/pr and op<3/pr: rows.append(i)
    B[name]=(np.array(rows),pp)
def seg(lab,fn):
    out=[]
    for name in ("HOLD","OLD"):
        ix,pp=B[name]; ix=ix[[fn(i,pp) for i in ix]] if len(ix) else ix
        n=len(ix)
        if n<20: out.append(f"{n:4d} bets (too few)"+" "*37); continue
        w=won[ix]; fo=np.mean(np.where(w,o[ix]-1,-1)); fd=np.mean(np.where(w,(o[ix]-1)*0.84,-1)); fb=np.mean(np.where(w,(bs[ix]-1)*0.92,-1)); mv=np.median(bs[ix]/o[ix])
        out.append(f"{n:4d} {100*w.mean():3.0f}% {100*fo:+4.0f}% {100*fd:+4.0f}% {100*fb:+4.0f}% {mv:.2f}")
    print(f"| {lab:34s} | {out[0]} | {out[1]} |")
print("| segment | HOLD: bets strike open open-16c BSP BSP/open | OLD: same |\n|---|---|---|")
seg("ALL",lambda i,pp:True)
print("| **price at the open** | | |")
for lo,hi in ((1,3),(3,5),(5,8),(8,12),(12,99)): seg(f"open ${lo}-${hi}",lambda i,pp,lo=lo,hi=hi: lo<=o[i]<hi)
print("| **edge at the open (open x our chance - 1)** | | |")
for lo,hi in ((0.2,0.4),(0.4,0.7),(0.7,1.0),(1.0,9)): seg(f"edge {int(lo*100)}-{int(hi*100)}%",lambda i,pp,lo=lo,hi=hi: lo<=o[i]*pp[i]-1<hi)
print("| **track** | | |")
seg("metro",lambda i,pp: track[i] in METRO); seg("provincial",lambda i,pp: track[i] in PROV); seg("country",lambda i,pp: track[i] not in METRO|PROV)
seg("Saturday",lambda i,pp: wd[i]==5); seg("midweek (Mon-Fri)",lambda i,pp: wd[i]<5); seg("Sunday",lambda i,pp: wd[i]==6)
print("| **race** | | |")
for lo,hi in ((2,9),(9,12),(12,30)): seg(f"field {lo}-{hi-1}",lambda i,pp,lo=lo,hi=hi: lo<=fld[i]<hi)
for lo,hi in ((0,1101),(1101,1401),(1401,1801),(1801,9999)): seg(f"distance {lo}-{hi-1}m",lambda i,pp,lo=lo,hi=hi: lo<=dist[i]<hi)
seg("good track",lambda i,pp: going[i]==1); seg("soft / heavy",lambda i,pp: going[i]>=2)
seg("races 1-3",lambda i,pp: rno[i]<=3); seg("races 4-6",lambda i,pp: 4<=rno[i]<=6); seg("races 7+",lambda i,pp: rno[i]>=7)
print("| **horse** | | |")
seg("2yo / 3yo",lambda i,pp: age[i]<=3); seg("4yo+",lambda i,pp: age[i]>=4)
seg("5 starts or fewer",lambda i,pp: starts[i]<=5); seg("first up (70+ days)",lambda i,pp: days[i]>=70); seg("racing fit (under 70 days)",lambda i,pp: days[i]<70)
seg("barrier 1-4",lambda i,pp: bar[i]<=4); seg("barrier 5-8",lambda i,pp: 5<=bar[i]<=8); seg("barrier 9+",lambda i,pp: bar[i]>=9)
seg("jockey's only ride",lambda i,pp: only[i]); seg("jockey has other rides",lambda i,pp: not only[i])
print("| **market** | | |")
seg("open favourite",lambda i,pp: orank[i]==1); seg("open 2nd-3rd fav",lambda i,pp: 2<=orank[i]<=3); seg("open 4th-6th",lambda i,pp: 4<=orank[i]<=6); seg("open 7th+",lambda i,pp: orank[i]>=7)
