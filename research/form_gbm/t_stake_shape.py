"""Staking shape test (2 Nov 2026, founder: "So how could we ever get a 10u bet ... Try and run the test - do what you
think is right"). Every live rule (t_all_rules.py: v10 holdout 3 Jun - 13 Oct, settled at the open less 7%); only the
stake changes. Our effective chance is recovered from the blended one the sheet uses: ours = (pp t^0.22)^(1/0.82)
(metro: the metro-fixed chance). Variants: the blend weight on our price, a steeper Kelly (power), and the multiplier.
Scale-free reads: ROI and profit / worst drawdown; each variant is also shown scaled to the live rule's turnover."""
import numpy as np, collections, datetime as dt, stake_rule
src = open("t_all_rules.py").read().split('summ(plan(pm0), "all rules')[0]
exec(src)
live_stake = stake_rule.stake
def kel(pp, t): return max(0.0, ((pp * t) ** 0.5 - 1) / (t - 1)) if t > 1 else 0.0
MODE = {}
def var_stake(pp, t, only_ride=False, field=0):
    if t <= 1: return 0.0
    ours = (pp * t ** 0.22) ** (1 / 0.82)
    w = MODE.get("w", 0.82); pp2 = ours ** w * t ** -(1 - w) if w != 0.82 else pp
    k = kel(pp2, t); g = MODE.get("g", 1.0); A = MODE.get("A", 125 * 5 / 8); cap = MODE.get("cap", 10.0)
    return round(min(cap, A * k ** g * (0.08 ** (1 - g) if g != 1 else 1)), 2)
def evaluate(lab, scale=None):
    stake_rule.stake = var_stake
    b = plan(pmS); stake_rule.stake = live_stake
    idx = np.array([i for i, _ in b]); st = np.array([s for _, s in b]); od = np.argsort(dd[idx], kind="stable"); idx, st = idx[od], st[od]
    if scale: st = st * scale / st.sum()
    pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st); c = np.cumsum(pl); D = np.max(np.maximum.accumulate(c) - c)
    h1 = dd[idx] < "2026-08-01"
    big = st >= 7.5
    print(f"{lab:38s} {len(idx):5d} bets {st.sum():6.0f}u {pl.sum():+6.0f}u ({100*pl.sum()/st.sum():+5.1f}%)  DD {D:4.0f}u  P/DD {pl.sum()/D:4.1f}  "
          f"halves {100*pl[h1].sum()/st[h1].sum():+3.0f}%/{100*pl[~h1].sum()/st[~h1].sum():+3.0f}%  7.5u+ bets {big.sum():3d} ({100*pl[big].sum()/max(st[big].sum(),1e-9):+4.0f}%)  max {st.max():4.1f}u")
    return idx, st, pl
print("== as staked")
MODE.clear(); i0, s0, p0 = evaluate("LIVE: blend 0.82, Kelly x78, cap 10")
T = s0.sum()
runs = [("ours 0.90 / market 0.10", dict(w=0.90)), ("ours only (no market blend)", dict(w=1.0)),
        ("steeper: Kelly^1.5", dict(g=1.5)), ("steeper: Kelly^2", dict(g=2.0)),
        ("live shape x1.5 (cap 10)", dict(A=125*5/8*1.5)), ("live shape x2 (cap 10)", dict(A=125*5/8*2)),
        ("ours 0.90 + Kelly^1.5", dict(w=0.90, g=1.5)), ("live, cap 15", dict(cap=15.0))]
res = {}
for lab, md in runs:
    MODE.clear(); MODE.update(md); res[lab] = evaluate(lab)
print("\n== scaled to the live rule's turnover (same money through the books)")
for lab, md in runs[:4] + runs[6:7]:
    MODE.clear(); MODE.update(md); evaluate(lab, scale=T)
print("\n== LIVE by stake band")
for lo, hi in ((0, 1), (1, 2), (2, 3), (3, 5), (5, 7.5), (7.5, 10.01)):
    k = (s0 >= lo) & (s0 < hi)
    if k.any(): print(f"  {lo:>4}-{hi:<5}u {k.sum():4d} bets {s0[k].sum():6.0f}u {p0[k].sum():+6.0f}u ({100*p0[k].sum()/s0[k].sum():+5.1f}%)  won {won[i0[k]].sum()}")
print("\n== LIVE by edge at the open (our chance x open price)")
ours = pmS[i0]; e = ours * o[i0]
for lo, hi in ((1.0, 1.3), (1.3, 1.5), (1.5, 1.8), (1.8, 2.2), (2.2, 9)):
    k = (e >= lo) & (e < hi)
    if k.any(): print(f"  edge {lo:.1f}-{hi:.1f}  {k.sum():4d} bets {s0[k].sum():6.0f}u {p0[k].sum():+6.0f}u ({100*p0[k].sum()/s0[k].sum():+5.1f}%)  avg stake {s0[k].mean():.2f}u")
