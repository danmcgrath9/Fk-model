"""Is BSP sharp, and where is it not? (13 Oct 2026, founder: "test if BSP is actually sharp, and where there are edges at
BSP, to make our model sharper than BSP"). Every runner with a BSP in races where every runner has one. A/E = actual wins /
BSP-implied wins (BSP chances normalised to 100% per race; 1.00 = priced right, above = BSP underrates). ROI = flat 1u on
every runner in the group at BSP, gross and after 8% commission on winnings. Two halves by date (EARLY / LATE) so a
segment only counts if it holds in both."""
import numpy as np, bench as b, datetime as dt, collections
D=b.load(); ri=D["race_idx"]; nR=D["n_races"]; n=len(ri); ar=np.arange(n)
bs=np.asarray(D["bsp"],float); o=np.asarray(D["open"],float); won=np.asarray(D["finish"],float)==1
ok=np.isfinite(bs)&(bs>1); full=np.bincount(ri,weights=ok,minlength=nR)==np.bincount(ri,minlength=nR); use=full[ri]
v=np.where(ok,1/np.where(ok,bs,2),0); pb=v/np.maximum(np.bincount(ri,weights=v,minlength=nR)[ri],1e-9)
book=np.bincount(ri,weights=v,minlength=nR)
Xr=D["X"].astype(float); c=D["colidx"]; age=Xr[:,c["age"]]; bar=Xr[:,c["raw_barrier"]]; starts=Xr[:,c["f_careerForm_s"]]
P=D["P"].astype(float); f={str(x):i for i,x in enumerate(D["past_fields"])}
real=~(P[:,:,f["trial"]]==1)&np.isfinite(P[:,:,f["finish"]])&(P[:,:,f["finish"]]>0); j=np.argmax(real,1); has=real[ar,j]
days=np.where(has,P[ar,j,f["days_before"]],np.nan)
Sh=np.load("S_hist.npy").astype(float); SF={str(x):i for i,x in enumerate(np.load("S_fields.npy",allow_pickle=True))}
hs=real&np.isfinite(Sh[:,:,SF["4-F|vsClass"]]); jj=np.argmax(hs,1); late=np.where(hs[ar,jj],Sh[ar,jj,SF["4-F|vsClass"]],np.nan)
lq=np.nanpercentile(late[use&np.isfinite(late)],[15,85])
track=D["track"][ri].astype(str); dist=D["distance"][ri].astype(float); fld=np.bincount(ri,minlength=nR)[ri]
wd=np.array([dt.date.fromisoformat(str(d)[:10]).weekday() for d in D["date"][ri]])
METRO={"Flemington","Caulfield","Caulfield Heath","Moonee Valley","Sandown Hillside","Sandown Lakeside"}
meet=np.char.add(track,np.char.add("|",D["date"][ri].astype(str))); jk=D["jockey"].astype(str)
cnt=collections.Counter(zip(meet,jk)); only=np.array([cnt[(m,x)]==1 for m,x in zip(meet,jk)])
brank=np.zeros(n)
for r in range(nR):
    ix=np.where(ri==r)[0]; brank[ix[np.argsort(np.where(ok[ix],bs[ix],999))]]=np.arange(1,len(ix)+1)
mv=np.where(np.isfinite(o)&(o>1),bs/o,np.nan)
dates=D["date"][ri].astype(str); cut=np.median(dates[use].astype("datetime64[D]").astype(int))
early=dates.astype("datetime64[D]").astype(int)<=cut
def seg(lab,m):
    out=[]
    for half in (early,~early):
        g=m&use&half; nn=g.sum()
        if nn<150: out.append(f"{nn:5d} (few)          "); continue
        w=won[g].sum(); ae=w/pb[g].sum(); roi=np.mean(np.where(won[g],bs[g]-1,-1)); roic=np.mean(np.where(won[g],(bs[g]-1)*0.92,-1))
        out.append(f"{nn:5d} {ae:.2f} {100*roi:+4.0f}% {100*roic:+4.0f}%")
    print(f"| {lab:38s} | {out[0]} | {out[1]} |")
print(f"runners {use.sum()}, races {full.sum()}, median BSP book {100*np.median(book[full]):.1f}%; halves split at {np.datetime64(int(cut),'D')}")
print("| group | EARLY: n  A/E  ROI  ROI-8% | LATE: n  A/E  ROI  ROI-8% |\n|---|---|---|")
seg("ALL",np.ones(n,bool))
for lo,hi in ((1,2),(2,3),(3,5),(5,8),(8,12),(12,20),(20,50),(50,1000)): seg(f"BSP ${lo}-${hi}",(bs>=lo)&(bs<hi))
seg("BSP favourite",brank==1); seg("BSP 2nd-3rd",(brank>=2)&(brank<=3)); seg("BSP 4th+",brank>=4)
seg("metro",np.isin(track,list(METRO))); seg("not metro",~np.isin(track,list(METRO)))
seg("Saturday",wd==5); seg("midweek",wd<5)
seg("field 8 or fewer",fld<=8); seg("field 12+",fld>=12)
seg("barrier 1-4",bar<=4); seg("barrier 9+",bar>=9)
seg("first up (70+ days)",days>=70); seg("racing fit",days<70)
seg("2yo/3yo",age<=3); seg("5 starts or fewer",starts<=5)
seg("jockey's only ride",only)
seg("last-start closer, top 15%",np.isfinite(late)&(late>=lq[1])); seg("last-start closer, bottom 15%",np.isfinite(late)&(late<=lq[0]))
seg("firmed 20%+ open->BSP",mv<=0.8); seg("held",(mv>0.95)&(mv<1.05)); seg("drifted 25%+",mv>=1.25)
seg("1000-1200m",(dist<=1200)); seg("1800m+",dist>=1800)
