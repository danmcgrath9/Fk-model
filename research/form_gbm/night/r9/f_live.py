"""f_live.py: the 9am rule in the form the LIVE files can feed (18 Nov 2026).
Live at 8:35am the morning run holds, per runner: our chance (v6.json), Form King's AVERAGE price now across its
bookmakers (fluc.md avg_now), its average opening price (open) and the best price now. So:
    log p = a log(ours) + b log(1 / average price now) + c log(average now / open),  renormalised over the race
Backtest stand-ins: the average of every bookmaker Betwatch holds at 9:00am; the open = TAB's first price.
Walk-forward by month (burn-in Jul-Oct 2025), then ONE final fit on every month for the live weights."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
with np.errstate(all="ignore"):
    ALL = [np.array([v for v in (d or {}).values() if v > 1.011], float) for d in bk9]
    AVG = np.array([a.mean() if len(a) >= 6 else np.nan for a in ALL]); BEST = np.array([a.max() if len(a) >= 6 else np.nan for a in ALL])
    first = np.array([p_[1][0] if p_ is not None else np.nan for p_ in tab])
base = (P > 0) & np.isfinite(AVG) & (AVG > 1) & np.isfinite(first) & (first > 1) & np.isfinite(T9)
ok = race_ok(base)
L = lambda x: np.log(np.where(ok & np.isfinite(x) & (x > 0), x, 1.0))
lo, la, mv = L(P), -L(AVG), L(AVG) - L(first)
months = sorted(set(month[ok])); test = np.isin(month, months[4:]) & ok
print("| rule | weights | test log loss | runners | bookie bets (majors) | winners | staked | profit | ROI | months up |\n|---|---|---|---|---|---|---|---|---|---|")
def run(label, cols, fixed=None):
    X = np.column_stack(cols); p = np.zeros(n)
    if fixed is not None:
        b = np.array(fixed); p = softmax_by_race(X @ b, ok)
    else:
        for mo in months[4:]:
            b = fit_cl(X, ok & (month < mo)); te = ok & (month == mo); p[te] = softmax_by_race(X @ b, ok)[te]
    fp = np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan); hit, st, pl = bets(fp, test, B7)
    mos = sorted(set(month[hit.any(1)])); up = sum(pl[month == mo].sum() > 0 for mo in mos)
    print(f"| {label} | " + ", ".join(f"{x:+.2f}" for x in b) + f" | {logloss(p, test):.4f} | {int(hit.any(1).sum())} | {int(hit.sum())} | {int((hit.any(1) & won).sum())} | "
          f"${st.sum():,.0f} | ${pl.sum():+,.0f} | {pl.sum() / max(st.sum(), 1):+.1%} | {up} of {len(mos)} |")
    return p, X
run("LIVE TODAY: 0.20 ours + 1.00 BEST price now", [lo, -L(BEST)], fixed=[0.20, 1.00])
run("0.20 ours + 1.00 average price now", [lo, la], fixed=[0.20, 1.00])
run("ours + average, fitted walk-forward", [lo, la])
p, X = run("ours + average + move, fitted walk-forward", [lo, la, mv])
bfin = fit_cl(X, ok)
print(f"\nFINAL WEIGHTS for the live rule, fitted on all 17 months: ours {bfin[0]:+.3f}, average price now {bfin[1]:+.3f}, move {bfin[2]:+.3f}")
pf = softmax_by_race(X @ bfin, ok); fp = np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan)
# what the founder would see: runners listed when the BEST price now is at the take price; how many bookmakers are at it
e = test & ran & ~fs & (fp >= 1.6) & (fp <= 15)
listed = e & (BEST >= 1.05 * fp)
nb = np.array([int((a >= 1.05 * f).sum()) if np.isfinite(f) else 0 for a, f in zip(ALL, fp)])
print(f"runners listed (best price now at the take price): {int(listed.sum())} over {len(set(date[test]))} race days = {listed.sum() / len(set(date[test])):.2f} a race day; "
      f"bookmakers at or above the take price on a listed runner: median {np.median(nb[listed]):.0f}, mean {nb[listed].mean():.1f}")
hit, st, pl = bets(fp, test, B7)
print("runners with at least one MAJOR at the take price:", int(hit.any(1).sum()), "| by day of week:",
      {d: int(hit.any(1)[np.array([__import__('datetime').date.fromisoformat(x).strftime('%a') == d for x in date])].sum()) for d in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")})
