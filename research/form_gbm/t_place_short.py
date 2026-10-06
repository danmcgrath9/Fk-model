"""Win bet plus a bigger place bet on the shorter live bets (open under $8), at REAL place prices (Betfair place
SP from Form King's results, less 8% commission). Win settled at the open (the price we take) and at BSP. Also split
by where the horse actually started (BSP $6 or shorter vs longer), as a diagnostic only: BSP is not known when betting.
6 Oct 2026."""
import numpy as np, csv
exec(open("t_backtest_full.py").read().split("rd=dates")[0])
fin=D["finish"].astype(float); starters=np.bincount(ri,minlength=nR)[ri]
places=np.where(starters>=8,3,np.where(starters>=5,2,0)); placed=(fin>=1)&(fin<=places)&(places>0)
dv={}
for r in csv.DictReader(l for l in open("place_divs.csv") if not l.startswith("#")):
    try: dv[(r["race_id"],r["horse_id"])]=float(r["betfairPlaceDiv"] or 0)
    except ValueError: pass
rid_=D["race_id"][ri].astype(str); hid_=D["horse_id"].astype(str)
bpd=np.array([dv.get((rid_[k],hid_[k]),np.nan) for k in range(n)])
miss=np.bincount(ri,weights=(placed&~(bpd>1)).astype(float),minlength=nR)>0
base=live&np.isfinite(bpd)&~miss[ri]&(places>0)&np.isfinite(bsp)&(bsp>1)
pw_o=np.where(won,op-1,-1.0); pw_b=np.where(won,(bsp-1)*0.92,-1.0); pp=np.where(placed&(bpd>1),(bpd-1)*0.92,-1.0)
s=stake
def rep(lab,m,k):
    w=100*s[m]; pl=100*k*s[m]
    for nm,pw in (("win at open",pw_o[m]),("win at BSP",pw_b[m])):
        inv=(w+pl).sum(); pr=(w*pw+pl*pp[m]).sum()
        print(f"  {lab:30s} place x{k:<3}  {nm:11s} bets {m.sum():4d}  invested ${inv:>8,.0f}  profit ${pr:>+8,.0f}  ROI {pr/inv*100:+6.1f}%   (place part alone {(pl*pp[m]).sum()/max(pl.sum(),1)*100:+6.1f}%)")
for lab,m in (("open under $8",base&(op<8)),("open under $8, BSP <= $6",base&(op<8)&(bsp<=6)),("open under $8, BSP > $6",base&(op<8)&(bsp>6)),("open $8+",base&(op>=8))):
    print(f"\n{lab}: place strike {placed[m].mean()*100:.1f}%, win strike {won[m].mean()*100:.1f}%, avg place SP when placed ${bpd[m&placed].mean():.2f}")
    for k in (0,1,1.5,2,3): rep(lab,m,k)
