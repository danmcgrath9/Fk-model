"""The new staking (x2 when the open is 2.2x+ our price and we rate it under $8, 10u cap) against the old, every live
rule, v10 holdout 3 Jun - 13 Oct at the open less 7%: units staked, profit and ROI by month and in total (2 Nov 2026)."""
import numpy as np, collections
src = open("t_all_rules.py").read().split('summ(plan(pm0), "all rules')[0]
exec(src)
b = plan(pmS); idx = np.array([i for i, _ in b]); st0 = np.array([s for _, s in b]); od = np.argsort(dd[idx], kind="stable"); idx, st0 = idx[od], st0[od]
e = pmS[idx] * o[idx]; ours = 1 / pmS[idx]; big = (e >= 2.2) & (ours < 8)
st1 = np.minimum(10, np.where(big, st0 * 2, st0))
pl = lambda st: np.where(won[idx], st * (o[idx] - 1) * 0.93, -st)
p0, p1 = pl(st0), pl(st1)
mo = collections.OrderedDict()
for j, i in enumerate(idx):
    a = mo.setdefault(dd[i][:7], [0, 0, 0.0, 0.0, 0.0, 0.0]); a[0] += 1; a[1] += big[j]
    a[2] += st0[j]; a[3] += p0[j]; a[4] += st1[j]; a[5] += p1[j]
print("| month | bets | doubled | old staked | old profit | old ROI | new staked | new profit | new ROI |")
for k, (n, nb, s0, q0, s1, q1) in mo.items():
    print(f"| {k} | {n} | {nb} | {s0:.0f}u | {q0:+.0f}u | {100*q0/s0:+.1f}% | {s1:.0f}u | {q1:+.0f}u | {100*q1/s1:+.1f}% |")
def dd_(p):
    c = np.cumsum(p); return np.max(np.maximum.accumulate(c) - c)
wk = collections.defaultdict(lambda: [0.0, 0.0])
import datetime as dt
for j, i in enumerate(idx):
    w = dt.date.fromisoformat(dd[i]).isocalendar()[:2]; wk[w][0] += p0[j]; wk[w][1] += p1[j]
W = np.array(list(wk.values()))
print(f"\nTOTAL old: {len(idx)} bets, {st0.sum():.0f}u staked, {p0.sum():+.0f}u ({100*p0.sum()/st0.sum():+.1f}%), worst drawdown {dd_(p0):.0f}u, "
      f"winning weeks {np.sum(W[:,0]>0)}/{len(W)}, worst week {W[:,0].min():+.1f}u")
print(f"TOTAL new: {len(idx)} bets ({big.sum()} doubled), {st1.sum():.0f}u staked, {p1.sum():+.0f}u ({100*p1.sum()/st1.sum():+.1f}%), worst drawdown {dd_(p1):.0f}u, "
      f"winning weeks {np.sum(W[:,1]>0)}/{len(W)}, worst week {W[:,1].min():+.1f}u")
print(f"per week (~{len(W)} weeks): old {p0.sum()/len(W):+.1f}u, new {p1.sum()/len(W):+.1f}u; at $37.50 a unit: old ${p0.sum()*37.5/len(W):+,.0f}, new ${p1.sum()*37.5/len(W):+,.0f} a week")
print(f"in dollars at $37.50: old {st0.sum()*37.5:,.0f} staked {p0.sum()*37.5:+,.0f}; new {st1.sum()*37.5:,.0f} staked {p1.sum()*37.5:+,.0f}")
k = big; print(f"the doubled bets alone: {k.sum()} bets, {won[idx[k]].sum()} won, new stake {st1[k].sum():.0f}u, profit {p1[k].sum():+.0f}u ({100*p1[k].sum()/st1[k].sum():+.0f}%)")
