"""Apply data/live_bets/form-adjustments.json to an export npz before pricing (9 Nov 2026: the Cavill Avenue +4 lengths
had been recorded but nothing applied it). For each adjusted run: that run's own ratings in P (rating, wfa, wfaRat and
the ratings measured against class and average) go up by the points, and every X column built from them moves with
them: the last-start columns by the full points, the best/peak columns to the new best. raceRating (the race's class)
and the speed figures are left alone.
    python form_adjust_npz.py IN.npz OUT.npz [--only "Cavill Avenue"] [--points 11.9]"""
import argparse, json, os
import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("--only"); ap.add_argument("--points", type=float, help="what-if: these points instead of the recorded ones")
a = ap.parse_args()
adj = json.load(open(os.path.join(here, "../../data/live_bets/form-adjustments.json")))
z = dict(np.load(a.inp, allow_pickle=True))
names = [str(n) for n in z["name"]]; pf = [str(f) for f in z["past_fields"]]; cols = [str(c) for c in z["cols"]]
P, X = z["P"].copy(), z["X"].copy()
LAST = ["raw_last", "raw_last_dist", "raw_wfa", "raw_last_vs_lws", "last_rel", "last_dist_rel", "wfa_rel", "last_vs_lws"]
BEST_RAW = ["raw_peak", "raw_peak12", "rating_peak", "rating_peak12m", "raw_best_dist", "raw_wfa_best"]
BEST_REL = {"peak_rel": "raw_peak", "peak12_rel": "raw_peak12", "best_dist_rel": "raw_best_dist", "wfa_best_rel": "raw_wfa_best",
            "best_vs_lws": "raw_peak", "raw_best_vs_lws": "raw_peak"}
for x in adj:
    if a.only and x["horse"] != a.only:
        continue
    if x["horse"] not in names:
        print(f"{x['horse']}: not in this export"); continue
    i = names.index(x["horse"]); pts = a.points if a.points is not None else float(x["points"]); day = x["run"][:10]
    # the run: the stored row whose rating matches the recorded from_wfa (dates are not in P, only days before)
    k = next((k for k in range(P.shape[1]) if np.isfinite(P[i, k, pf.index("wfa")]) and abs(P[i, k, pf.index("wfa")] - x["from_wfa"]) < 0.1), None)
    if k is None:
        print(f"{x['horse']}: the {day} run (WFA {x['from_wfa']}) is not among its stored runs"); continue
    for f in ("rating", "wfa", "wfaRat", "vsClass", "vsAllAvg"):
        if np.isfinite(P[i, k, pf.index(f)]):
            P[i, k, pf.index(f)] += pts
    is_last = all(not np.isfinite(P[i, j, pf.index("wfa")]) for j in range(k))   # no rated run newer than it
    old = {c: float(X[i, cols.index(c)]) for c in cols}
    if is_last:
        for c in LAST:
            if c in cols and np.isfinite(X[i, cols.index(c)]):
                X[i, cols.index(c)] += pts
    new_best = float(P[i, k, pf.index("wfa")])
    for c in BEST_RAW:
        if c in cols and np.isfinite(X[i, cols.index(c)]) and new_best > X[i, cols.index(c)]:
            X[i, cols.index(c)] = new_best
    for c, base in BEST_REL.items():
        if c in cols and base in cols and np.isfinite(X[i, cols.index(c)]):
            X[i, cols.index(c)] += X[i, cols.index(base)] - old[base]
    moved = {c: (round(old[c], 2), round(float(X[i, cols.index(c)]), 2)) for c in cols if np.isfinite(old[c]) and abs(old[c] - X[i, cols.index(c)]) > 1e-6}
    print(f"{x['horse']}: run {day} +{pts} points (last start: {is_last}); X moved: {moved}")
z["P"], z["X"] = P, X
np.savez(a.out, **z)
