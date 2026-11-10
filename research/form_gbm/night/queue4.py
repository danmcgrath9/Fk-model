"""Queue 4: do the three small gains from queues 1-2 hold together, at the live seed count? (night of 10 Nov 2026)
  base5          the live settings on 5 seeds (what train_all_f9.py averages)
  slow5          learning rate 0.03, 8000 rounds, 5 seeds
  slow5_margin   the same with the 12 headline "margin over the best other runner" inputs
  seeds10        the live settings on 10 seeds
Each against base5 on both folds.
    python3.13 queue4.py"""
import numpy as np
import nl, feats_night as fn
F, NM, ri, nR = nl.F, nl.NM, nl.ri, nl.nR
G2, g2n = fn.gap2(F, NM, ri, nR)
HEAD = [n for n in g2n if n.split("__")[0] in ("rating_neural", "e_rat_rw", "e_wfaRat_rw", "e_speedRating_rw", "rating_peak12m", "e_rat_last", "x_pastp_rw", "e_rat_max5", "rating_peak", "raw_neural", "e_wfaRat_last", "e_lbsp_rw")]
hi = [g2n.index(n) for n in HEAD]; slow = dict(rounds=8000, params=dict(learning_rate=0.03)); s5 = tuple(range(5))
EXP = [("base5", (F, NM), dict(seeds=s5), "live settings, 5 seeds"),
       ("slow5", (F, NM), dict(seeds=s5, **slow), "learning rate 0.03, 8000 rounds, 5 seeds"),
       ("slow5_margin", (np.hstack([F, G2[:, hi]]), NM + HEAD), dict(seeds=s5, **slow), "slow + the 12 headline margins, 5 seeds"),
       ("seeds10", (F, NM), dict(seeds=tuple(range(10))), "live settings, 10 seeds")]
for name, (FF, names), kw, note in EXP:
    for fold in ("A", "B"):
        if nl.done(name, fold): continue
        p, bst = nl.fit(FF, names, fold, **kw); nl.record(name, fold, p, note)
print("queue 4 done")
