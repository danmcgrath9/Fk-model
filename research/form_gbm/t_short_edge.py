"""Should the edge be lower for horses that OPEN under $6? (8 Nov 2026, founder: "For horses that open less than $6, do you
think we should make our value slightly less? Does that make sense from an ROI point of view")
v10 holdout (3 Jun on, trees trained before), country/provincial (the metro fix is its own rule), first starters out,
ours $1.60-$15, nothing at 3x ours. The edge an order needs at the open price o: e = p^0.82 x (o/0.95)^0.78 (the live
minimum, 0.95 x (E/p^0.82)^(1/0.78), solved for E). Live: E 1.2, 1.15 under $4. Part 1 flat 1u by open band and edge;
part 2 the live staking with a lower E under $6, the bets it ADDS and what they made. Settled at the open less 7%
(TAB's average deduction on an open bet), and at BSP less 8%."""
import numpy as np, collections, stake_rule
exec(open("t_metro_fix.py").read().split("H1 = ")[0])
cols = list(z["cols"]); fs = z["X"][:, cols.index("firstStarter")] == 1
pm = pm0; ours = 1 / pm
base_ok = m & ~metro & ~fs & (ours >= 1.6) & (ours <= 15) & (o < 3 * ours)
e = pm ** 0.82 * (o / 0.95) ** 0.78
H1 = dd < "2026-08-01"
def roi(sel, st=None):
    idx = np.where(sel)[0]
    if len(idx) == 0: return "    0"
    s = np.ones(len(idx)) if st is None else st
    p7 = np.where(won[idx], s * (o[idx] - 1) * 0.93, -s).sum(); pb = np.where(won[idx], s * (bs[idx] - 1) * 0.92, -s).sum()
    return f"{len(idx):5d} {won[idx].sum():4d} won  open-7% {100*p7/s.sum():+6.1f}%  BSP {100*pb/s.sum():+6.1f}%"
print("PART 1: flat 1u, every country runner by open price and edge at the open (live needs 1.2; 1.15 under $4)\n")
bands = ((1.6, 4), (4, 6), (6, 10), (10, 45))
bins = ((0.90, 1.00), (1.00, 1.05), (1.05, 1.10), (1.10, 1.15), (1.15, 1.20), (1.20, 1.30), (1.30, 1.50), (1.50, 9))
for lo, hi in bands:
    print(f"opens ${lo:g}-${hi:g}")
    for a, b in bins:
        sel = base_ok & (o >= lo) & (o < hi) & (e >= a) & (e < b)
        print(f"  edge {a:.2f}-{b:.2f}  {roi(sel)}   (Jun-Jul {roi(sel & H1)[:5].strip()} bets {roi(sel & H1)[-7:]}, Aug-Oct {roi(sel & ~H1)[-7:]})")
    print()
def run(Eshort, under=6.0):
    out = {}
    for i in np.where(base_ok)[0]:
        qq = ours[i]
        E = Eshort if o[i] < under else 1.2
        if o[i] < 4: E = min(E, 1.15)
        mo = 0.95 * (E / pm[i] ** 0.82) ** (1 / 0.78)
        if o[i] < mo: continue
        tiers = [mo * x for x in (1.0, 1.25, 1.5) if mo * x < 3 * qq]; tot = prev = 0.0
        for k, tt in enumerate(tiers):
            tp = tiers[k + 1] if k + 1 < len(tiers) else tt
            s_ = stake_rule.stake(pm[i] ** 0.82 * tp ** -0.22, tp, False, fld[i]); add = max(0.0, s_ - prev); prev = max(prev, s_)
            if o[i] >= tt: tot += add
        if tot > 0: out[i] = tot
    return out
def line(d, sel=None):
    idx = np.array([i for i in d if sel is None or sel[i]]); st = np.array([d[i] for i in idx]) if len(idx) else np.array([])
    if len(idx) == 0: return "    0 bets"
    p7 = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st).sum(); pb = np.where(won[idx], st * (bs[idx] - 1) * 0.92, -st).sum()
    return f"{len(idx):5d} bets {won[idx].sum():4d} won {st.sum():7.1f}u  open-7% {p7:+7.1f}u ({100*p7/st.sum():+5.1f}%)  BSP {pb:+7.1f}u ({100*pb/st.sum():+5.1f}%)"
print("PART 2: the live staking, edge under $6 lowered (everything else as live)\n")
live = run(1.2)
print(f"live (1.2; 1.15 under $4)       {line(live)}")
for E in (1.15, 1.10, 1.05):
    d = run(E); add = {i: d[i] for i in d if i not in live}; ch = {i: d[i] for i in d}
    print(f"\nunder $6 at {E:.2f}               {line(d)}")
    print(f"  the bets it ADDS              {line(add)}")
    print(f"    Jun-Jul                     {line(add, H1)}")
    print(f"    Aug-Oct                     {line(add, ~H1)}")
    print(f"  opens under $4 only           {line(add, o < 4)}")
    print(f"  opens $4-$6 only              {line(add, (o >= 4) & (o < 6))}")
print(f"\nlive bets that open under $6:   {line(live, o < 6)}")
print(f"live bets that open $6+:        {line(live, o >= 6)}")
