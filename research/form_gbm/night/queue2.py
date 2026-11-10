"""Queue 2: new input families (feats_night.py) and the learning curve.
    python3.13 queue2.py [names...]"""
import sys, numpy as np
import nl, feats_night as fn

F, NM, ri, nR = nl.F, nl.NM, nl.ri, nl.nR
G2, g2n = fn.gap2(F, NM, ri, nR); G2Z, g2zn = fn.gap2(F, NM, ri, nR, with_z=True); CC, ccn = fn.close_counts(F, NM, ri, nR); AP, apn = fn.aptitude(nl.D)
print(f"gap2 {G2.shape[1]} inputs, gap2+z {G2Z.shape[1]}, close {CC.shape[1]}, aptitude {AP.shape[1]}", flush=True)
for k, n in enumerate(apn): print(f"  {n:18s} finite {np.isfinite(AP[:, k]).mean():.2f} mean {np.nanmean(AP[:, k]):+.3f} sd {np.nanstd(AP[:, k]):.3f}")
HEAD = [n for n in g2n if n.split("__")[0] in ("rating_neural", "e_rat_rw", "e_wfaRat_rw", "e_speedRating_rw", "rating_peak12m", "e_rat_last", "x_pastp_rw", "e_rat_max5", "rating_peak", "raw_neural", "e_wfaRat_last", "e_lbsp_rw")]
hi = [g2n.index(n) for n in HEAD]
EXP = [("gap2", (np.hstack([F, G2]), NM + g2n), {}, f"+ margin over the best other runner, {len(g2n)} inputs"),
       ("gap2_head", (np.hstack([F, G2[:, hi]]), NM + HEAD), {}, f"+ the margin for the {len(HEAD)} headline ratings only"),
       ("gap2_z", (np.hstack([F, G2Z]), NM + g2zn), {}, "+ margin and race z-score"),
       ("gap2_close", (np.hstack([F, G2, CC]), NM + g2n + ccn), {}, "+ margin and rivals-close counts"),
       ("apt", (np.hstack([F, AP]), NM + apn), {}, "+ sire / dam sire on today's going and distance band, jockey at the track, trainer in the band"),
       ("gap2_apt", (np.hstack([F, G2, AP]), NM + g2n + apn), {}, "+ both")]
only = set(sys.argv[1:])
for name, (FF, names), kw, note in EXP:
    if only and name not in only: continue
    for fold in ("A", "B"):
        if nl.done(name, fold): continue
        p, bst = nl.fit(FF, names, fold, **kw)
        imp = bst.feature_importance("gain"); new = imp[len(NM):].sum() / imp.sum()
        top = sorted(zip(imp[len(NM):], names[len(NM):]), reverse=True)[:6]
        nl.record(name, fold, p, note, dict(inputs=FF.shape[1], new_gain_share=float(new), top_new=[(n, float(g / imp.sum())) for g, n in top]))
# the learning curve, fold A: the same holdout, less history
for name, start in (("lc_from_oct25", "2025-10-01"), ("lc_from_jan26", "2026-01-01"), ("lc_from_mar26", "2026-03-01")):
    if (only and name not in only) or nl.done(name, "A"): continue
    races = np.arange(nR)[(nl.rdate < "2026-06-03") & (nl.rdate >= start)]; preds = []
    for s in (0, 1, 2):
        bst = nl.train(F, NM, races, nl.q, seed=s); preds.append(np.log(nl.b.softmax_races(bst.predict(F))))
    nl.record(name, "A", nl.b.softmax_races(np.mean(preds, 0)), f"trained only on races from {start} to 2 Jun 2026", dict(train_races=int(len(races))))
print("queue 2 done")
