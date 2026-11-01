"""The current rule set end to end (1 Nov 2026, founder: "run a backtest on our actual rules"). v10 holdout from 3 Jun 2026
(the trees were trained before it). Rules as live from 1 Nov:
  country/provincial: ours $1.60-$15, nothing at 3x ours, minimum odds 0.95 x (E/p^0.82)^(1/0.78) (E 1.15 under $4, else
  1.2), steps x1/x1.25/x1.5, stake_rule (Kelly on the blend, 10u cap), filled at the opening price;
  metro (Flemington, Caulfield, Moonee Valley, Sandown): the fix (C p^0.8 t^-0.2), no bet at $12+, full stakes;
  first starters never bet; races holding them are bet (race rule scrapped 1 Nov).
NOT modelled: the first-up/bounce blocks and the EARLY $8 cap (they need the sheet's angle files), so this slightly
overstates the bet count. Settled at the open less 7% (what TAB deducts on average from a bet struck at the open) and,
for comparison, at the open with no deduction (how paper now settles) and at BSP less 8%."""
import numpy as np, collections, datetime as dt
pm_cur = None
exec(open("t_metro_fix.py").read().split("H1 = ")[0])
_t = open("t_metro_orders.py").read()
exec("C, W = 0.986, 0.8\ndef run2(" + _t.split("def run2(")[1].split("pm_cur = pm0")[0])
cols = list(z["cols"]); fs = z["X"][:, cols.index("firstStarter")] == 1
bets = [(i, s) for i, s in run(pm0, ~metro) if not fs[i]] + [(i, s) for i, s in run2(metro, False) if o[i] < 12 and not fs[i]]
idx = np.array([i for i, _ in bets]); st = np.array([s for _, s in bets]); od = np.argsort(dd[idx], kind="stable")
idx, st = idx[od], st[od]
pl7 = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st); pl0 = np.where(won[idx], st * (o[idx] - 1), -st)
plb = np.where(won[idx], st * (bs[idx] - 1) * 0.92, -st)
c = np.cumsum(pl7); ddn = np.max(np.maximum.accumulate(c) - c)
days = sorted(set(dd[idx]))
print(f"{len(idx)} bets on {len(days)} race days, {won[idx].sum()} won, {st.sum():.0f}u staked (avg {st.mean():.2f}u, max {st.max():.2f}u)")
print(f"at the open less 7%: {pl7.sum():+.0f}u ({100*pl7.sum()/st.sum():+.1f}%)   no deduction: {pl0.sum():+.0f}u ({100*pl0.sum()/st.sum():+.1f}%)   BSP less 8%: {plb.sum():+.0f}u ({100*plb.sum()/st.sum():+.1f}%)")
print(f"worst drawdown {ddn:.0f}u; at $50 a unit: staked ${st.sum()*50:,.0f}, profit ${pl7.sum()*50:,.0f}, worst drawdown ${ddn*50:,.0f}")
print(f"beat BSP (open > BSP): {100*np.mean(o[idx] > bs[idx]):.0f}%")
print("\nby month              bets   staked   profit     ROI   at $50")
mo = collections.defaultdict(lambda: [0, 0.0, 0.0])
for i, s, p in zip(idx, st, pl7): a = mo[dd[i][:7]]; a[0] += 1; a[1] += s; a[2] += p
for k in sorted(mo): n, s_, p = mo[k]; print(f"  {k}            {n:5d} {s_:8.1f} {p:+8.1f} {100*p/s_:+6.1f}% {p*50:+9,.0f}")
print("\nby track type         bets   staked   profit     ROI")
for lab, sel in (("metro", metro[idx]), ("country/provincial", ~metro[idx])):
    print(f"  {lab:18s} {sel.sum():5d} {st[sel].sum():8.1f} {pl7[sel].sum():+8.1f} {100*pl7[sel].sum()/st[sel].sum():+6.1f}%")
print("\nby stake              bets   staked   profit     ROI")
for lo, hi in ((0, 1), (1, 2), (2, 4), (4, 7), (7, 10.01)):
    sel = (st >= lo) & (st < hi)
    if sel.any(): print(f"  {lo}-{hi:g}u{'':12s} {sel.sum():5d} {st[sel].sum():8.1f} {pl7[sel].sum():+8.1f} {100*pl7[sel].sum()/st[sel].sum():+6.1f}%")
dpl = collections.defaultdict(float)
for i, p in zip(idx, pl7): dpl[dd[i]] += p
v = np.array([dpl[d] for d in days]); print(f"\nrace days in profit: {np.sum(v>0)} of {len(v)}; best day {v.max():+.1f}u, worst day {v.min():+.1f}u")
wk = collections.defaultdict(float)
for d in days: wk[dt.date.fromisoformat(d).isocalendar()[:2]] += dpl[d]
w = np.array(list(wk.values())); print(f"weeks in profit: {np.sum(w>0)} of {len(w)}; worst week {w.min():+.1f}u")
