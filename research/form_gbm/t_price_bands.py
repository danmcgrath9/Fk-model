"""Do we overrate longer prices? (1 Nov 2026, founder: "we overestimate the market on longer odds... we nail the
favourites... higher staked units on those favourites versus the longer shots?") v10 holdout from 3 Jun, at the open
less 7%. Country/provincial at the live rule, metro at the fix (full-size stakes)."""
import numpy as np, collections
pm_cur = None
exec(open("t_metro_fix.py").read().split("H1 = ")[0])
_t = open("t_metro_orders.py").read()
exec("C, W = 0.986, 0.8\ndef run2(" + _t.split("def run2(")[1].split("pm_cur = pm0")[0])
cols = list(z["cols"]); fs = z["X"][:, cols.index("firstStarter")] == 1
B = [(0, 3, "under $3"), (3, 5, "$3-5"), (5, 8, "$5-8"), (8, 12, "$8-12"), (12, 20, "$12-20"), (20, 999, "$20+")]
def bands(r, chance, title):
    g = collections.defaultdict(lambda: [0, 0.0, 0.0, 0, 0.0])
    for i, s in r:
        k = next(b[2] for b in B if b[0] <= o[i] < b[1]); a = g[k]
        a[0] += 1; a[1] += s; a[2] += s * ((o[i] - 1) * 0.93 if won[i] else -1); a[3] += int(won[i]); a[4] += chance(i)
    print(title + f"   {'bets':>5s} {'won':>4s} {'exp':>6s} {'won/exp':>7s} {'staked':>7s} {'profit':>8s} {'ROI':>7s} {'avg stake':>9s}")
    for b in B:
        if b[2] in g: n, st, pl, w, e = g[b[2]]; print(f"  {b[2]:10s}  {n:5d} {w:4d} {e:6.1f} {w/e:7.2f} {st:7.1f} {pl:+8.1f} {100*pl/st:+6.1f}% {st/n:9.2f}")
cty = [(i, s) for i, s in run(pm0, ~metro) if not fs[i]]
met = run2(metro, False)
bands(cty, lambda i: pm0[i], "COUNTRY/PROVINCIAL by opening price")
bands(met, lambda i: 0.986 * pm0[i] ** 0.8 * o[i] ** -0.2, "\nMETRO (fix) by opening price")
def scheme(r, f):
    st = np.array([s * f(i) for i, s in r]); idx = np.array([i for i, _ in r])
    pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st); od = np.argsort(dd[idx], kind="stable"); c = np.cumsum(pl[od])
    keep = st > 0; h1 = dd[idx] < "2026-08-01"
    return f"{keep.sum():5d} bets {st.sum():7.0f}u {pl.sum():+7.0f}u ({100*pl.sum()/st.sum():+5.1f}%)  worst DD {np.max(np.maximum.accumulate(c)-c):4.0f}u  halves {100*pl[h1].sum()/st[h1].sum():+4.0f}% / {100*pl[~h1].sum()/st[~h1].sum():+4.0f}%"
print("\nSTAKING BY PRICE (multiplier on the live stake)")
for lab, f in [("live", lambda i: 1.0), ("x1.5 under $5", lambda i: 1.5 if o[i] < 5 else 1.0),
               ("x0.5 at $12+", lambda i: 0.5 if o[i] >= 12 else 1.0), ("x1.5 under $5, x0.5 at $12+", lambda i: 1.5 if o[i] < 5 else (0.5 if o[i] >= 12 else 1.0)),
               ("no bets at $20+", lambda i: 0.0 if o[i] >= 20 else 1.0), ("no bets at $12+", lambda i: 0.0 if o[i] >= 12 else 1.0)]:
    print(f" country {lab:30s}", scheme(cty, f))
for lab, f in [("live", lambda i: 1.0), ("no bets at $12+", lambda i: 0.0 if o[i] >= 12 else 1.0),
               ("no bets at $8+", lambda i: 0.0 if o[i] >= 8 else 1.0), ("x1.5 under $5, none $12+", lambda i: 1.5 if o[i] < 5 else (0.0 if o[i] >= 12 else 1.0))]:
    print(f" metro   {lab:30s}", scheme(met, f))
u = [(i, s) for i, s in met if o[i] < 12]; idx = np.array([i for i, _ in u])
print(f"\nmetro under $12: won {won[idx].sum()} v fixed chance {np.sum(0.986*pm0[idx]**0.8*o[idx]**-0.2):.1f}; country: won/exp {sum(won[i] for i,_ in cty)}/{sum(pm0[i] for i,_ in cty):.1f}")
print(" metro cap $12, full stakes", scheme(met, lambda i: 0.0 if o[i] >= 12 else 1.0))
print(" metro cap $12, half stakes", scheme(met, lambda i: 0.0 if o[i] >= 12 else 0.5))
