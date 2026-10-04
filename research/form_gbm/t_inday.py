"""Kingsley Bartholomew's in-day track bias: what the EARLIER races at the same meeting said (where the winners and
placegetters settled, how the inside/outside barriers went), interacted with this runner's own style and draw.
Only races run earlier the same day are used, so it is knowable before the jump."""
import numpy as np, bench as b, stage2
src=open("t_research.py").read().split("# 1. Accardi")[0]
exec(src)
c=D["colidx"]; X=D["X"].astype(float); ssh=X[:,c["raw_settle_share"]]; bsh=X[:,c["raw_barrier_share"]]
fin=D["finish"].astype(float); rno=D["race_number"] if "race_number" in D else None
rid=D["race_id"].astype(str)
rn=np.array([int(x.rsplit("_",1)[-1]) if x.rsplit("_",1)[-1].isdigit() else 0 for x in rid])          # race number from the id
meet=np.array([x.rsplit("_",1)[0] for x in rid])
# per race: settle share of the winner and mean of the first three; barrier share of the winner
won=fin==1; top3=np.isfinite(fin)&(fin<=3)
w_settle=np.full(nR,np.nan); t3_settle=np.full(nR,np.nan); w_bar=np.full(nR,np.nan); t3_bar=np.full(nR,np.nan)
for r in range(nR):
    m=(ri==r)
    if (m&won).any():
        w_settle[r]=np.nanmean(ssh[m&won]); w_bar[r]=np.nanmean(bsh[m&won])
    if (m&top3).sum()>=2: t3_settle[r]=np.nanmean(ssh[m&top3]); t3_bar[r]=np.nanmean(bsh[m&top3])
# for each race: averages over EARLIER races at the same meeting (race number lower)
lead_bias=np.full(nR,np.nan); bar_bias=np.full(nR,np.nan); n_prior=np.zeros(nR)
by_meet={}
for r in range(nR): by_meet.setdefault(meet[r],[]).append(r)
for mt,rs in by_meet.items():
    for r in rs:
        prior=[x for x in rs if rn[x]<rn[r] and np.isfinite(t3_settle[x])]
        if len(prior)>=2:
            lead_bias[r]=np.nanmean(t3_settle[prior]); bar_bias[r]=np.nanmean(t3_bar[prior]); n_prior[r]=len(prior)
print("races with 2+ earlier races today:",np.isfinite(lead_bias).mean().round(3))
# bias relative to normal (0.5 = no pattern); horse fit = how its style/draw matches the day's pattern
lb=lead_bias[ri]-0.5; bb=bar_bias[ri]-0.5
fit_style=-(lb)*(np.nan_to_num(ssh,nan=0.5)-0.5)      # leaders winning (lb<0) and this horse leads (ssh small) -> positive
fit_draw=-(bb)*(np.nan_to_num(bsh,nan=0.5)-0.5)
G=np.column_stack([np.nan_to_num(lb,nan=0),np.nan_to_num(bb,nan=0),np.nan_to_num(fit_style,nan=0),np.nan_to_num(fit_draw,nan=0),n_prior[ri],rrel(np.nan_to_num(fit_style,nan=0)),rrel(np.nan_to_num(fit_draw,nan=0))])
np.save("G_inday.npy",G)
evaluate(V4,"live (blend9 + stage-2 v4)")
evaluate(np.column_stack([V4,G]),"live + in-day bias (earlier races today)")
