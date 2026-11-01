"""Old rules v new rules on the same holdout (1 Nov 2026, founder: "with our new rules give me my back ran test versus what we
were running"). v10 holdout from 3 Jun 2026, at the open less 7%. Three rule sets:
  A to 30 Oct: metro as country (no fix, full stakes); no bets on first starters, no bets in a race where one opens $6 or under
  B 30-31 Oct: metro fix at half stakes; any race holding a first starter skipped
  C from 1 Nov: metro fix, no metro bet at $12+, full stakes; first starters never bet, their races bet"""
import numpy as np, collections
pm_cur = None
exec(open("t_metro_fix.py").read().split("H1 = ")[0])
_t = open("t_metro_orders.py").read()
exec("C, W = 0.986, 0.8\ndef run2(" + _t.split("def run2(")[1].split("pm_cur = pm0")[0])
cols = list(z["cols"]); fs = z["X"][:, cols.index("firstStarter")] == 1
fs_in = np.bincount(ri, weights=fs.astype(float), minlength=nR)[ri] > 0
fs_short = np.bincount(ri, weights=(fs & (o <= 6)).astype(float), minlength=nR)[ri] > 0
cty = run(pm0, ~metro)
A = [(i, s) for i, s in cty + run(pm0, metro) if not fs[i] and not fs_short[i]]
B = [(i, s) for i, s in cty if not fs_in[i]] + [(i, s * 0.5) for i, s in run2(metro, False) if not fs_in[i]]
Cn = [(i, s) for i, s in cty if not fs[i]] + [(i, s) for i, s in run2(metro, False) if o[i] < 12 and not fs[i]]
def summ(r):
    idx = np.array([i for i, _ in r]); st = np.array([s for _, s in r]); od = np.argsort(dd[idx], kind="stable"); idx, st = idx[od], st[od]
    pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st); c = np.cumsum(pl)
    mo = collections.defaultdict(float)
    for i, p in zip(idx, pl): mo[dd[i][:7]] += p
    wk = collections.defaultdict(float)
    import datetime as dt
    for i, p in zip(idx, pl): wk[dt.date.fromisoformat(dd[i]).isocalendar()[:2]] += p
    w = np.array(list(wk.values()))
    met = metro[idx]
    return dict(n=len(idx), st=st.sum(), pl=pl.sum(), roi=100 * pl.sum() / st.sum(), dd=np.max(np.maximum.accumulate(c) - c),
                mo=mo, wk=f"{np.sum(w > 0)}/{len(w)}", worstwk=w.min(), metro=(met.sum(), pl[met].sum(), 100 * pl[met].sum() / st[met].sum()))
R = {"A to 30 Oct": summ(A), "B 30-31 Oct": summ(B), "C new (1 Nov)": summ(Cn)}
print(f"{'':16s}" + "".join(f"{k:>18s}" for k in R))
for lab, f in [("bets", lambda r: f"{r['n']}"), ("staked", lambda r: f"{r['st']:.0f}u"), ("profit", lambda r: f"{r['pl']:+.0f}u"),
               ("ROI", lambda r: f"{r['roi']:+.1f}%"), ("profit at $50", lambda r: f"${r['pl']*50:,.0f}"),
               ("worst drawdown", lambda r: f"{r['dd']:.0f}u"), ("weeks in profit", lambda r: r['wk']), ("worst week", lambda r: f"{r['worstwk']:+.1f}u"),
               ("metro bets", lambda r: f"{r['metro'][0]}"), ("metro profit", lambda r: f"{r['metro'][1]:+.0f}u ({r['metro'][2]:+.0f}%)")]:
    print(f"{lab:16s}" + "".join(f"{f(r):>18s}" for r in R.values()))
for m in sorted(R["C new (1 Nov)"]["mo"]):
    print(f"{m:16s}" + "".join(f"{r['mo'][m]:+17.0f}u" for r in R.values()))
