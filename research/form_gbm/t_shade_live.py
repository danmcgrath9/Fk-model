"""The back-settler shade on the v10 holdout with the full 1 Nov rules (t_live_rules.py), with and without it."""
import numpy as np
exec(open("t_live_rules.py").read().split("idx = np.array")[0])
cols = list(z["cols"]); ss = z["X"][:, cols.index("raw_settle_share")].astype(float); dist = z["distance"].astype(float)[ri]
def shaded(sel):
    q = np.where(m & sel & (ss >= 0.65), pm0 * 0.85, pm0); s_ = np.bincount(ri, weights=np.where(m, q, 0), minlength=nR); return np.where(m, q / np.where(s_[ri] > 0, s_[ri], 1), np.nan)
def go(pp):
    global pm0
    keep = pm0; pm0 = pp
    b = [(i, s) for i, s in run(pp, ~metro) if not fs[i]] + [(i, s) for i, s in run2(metro, False) if o[i] < 12 and not fs[i]]
    pm0 = keep
    idx = np.array([i for i, _ in b]); st = np.array([s for _, s in b]); pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st); h1 = dd[idx] < "2026-08-01"
    return f"{len(idx):5d} bets {st.sum():6.0f}u {pl.sum():+6.0f}u ({100*pl.sum()/st.sum():+5.1f}%)  halves {100*pl[h1].sum()/st[h1].sum():+4.0f}% / {100*pl[~h1].sum()/st[~h1].sum():+4.0f}%"
print("no shade (the backtest as reported)", go(pm0))
print("shade every back-settler (live)     ", go(shaded(np.ones(len(m), bool))))
print("shade only beyond 1200m             ", go(shaded(dist > 1200)))
