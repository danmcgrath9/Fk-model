"""Tick-over trials (1 Nov 2026, founder: "horses in the middle of their prep... have a tick over trial, where they don't show
anything cause they're already fit... -10% for trial form... but there was no intent"). v10 holdout from 3 Jun: horses whose
most recent outing is a trial, split by mid-prep (a race start in the 60 days before the trial) v first-up/spelled, and by
how the trial went. Actual wins v the model's chance (normalised) and v the market's (BSP)."""
import numpy as np, stake_rule
pm_cur = None
exec(open("t_metro_fix.py").read().split("H1 = ")[0])
P = z["P"]; pf = list(z["past_fields"])
tr = P[:, :, pf.index("trial")] == 1; db = P[:, :, pf.index("days_before")].astype(float)
fin = P[:, :, pf.index("finish")].astype(float); mg = P[:, :, pf.index("margin")].astype(float); runs = P[:, :, pf.index("runners")].astype(float)
last_is_trial = tr[:, 0] & np.isfinite(db[:, 0])
# a race start (not a trial) within 60 days before that trial = mid-prep tick-over
gap = db[:, 1:] - db[:, [0]]
mid = last_is_trial & np.any(~tr[:, 1:] & np.isfinite(db[:, 1:]) & (gap > 0) & (gap <= 60), axis=1)
first = last_is_trial & ~mid
poor = (fin[:, 0] >= 4) | (mg[:, 0] > 2.5); good = (fin[:, 0] <= 3) & ~(mg[:, 0] > 2.5)
ib = np.where(m, 1 / bs, 0); sb = np.bincount(ri, weights=ib, minlength=nR); pb = np.where(m, ib / np.where(sb[ri] > 0, sb[ri], 1), np.nan)
def row(lab, g):
    g = g & m; w = won[g].sum(); e = pm0[g].sum(); eb = pb[g].sum(); sd = np.sqrt((pm0[g] * (1 - pm0[g])).sum())
    print(f"  {lab:44s} n={g.sum():5d} won {w:4d}  model {e:6.1f} ({w/e:4.2f}, z {(w-e)/sd:+.1f})  market {eb:6.1f} ({w/eb:4.2f})")
print("LAST OUTING A TRIAL")
row("mid-prep (tick-over), trial poor (4th+ or >2.5L)", mid & poor)
row("mid-prep (tick-over), trial good (top 3, <=2.5L)", mid & good)
row("first-up / spelled, trial poor", first & poor)
row("first-up / spelled, trial good", first & good)
row("all horses (check)", np.ones(len(m), bool))
# our bets on the mid-prep poor-trial group, live rule (country) at the open less 7%
bets = [(i, s) for i, s in run(pm0, ~metro) if mid[i] and poor[i]]
if bets:
    idx = np.array([i for i, _ in bets]); st = np.array([s for _, s in bets]); pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st)
    print(f"\nlive-rule bets on mid-prep poor-trial horses: {len(idx)} bets, {won[idx].sum()} won, {st.sum():.1f}u, {pl.sum():+.1f}u ({100*pl.sum()/st.sum():+.0f}%)")
