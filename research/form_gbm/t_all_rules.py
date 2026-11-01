"""Every live rule as of 1 Nov 2026 evening, on the v10 holdout (3 Jun - 13 Oct, trees trained before it), at the open less 7%.
Country/provincial: open rule, steps, stake_rule (10u). Metro: fix (C p^0.8 t^-0.2), no bet at $12+, full stakes. First
starters never bet, their races bet. Back-settler shade OFF. Flemington straight (<=1200m): forward runners (settle share
under 0.3) x0.7, race renormalised. NOT modelled: first-up/bounce blocks and EARLY caps (need the sheet's angle files)."""
import numpy as np, collections, datetime as dt
pm_cur = None
exec(open("t_metro_fix.py").read().split("H1 = ")[0])
_t = open("t_metro_orders.py").read(); exec("C, W = 0.986, 0.8\ndef run2(" + _t.split("def run2(")[1].split("pm_cur = pm0")[0])
cols = list(z["cols"]); fs = z["X"][:, cols.index("firstStarter")] == 1; ss = z["X"][:, cols.index("raw_settle_share")].astype(float)
dist = z["distance"].astype(float)[ri]; straight = np.array([t.startswith("Flemington") for t in trk])[ri] & (dist <= 1200)
q = np.where(m & straight & (ss < 0.3), pm0 * 0.7, pm0); s_ = np.bincount(ri, weights=np.where(m, q, 0), minlength=nR); pmS = np.where(m, q / np.where(s_[ri] > 0, s_[ri], 1), np.nan)
def plan(p):
    global pm0
    keep = pm0; pm0 = p
    b = [(i, s) for i, s in run(p, ~metro) if not fs[i]] + [(i, s) for i, s in run2(metro, False) if o[i] < 12 and not fs[i]]
    pm0 = keep; return b
def summ(b, lab):
    idx = np.array([i for i, _ in b]); st = np.array([s for _, s in b]); od = np.argsort(dd[idx], kind="stable"); idx, st = idx[od], st[od]
    pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st); c = np.cumsum(pl); h1 = dd[idx] < "2026-08-01"
    wk = collections.defaultdict(float)
    for i, p_ in zip(idx, pl): wk[dt.date.fromisoformat(dd[i]).isocalendar()[:2]] += p_
    w = np.array(list(wk.values()))
    print(f"{lab:34s} {len(idx):5d} bets {won[idx].sum():4d} won {st.sum():6.0f}u {pl.sum():+6.0f}u ({100*pl.sum()/st.sum():+5.1f}%)  ${pl.sum()*50:+8,.0f}  DD {np.max(np.maximum.accumulate(c)-c):3.0f}u  halves {100*pl[h1].sum()/st[h1].sum():+3.0f}%/{100*pl[~h1].sum()/st[~h1].sum():+3.0f}%  weeks {np.sum(w>0)}/{len(w)} worst {w.min():+.1f}u")
    return idx, st, pl
summ(plan(pm0), "all rules, no straight markdown")
idx, st, pl = summ(plan(pmS), "ALL RULES (live)")
mo = collections.defaultdict(lambda: [0, 0.0, 0.0])
for i, s, p in zip(idx, st, pl): a = mo[dd[i][:7]]; a[0] += 1; a[1] += s; a[2] += p
for k in sorted(mo): n, s, p = mo[k]; print(f"   {k}  {n:4d} bets {s:6.1f}u {p:+7.1f}u ({100*p/s:+5.1f}%)  ${p*50:+8,.0f}")
