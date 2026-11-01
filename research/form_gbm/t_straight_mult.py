"""Flemington straight, forward runners: a chance multiplier instead of a ban (1 Nov 2026, founder: "only drop them if it
makes sense... a leader can win, but it has to make sense from an ROI point of view"). Out of fold, full history. Forward =
usual settle share under 0.3. Multiply forward runners' chance on the straight by k, renormalise, apply the open rule; the
straight's bets and ROI at the open less 7% for each k."""
import numpy as np, stake_rule
exec(open("t_straight_oof.py").read().split("def row(")[0])
ss = z["X"][:, cols.index("raw_settle_share")].astype(float); fwd = straight & (ss < 0.3)
def go(k):
    q = np.where(m & fwd, pm * k, pm); s_ = np.bincount(ri, weights=np.where(m, q, 0), minlength=nR); pp = np.where(m, q / np.where(s_[ri] > 0, s_[ri], 1), np.nan)
    out = []
    for i in np.where(m & straight)[0]:
        qq = 1 / pp[i]
        if not (1.6 <= qq <= 15 and np.isfinite(o[i]) and o[i] < 3 * qq and o[i] < 12): continue
        E = 1.15 if qq < 4 else 1.2; mo = 0.95 * (E / pp[i] ** 0.82) ** (1 / 0.78)
        if o[i] >= mo: out.append((i, stake_rule.stake(pp[i] ** 0.82 * o[i] ** -0.22, o[i])))
    idx = np.array([i for i, _ in out]); st = np.array([s for _, s in out]); pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st); f = fwd[idx]
    return f"k={k:.2f}  straight: {len(idx):3d} bets {won[idx].sum():2d} won {st.sum():5.1f}u {pl.sum():+6.1f}u ({100*pl.sum()/max(st.sum(),1e-9):+5.0f}%)   of which forward {f.sum():3d} bets {won[idx][f].sum():2d} won {pl[f].sum():+6.1f}u"
for k in (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.0): print(go(k))
