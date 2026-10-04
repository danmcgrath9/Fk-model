"""Ridden-back inputs in stage 2: first-up, drawn wide, short of trip -> expected settling position (holdout KL to BSP)."""
import numpy as np, bench as b, stage2
src=open("t_research.py").read().split("# 1. Accardi")[0]
exec(src)
c=D["colidx"]; X=D["X"].astype(float); bsh=X[:,c["raw_barrier_share"]]; ssh=X[:,c["raw_settle_share"]]
jr=np.argmax(race,1); okr=race[ar,jr]
gap=np.where(okr,P[ar,jr,f["days_before"]],np.nan); ldist=np.where(okr,P[ar,jr,f["distance"]],np.nan)
today=D["distance"][ri].astype(float); drop=ldist-today
fu=(gap>=60).astype(float); wide=(bsh>=0.5).astype(float); short=(drop>=200).astype(float)
# expected shift in settling share, measured over past runs of usual midfield settlers (t_goback.py)
shift=fu*np.where(wide==1,np.where(short==1,0.212,0.087),0.020)+(1-fu)*np.where((wide==1)&(short==1),0.13,-0.02)
pred=ssh+shift
G=np.column_stack([fu,np.nan_to_num(drop,nan=0),fu*bsh,fu*np.nan_to_num(drop,nan=0),fu*wide*short,shift,pred,rrel(pred)])
evaluate(V4,"live (blend9 + stage-2 v4)")
evaluate(np.column_stack([V4,G]),"live + ridden-back inputs")
