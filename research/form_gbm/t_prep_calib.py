import numpy as np, prep_feats
pm_cur = None
exec(open("t_metro_fix.py").read().split("H1 = ")[0])
cols = list(z["cols"]); rip = z["X"][:, cols.index("raw_run_in_prep")].astype(float)
F = prep_feats.build(z["P"], list(z["past_fields"]), rip)
for k, v in F.items(): print(f"{k:16s} set for {np.isfinite(v).mean():5.1%}  median {np.nanmedian(v):+.1f}")
def row(lab, g):
    g = g & m; w = won[g].sum(); e = pm0[g].sum(); sd = np.sqrt((pm0[g] * (1 - pm0[g])).sum())
    if g.sum() >= 50: print(f"  {lab:46s} n={g.sum():5d} won {w:4d} model {e:6.1f} ({w/e:4.2f}, z {(w-e)/sd:+.1f})")
print("\nHOLDOUT: wins v the model by prep pattern")
fg = F["fu_gain"]; row("came back better (first-up +3 on last prep's)", fg >= 3); row("came back about the same", np.abs(fg) < 3); row("came back worse (-3 or more)", fg <= -3)
pv = F["prep_vs_prev"]; row("this prep's best +3 on last prep's", pv >= 3); row("this prep's best 3+ below last prep's", pv <= -3)
pt = F["prep_trend"]; row("improving through this prep (+3 on first-up)", pt >= 3); row("going backwards this prep (-3)", pt <= -3)
rs = F["runs_since_best"]; row("last run was this prep's best", rs == 0); row("2+ runs since this prep's best (plateau)", rs >= 2)
pr = F["prev_prep_rise"]; row("first-up, progressed 5+ through last prep", pr >= 5); row("first-up, flat last prep (<2)", pr < 2)
