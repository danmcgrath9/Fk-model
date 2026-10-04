"""Collateral form (Benter 'key race', pros' form lines): how the rivals from this horse's last start went NEXT time,
using only races run before today. Tested as stage-2 inputs on the holdout."""
import numpy as np, bench as b, stage2
src=open("t_research.py").read().split("# 1. Accardi")[0]
exec(src)
rid=D["race_id"].astype(str); rdate=D["date"].astype(str); hid=D["horse_id"].astype(str)
pr=D["past_race_ids"].astype(str); fin_all=D["finish"].astype(float); q_all=D["q"]
# index: race id -> runner rows; horse -> rows sorted by date
race_rows={}; 
for k,r in enumerate(rid[ri]): race_rows.setdefault(r,[]).append(k)
horse_rows={}
for k in range(n): horse_rows.setdefault(hid[k],[]).append(k)
for h in horse_rows: horse_rows[h].sort(key=lambda k: rdate[ri[k]])
race_date={r:rdate[ri[rows[0]]] for r,rows in race_rows.items()}
def next_run(h,after_date,before_date):
    """the horse's first run strictly after after_date and before before_date (today), or None"""
    for k in horse_rows.get(h,[]):
        d=rdate[ri[k]]
        if d>after_date and d<before_date: return k
    return None
# for each runner today: last-start race id (first non-empty past id); rivals = other runners of that race in our data
last=np.array([next((x for x in row if x),"") for row in pr])
n_riv=np.full(n,np.nan); n_next=np.full(n,np.nan); nxt_win=np.full(n,np.nan); nxt_q=np.full(n,np.nan); nxt_beat=np.full(n,np.nan); nxt_bq=np.full(n,np.nan)
for k in range(n):
    r=last[k]; today=rdate[ri[k]]
    if r not in race_rows: continue
    rows=[x for x in race_rows[r] if hid[x]!=hid[k]]
    if not rows: continue
    rd=race_date[r]; n_riv[k]=len(rows)
    my_fin=next((fin_all[x] for x in race_rows[r] if hid[x]==hid[k]),np.nan)
    wins=[];qs=[];bw=[];bqs=[]
    for x in rows:
        nk=next_run(hid[x],rd,today)
        if nk is None: continue
        w=float(fin_all[nk]==1); wins.append(w); qs.append(q_all[nk])
        if np.isfinite(my_fin) and np.isfinite(fin_all[x]) and fin_all[x]>my_fin: bw.append(w); bqs.append(q_all[nk])   # rivals this horse BEAT
    if wins:
        n_next[k]=len(wins); nxt_win[k]=np.mean(wins); nxt_q[k]=np.mean(qs)
        # wins above what the market expected of them = the race was stronger than it looked
        nxt_beat[k]=np.sum(wins)-np.sum(qs)
    if bw: nxt_bq[k]=np.mean(bw)-np.mean(bqs)
print("coverage: last start in data",np.isfinite(n_riv).mean().round(3)," with rivals' next runs",np.isfinite(n_next).mean().round(3))
G=np.column_stack([np.nan_to_num(n_next,nan=0),np.nan_to_num(nxt_win,nan=0),np.nan_to_num(nxt_beat,nan=0),np.nan_to_num(nxt_bq,nan=0),np.isfinite(n_next).astype(float),rrel(np.nan_to_num(nxt_beat,nan=0))])
np.save("G_collateral.npy",G)
evaluate(V4,"live (blend9 + stage-2 v4)")
evaluate(np.column_stack([V4,G]),"live + collateral form (rivals' next runs)")
