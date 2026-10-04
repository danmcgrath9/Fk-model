"""Holdout check of the EXACT live v6 inputs (stage2.travel + stage2.collateral via last_start), same harness as t_b9_s2."""
import numpy as np, bench as b, stage2
src=open("t_research.py").read().split("# 1. Accardi")[0]
exec(src)
TV=stage2.travel(D["training_location"],D["track"][ri],ri,nR)
lid,lf=stage2.last_start(D["P"],D["past_fields"],D["past_race_ids"])
CO=stage2.collateral(D["race_id"][ri],D["date"][ri],D["horse_id"],D["finish"],D["q"],lid,D["date"][ri],D["horse_id"],lf,ri,nR)
print("collateral coverage",CO[:,4].mean().round(3))
evaluate(V4,"live v5 (blend9 + stage-2 v4)")
evaluate(np.column_stack([V4,TV,CO]),"v6 (live inputs: travel + collateral)")
