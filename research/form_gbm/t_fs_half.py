"""(1 Nov 2026, founder: "Are we sure on this first starter rule?" and "this half stake stuff, I think we scrap it if we changed
the rule and our edge is bigger now?") v10 holdout from 3 Jun. Country/provincial at the live open rule, metro at the metro
fix (order-sheet form, t_metro_orders.py). Settled at the open less 7% (deductions, as every backtest) and at BSP less 8%."""
import numpy as np, collections
pm_cur = None
exec(open("t_metro_fix.py").read().split("H1 = ")[0])
_t = open("t_metro_orders.py").read()
exec("C, W = 0.986, 0.8\ndef run2(" + _t.split("def run2(")[1].split("pm_cur = pm0")[0])
cols = list(z["cols"]); fs = z["X"][:, cols.index("firstStarter")] == 1
fs_in_race = np.bincount(ri, weights=fs.astype(float), minlength=nR)[ri] > 0
fs_short = np.bincount(ri, weights=(fs & (o <= 6)).astype(float), minlength=nR)[ri] > 0
pm_cur = pm0
def stats(r):
    idx = np.array([i for i, _ in r]); st = np.array([s for _, s in r])
    pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st); plb = np.where(won[idx], st * (bs[idx] - 1) * 0.92, -st)
    od = np.argsort(dd[idx], kind="stable"); c = np.cumsum(pl[od]); ddn = np.max(np.maximum.accumulate(c) - c)
    h1 = dd[idx] < "2026-08-01"
    return f"{len(r):5d} bets {st.sum():7.0f}u  open {pl.sum():+7.0f}u ({100*pl.sum()/st.sum():+5.1f}%)  BSP {100*plb.sum()/st.sum():+5.1f}%  worst DD {ddn:4.0f}u  halves {100*pl[h1].sum()/st[h1].sum():+4.0f}% / {100*pl[~h1].sum()/st[~h1].sum():+4.0f}%"
country = run(pm0, ~metro); metro_full = run2(metro, False); metro_half = run2(metro, True)
print("METRO with the fix")
print(" full stake ", stats(metro_full)); print(" half stake ", stats(metro_half))
print(" (no fix, as before 31 Oct)", stats(run(pm0, metro)))
print("\nFIRST-STARTER RULE (country/provincial, live rule; metro full-stake fix)")
allb = country + metro_full
for lab, keep in [("no rule", lambda i: True),
                  ("no bets ON first starters only", lambda i: not fs[i]),
                  ("+ skip race if a first starter opens $6 or shorter (26 Oct)", lambda i: not fs[i] and not fs_short[i]),
                  ("skip any race with a first starter (30 Oct, live)", lambda i: not fs_in_race[i])]:
    print(f" {lab:60s}", stats([(i, s) for i, s in allb if keep(i)]))
# the races the live rule removes but the $6 rule keeps
gap = [(i, s) for i, s in allb if not fs[i] and not fs_short[i] and fs_in_race[i]]
print(f" {'  of which: races with a first starter, none at $6 or shorter':60s}", stats(gap))
# calibration of the metro-fix bets: wins v the fixed chance at the open, and v the old chance
idx = np.array([i for i, _ in metro_full]); pfix = 0.986 * pm0[idx] ** 0.8 * o[idx] ** -0.2
print(f"\nmetro-fix bets: won {won[idx].sum()} v fixed chance {pfix.sum():.1f} (old model {pm0[idx].sum():.1f}, open price {np.sum(1/o[idx]):.1f})")
ib = np.array([i for i, _ in country]); print(f"country bets:   won {won[ib].sum()} v model {pm0[ib].sum():.1f}")
