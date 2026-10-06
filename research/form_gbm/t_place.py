"""Place betting on the live bets (6 Oct 2026). Form King gives no place prices, so the place price is ESTIMATED:
Harville place chance from the opening win market, priced with a place-book margin (1.18 per place share, with
1.12 and 1.25 as sensitivity). Places paid: 8+ starters 3, 5-7 starters 2, under 5 none (win only).
Our place chance is Harville on our win chance. Checks: (1) is Harville calibrated for places, and does the
speed map (settle position) or the ratings move the real place rate beyond what the chance says;
(2) win vs place vs each-way vs price-split staking on the live bets, at the open, $100 a unit."""
import numpy as np
exec(open("t_backtest_full.py").read().split("rd=dates")[0])
fin=D["finish"].astype(float); starters=np.bincount(ri,minlength=nR)[ri]
places=np.where(starters>=8,3,np.where(starters>=5,2,0))
def harville(w,k):
    m=len(w); out=w.copy()
    if k>=2:
        p2=np.zeros(m)
        for j in range(m):
            if 1-w[j]<=1e-9: continue
            p2+=np.where(np.arange(m)!=j,w[j]*w/(1-w[j]),0)
        out=out+p2
    if k>=3:
        p3=np.zeros(m)
        for j in range(m):
            for l in range(m):
                if l==j: continue
                d1=1-w[j]; d2=1-w[j]-w[l]
                if d1<=1e-9 or d2<=1e-9: continue
                msk=(np.arange(m)!=j)&(np.arange(m)!=l)
                p3+=np.where(msk,w[j]*w[l]/d1*w/d2,0)
        out=out+p3
    return np.clip(out,0,1)
okm=np.isfinite(op)&(op>1)
qm=np.where(okm,1/np.where(okm,op,2),0.0)
pl_us=np.full(n,np.nan); pl_mk=np.full(n,np.nan)
for r in np.unique(ri[hm]):
    ix=np.where(ri==r)[0]; k=places[ix[0]]
    if k==0 or not np.isfinite(p[ix]).all(): continue
    w=p[ix]/p[ix].sum(); pl_us[ix]=harville(w,k)
    if okm[ix].all():
        wm=qm[ix]/qm[ix].sum(); pl_mk[ix]=harville(wm,k)
placed=(fin>=1)&(fin<=places)&(places>0)
ok=hm&np.isfinite(pl_us)&np.isfinite(pl_mk)&(fin>0)
print(f"races with places and a full market: {len(np.unique(ri[ok]))}, runners {ok.sum()}")

def calib(lab,m):
    a=placed[m].sum(); eu=pl_us[m].sum(); em=pl_mk[m].sum()
    print(f"  {lab:34s} runners {m.sum():6d}  placed {a:6.0f}  ours expects {eu:7.1f} ({a/eu*100:5.1f}%)  market expects {em:7.1f} ({a/em*100:5.1f}%)")
print("\n(1) Does Harville get places right? actual placings against what each expects (100% = right)")
calib("all runners",ok)
for lo,hi,lab in ((0,.25,"favourite-ish (our win 25%+)"),(.1,.25,"our win 10-25%"),(.04,.1,"our win 4-10%"),(0,.04,"our win under 4%")):
    if lab.startswith("fav"): calib(lab,ok&(p>=.25))
    else: calib(lab,ok&(p>=lo)&(p<hi))
print("  by usual settle position (speed map habit):")
for lo,hi,lab in ((0,.3,"leads / on pace"),(.3,.65,"midfield"),(.65,1.01,"back")):
    calib(lab,ok&(ss>=lo)&(ss<hi))
calib("no settle data",ok&~np.isfinite(ss))
# ratings: last-start rating rank in the race
lr=ld(rat)
rk=np.full(n,np.nan)
for r in np.unique(ri[ok]):
    ix=np.where(ri==r)[0]; v_=np.where(np.isfinite(lr[ix]),lr[ix],-1e9); o=np.argsort(-v_); rr=np.empty(len(ix)); rr[o]=np.arange(1,len(ix)+1); rk[ix]=np.where(np.isfinite(lr[ix]),rr,np.nan)
print("  by last-start rating rank in the race:")
for lo,hi,lab in ((1,1,"top rated"),(2,3,"2nd-3rd rated"),(4,99,"4th or lower")):
    calib(lab,ok&(rk>=lo)&(rk<=hi))
print("  forward AND top-3 rated vs back AND top-3 rated:")
calib("forward + top-3 rated",ok&(ss<.3)&(rk<=3)); calib("back + top-3 rated",ok&(ss>=.65)&(rk<=3))

print("\n(1b) Wins: actual winners against what our win chance expects, by settle position and rating rank")
for lo,hi,lab in ((0,.3,"leads / on pace"),(.3,.65,"midfield"),(.65,1.01,"back")):
    m=ok&(ss>=lo)&(ss<hi); print(f"  {lab:20s} won {won[m].sum():5d}  ours expects {p[m].sum():7.1f} ({won[m].sum()/p[m].sum()*100:5.1f}%)  market {qm[m].sum()/1:7.1f}")
for lo,hi,lab in ((1,1,"top rated"),(2,3,"2nd-3rd rated"),(4,99,"4th or lower")):
    m=ok&(rk>=lo)&(rk<=hi); print(f"  {lab:20s} won {won[m].sum():5d}  ours expects {p[m].sum():7.1f} ({won[m].sum()/p[m].sum()*100:5.1f}%)")
print("\n(2) The live bets, same stakes, settled at the open ($100 a unit)")
L=live&ok
po_w=np.where(won,op-1,-1.0)
for M in (1.12,1.18,1.25):
    pp_=np.maximum(1.04,1/np.maximum(pl_mk*M,1e-9)); po_p=np.where(placed,pp_-1,-1.0)
    def rep(lab,ws,ps):
        inv=100*(ws+ps)[L].sum(); pr=100*(ws*po_w+ps*po_p)[L].sum()
        idx=np.where(L)[0]; o=idx[np.argsort(D["date"][ri[idx]].astype(str),kind="stable")]
        cum=np.cumsum(100*(ws*po_w+ps*po_p)[o]); dd=(np.maximum.accumulate(np.concatenate([[0],cum]))[1:]-cum).max()
        ret_any=((ws>0)&won)|((ps>0)&placed); run=best=0
        for k in o:
            run=0 if ret_any[k] else run+1; best=max(best,run)
        print(f"  margin {M:.2f}  {lab:44s} invested ${inv:>9,.0f}  profit ${pr:>+9,.0f}  ROI {pr/inv*100:+6.1f}%  worst drawdown ${dd:>7,.0f}  profit/drawdown {pr/dd:4.1f}  longest run with no return {best}")
    s=stake
    rep("WIN only (the plan)",s,0*s); rep("PLACE only",0*s,s); rep("EACH-WAY (half win, half place)",s/2,s/2)
    for X_ in (6,8,10):
        rep(f"win under ${X_}, each-way ${X_}+",np.where(op<X_,s,s/2),np.where(op<X_,0,s/2))
    rep("win + place on forward runners, win else",np.where(ss<.3,s/2,s),np.where(ss<.3,s/2,0))
    if M==1.18:
        print(f"     place strike on the live bets {placed[L].mean()*100:.1f}% (win strike {won[L].mean()*100:.1f}%), avg est place price ${pp_[L].mean():.2f}")
        pv=pl_us*pp_-1
        for th in (0.1,0.2):
            m=hm&ok&(pv>=th)&caps&(1/p>=2)&(1/p<=15)&~blockset
            inv=100*m.sum(); pr=100*po_p[m].sum()
            print(f"     PLACE-VALUE bets (our place chance x est place price {int(th*100)}c+), flat $100: bets {m.sum()}, ROI {pr/inv*100:+.1f}%, strike {placed[m].mean()*100:.1f}%")
        for lo,hi,lab in ((0,.3,"forward"),(.3,.65,"midfield"),(.65,1.01,"back")):
            m=L&(ss>=lo)&(ss<hi)
            print(f"     live bets that settle {lab:8s}: {m.sum():4d}  win ROI {(100*(s*po_w)[m].sum())/(100*s[m].sum())*100:+6.1f}%  place ROI {(100*(s*po_p)[m].sum())/(100*s[m].sum())*100:+6.1f}%  place strike {placed[m].mean()*100:4.1f}%")

print("\n(3) REAL place prices: Betfair place dividend (place SP) from Form King's results, against win at BSP, both less 8% commission")
import csv
dv={}
for r in csv.DictReader(l for l in open("place_divs.csv") if not l.startswith("#")):
    try: dv[(r["race_id"],r["horse_id"])]=float(r["betfairPlaceDiv"] or 0)
    except ValueError: pass
rid_=D["race_id"][ri].astype(str); hid_=D["horse_id"].astype(str)
bpd=np.array([dv.get((rid_[k],hid_[k]),np.nan) for k in range(n)])
has_pl=np.isfinite(bpd)
# a placegetter whose dividend is missing cannot be settled: leave those races out
miss_race=np.bincount(ri,weights=(placed&~(bpd>1)).astype(float),minlength=nR)>0
L3=live&ok&has_pl&~miss_race[ri]&np.isfinite(bsp)&(bsp>1)
pw=np.where(won,(bsp-1)*0.92,-1.0); pp3=np.where(placed&(bpd>1),(bpd-1)*0.92,-1.0)
print(f"  live bets with a real place price: {L3.sum()} of {live.sum()}; place strike {placed[L3].mean()*100:.1f}%, avg place SP of placegetters ${bpd[L3&placed].mean():.2f}")
def rep3(lab,ws,ps,m=L3):
    inv=100*(ws+ps)[m].sum(); pr=100*(ws*pw+ps*pp3)[m].sum()
    idx=np.where(m)[0]; o=idx[np.argsort(D["date"][ri[idx]].astype(str),kind="stable")]
    cum=np.cumsum(100*(ws*pw+ps*pp3)[o]); dd=(np.maximum.accumulate(np.concatenate([[0],cum]))[1:]-cum).max()
    print(f"  {lab:46s} invested ${inv:>9,.0f}  profit ${pr:>+8,.0f}  ROI {pr/inv*100:+6.1f}%  worst drawdown ${dd:>6,.0f}")
s=stake
rep3("WIN only at BSP (the plan)",s,0*s); rep3("PLACE only at place SP",0*s,s); rep3("EACH-WAY",s/2,s/2)
for X_ in (6,8,10): rep3(f"win under ${X_} (open), each-way ${X_}+",np.where(op<X_,s,s/2),np.where(op<X_,0,s/2))
for lo,hi,lab in ((0,.3,"forward"),(.3,.65,"midfield"),(.65,1.01,"back")):
    m=L3&(ss>=lo)&(ss<hi)
    print(f"  settle {lab:8s} {m.sum():4d} bets  win ROI {(s*pw)[m].sum()/s[m].sum()*100:+6.1f}%  place ROI {(s*pp3)[m].sum()/s[m].sum()*100:+6.1f}%  place strike {placed[m].mean()*100:4.1f}%")
for lo,hi in ((2,6),(6,10),(10,20),(20,99)):
    m=L3&(op>=lo)&(op<hi)
    print(f"  open ${lo}-${hi:<3d} {m.sum():4d} bets  win ROI {(s*pw)[m].sum()/s[m].sum()*100:+6.1f}%  place ROI {(s*pp3)[m].sum()/s[m].sum()*100:+6.1f}%")
# how good was the estimate? estimated place price from BSP-market Harville x 1.18 vs real place SP
okb=hm&np.isfinite(bsp)&(bsp>1)
pl_b=np.full(n,np.nan)
for r in np.unique(ri[L3]):
    ix=np.where(ri==r)[0]; k=places[ix[0]]
    if okb[ix].all() and k: w=(1/bsp[ix])/(1/bsp[ix]).sum(); pl_b[ix]=harville(w,k)
m=L3&placed&(bpd>1)&np.isfinite(pl_b)
print(f"  real place SP vs fair Harville place price off BSP, placegetters: median ratio {np.median(bpd[m]*pl_b[m]):.2f} (1.00 = Betfair place SP is fair)")
