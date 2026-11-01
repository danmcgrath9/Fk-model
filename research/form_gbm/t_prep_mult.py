"""Came back worse / better as a direct adjustment (1 Nov 2026, founder: "if you have the 50 winners versus 65 why can't we
include that?"). Full history, out of fold (p_oof_blend9): fu_gain = this prep's first-up WFA rating minus the previous
prep's, set for runners second-up or later. Multiply the chance of "came back worse" (fu_gain <= -3) by kw and "came back
better" (>= +3) by kb, renormalise the race, apply the open rule ($1.60-$15, under 3x ours, $12 cap at metro not modelled),
settle at the open less 7%. Coverage: how often the comparison exists, overall and for second-up+ runners."""
import numpy as np, stake_rule, prep_feats
exec(open("t_straight_oof.py").read().split("def row(")[0])
rip = z["X"][:, cols.index("raw_run_in_prep")].astype(float)
F = prep_feats.build(z["P"], list(z["past_fields"]), rip); fg = F["fu_gain"]
P = z["P"]; pf = list(z["past_fields"]); pr = P[:, :, pf.index("prep")].astype(float); tr = P[:, :, pf.index("trial")] == 1
had_prev = np.array([np.sum((pr[i] == 1) & ~tr[i]) for i in range(len(pr))])   # first-up runs visible in the 10 stored outings
sec = m & (rip >= 2)
print(f"second-up or later: {sec.mean():.0%} of runners; of those, comparison available {np.isfinite(fg[sec]).mean():.0%}; "
      f"with 2+ preps visible {np.mean(had_prev[sec] >= 2):.0%}")
def row(lab, g):
    g = g & m; w = won[g].sum(); e = pm[g].sum(); sd = np.sqrt((pm[g] * (1 - pm[g])).sum()); print(f"  {lab:34s} n={g.sum():5d} won {w:4d} model {e:6.1f} ({w/e:4.2f}, z {(w-e)/sd:+.1f})")
print("full history, out of fold:"); row("came back worse (<= -3)", fg <= -3); row("about the same", np.abs(fg) < 3); row("came back better (>= +3)", fg >= 3)
def go(kw, kb):
    q = np.where(m & (fg <= -3), pm * kw, np.where(m & (fg >= 3), pm * kb, pm)); s_ = np.bincount(ri, weights=np.where(m, q, 0), minlength=nR); pp = np.where(m, q / np.where(s_[ri] > 0, s_[ri], 1), np.nan)
    out = []
    for i in np.where(m)[0]:
        qq = 1 / pp[i]
        if not (1.6 <= qq <= 15 and np.isfinite(o[i]) and o[i] < 3 * qq): continue
        E = 1.15 if qq < 4 else 1.2; mo = 0.95 * (E / pp[i] ** 0.82) ** (1 / 0.78)
        if o[i] >= mo: out.append((i, stake_rule.stake(pp[i] ** 0.82 * o[i] ** -0.22, o[i])))
    idx = np.array([i for i, _ in out]); st = np.array([s for _, s in out]); pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st)
    dd_ = z["date"].astype(str)[ri][idx]; h1 = dd_ < "2026-02-15"; w_ = fg[idx] <= -3
    return f"worse x{kw:.2f} better x{kb:.2f}: {len(idx):5d} bets {st.sum():6.0f}u {pl.sum():+7.0f}u ({100*pl.sum()/st.sum():+5.1f}%)  halves {100*pl[h1].sum()/st[h1].sum():+5.1f}%/{100*pl[~h1].sum()/st[~h1].sum():+5.1f}%   came-back-worse bets {w_.sum():3d}: {pl[w_].sum():+6.0f}u"
for kw, kb in ((1, 1), (0.9, 1), (0.8, 1), (0.7, 1), (0.8, 1.1), (0.8, 1.2), (1, 1.1)): print(go(kw, kb))
