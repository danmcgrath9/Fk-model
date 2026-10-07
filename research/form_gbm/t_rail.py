"""Rail position and the speed map (7 Oct 2026, founder: 'rail out 9m at Caulfield I'd want to be on speed').
Do leaders / on-pace runners win more than the market (BSP) and our model expect when the rail is out?
Races with a rail from rails.csv (DB pulls; the history files carry none). Position = Form King's predicted
settling position (speed map, known before the race). Our chance = stage-1 out-of-fold (all races) and the
stage-2 holdout chance where available."""
import numpy as np, csv, re
exec(open("t_pros.py").read().split("def gr(")[0])
rail={}
for r in csv.DictReader(l for l in open("rails.csv") if not l.startswith("#")):
    t=r["rail"].lower(); m=re.search(r"(\d+(?:\.\d+)?)\s*m",t)
    rail[r["race_id"]]=0.0 if "true" in t and not m else (float(m.group(1)) if m else np.nan)
rid=D["race_id"].astype(str)   # race-level array
rm=np.array([rail.get(x,np.nan) for x in rid])[ri]
trk=D["track"].astype(str)[ri]
pos=X[:,c["sm_predicted_position"]]; fld=np.bincount(ri,minlength=nR)[ri].astype(float)
psh=(pos-1)/np.maximum(fld-1,1)
pb=np.where(~np.isfinite(pos),"?",np.where(pos==1,"lead",np.where(psh<0.34,"on pace",np.where(psh<0.67,"midfield","back"))))
po=np.load("p_oof_blend9.npy"); okb=np.isfinite(bsp)&(bsp>1)&np.isfinite(q)&(D["finish"]>0)
band=np.where(~np.isfinite(rm),"",np.where(rm==0,"true",np.where(rm<=4,"out 1-4m",np.where(rm<=8,"out 5-8m","out 9m+"))))
rr=np.unique(ri[band!=""]); ds=sorted(dates[rr]); print("runners with a rail:", (band!="").sum(), "in", len(rr), "races; dates", ds[0], "to", ds[-1])
def tab(lab,m):
    print(f"\n{lab}")
    print(f"  {'rail':10s} {'position':9s} {'runners':>7s} {'wins':>5s}  vs market (BSP)  vs our model (OOF)")
    for b_ in ("true","out 1-4m","out 5-8m","out 9m+"):
        for p_ in ("lead","on pace","midfield","back"):
            mm=m&(band==b_)&(pb==p_)&okb&np.isfinite(po)
            if mm.sum()<30: continue
            w=won[mm].sum(); print(f"  {b_:10s} {p_:9s} {mm.sum():7d} {w:5d}  {w/q[mm].sum()*100:6.0f}%          {w/po[mm].sum()*100:6.0f}%")
tab("ALL VIC TRACKS (100% = wins exactly as expected; above 100 = won more than priced)",np.ones(n,bool))
tab("CAULFIELD",np.char.startswith(trk,"Caulfield"))
tab("METRO (Caulfield, Flemington, Moonee Valley, Sandown)",np.isin(np.char.split(trk).astype(object).tolist() if False else trk,["Caulfield","Flemington","Moonee Valley","Sandown","Sandown Hillside","Sandown Lakeside","Caulfield Heath"]))
# leaders+on pace combined by rail band, with a simple significance check
print("\nLEADERS + ON PACE combined, all tracks:")
for b_ in ("true","out 1-4m","out 5-8m","out 9m+"):
    mm=(band==b_)&np.isin(pb,["lead","on pace"])&okb&np.isfinite(po)
    w=won[mm].sum(); e=q[mm].sum(); sd=np.sqrt((q[mm]*(1-q[mm])).sum())
    print(f"  {b_:10s} runners {mm.sum():5d} wins {w:4d}  market expected {e:6.1f} ({w/e*100:4.0f}%, z {(w-e)/sd:+.1f})  our model expected {po[mm].sum():6.1f} ({w/po[mm].sum()*100:4.0f}%)")
