"""Prep-pattern inputs (1 Nov 2026, founder: St Gotthard and The Next Episode "clearly being peaked for yesterday, their
first-up runs from previous prep were better, indicating they have come back better, whereas Natural Fling clearly reached
peak and maintaining"). From the past-run array P (index 0 most recent; prep = run number in its preparation, 1 = first-up,
0 = trial), on WFA ratings, race runs only:
  fu_gain        this prep's first-up rating minus the previous prep's first-up rating (today second-up or later)
  prep_vs_prev   best rating so far this prep minus the previous prep's best (today second-up or later)
  prep_trend     last run's rating minus this prep's first-up rating (today second-up or later)
  off_prep_best  last run's rating minus this prep's best (0 = last run was the peak)
  runs_since_best runs since this prep's best
  prev_prep_rise for a first-upper: the previous prep's best minus its first-up (it progressed through last prep)
  prev_fu_gain   for a first-upper: previous prep's first-up minus the one before (came back better last time)"""
import numpy as np
def build(P, pf, run_in_prep):
    rt = P[:, :, pf.index("wfaRat")].astype(float); pr = P[:, :, pf.index("prep")].astype(float); tr = P[:, :, pf.index("trial")] == 1
    n = len(P); out = {k: np.full(n, np.nan) for k in ("fu_gain", "prep_vs_prev", "prep_trend", "off_prep_best", "runs_since_best", "prev_prep_rise", "prev_fu_gain")}
    for i in range(n):
        runs = [(pr[i, k], rt[i, k]) for k in range(P.shape[1]) if not tr[i, k] and np.isfinite(pr[i, k]) and pr[i, k] >= 1 and np.isfinite(rt[i, k])]
        if not runs: continue
        preps, cur = [], []
        for p_, r_ in runs:              # newest first: a prep ends (going back) at its first-up run
            cur.append(r_)
            if p_ == 1: preps.append(cur[::-1]); cur = []
        if cur: preps.append(cur[::-1])   # oldest prep cut off by the array: incomplete, first-up unknown
        complete = [len(preps) > j and (j < len(preps) - 1 or not cur) for j in range(len(preps))]
        rip = run_in_prep[i]
        if np.isfinite(rip) and rip >= 2 and preps:       # today continues prep 0
            p0 = preps[0]
            out["prep_trend"][i] = p0[-1] - p0[0] if complete[0] else np.nan
            out["off_prep_best"][i] = p0[-1] - max(p0); out["runs_since_best"][i] = len(p0) - 1 - int(np.argmax(p0))
            if len(preps) > 1 and complete[0] and complete[1]:
                out["fu_gain"][i] = p0[0] - preps[1][0]; out["prep_vs_prev"][i] = max(p0) - max(preps[1])
        elif preps:                                       # first-up today: prep 0 is last prep
            if complete[0]: out["prev_prep_rise"][i] = max(preps[0]) - preps[0][0]
            if len(preps) > 1 and complete[0] and complete[1]: out["prev_fu_gain"][i] = preps[0][0] - preps[1][0]
    return out
