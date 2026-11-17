"""g_later.py: a list made LATER in the day with the market as it stands then (18 Nov 2026).
c_timing.py showed a horse that drifts up to the 9am take price is a loser. Here the fair price is re-made at each
time from TAB's price then and the move to then: log p = a log(ours) + b log(1/TAB then) + c log(TAB then / TAB first),
fitted walk-forward by month AT THAT TIME, and one bet goes on at the best major price then when it is 1.05x the fair
price. TAB alone is a poorer read of the market than the majors' median (which Betwatch's pull holds only at 9am), so
these understate what a median-based list would do; the comparison across times is the point."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
first = np.array([p_[1][0] if p_ is not None else np.nan for p_ in tab])
jump9 = -nine                                                   # minutes from 9am to the jump
TIMES = [("9:00am", lambda i: nine[i]), ("10:30am", lambda i: nine[i] + 90), ("3 h before the jump", lambda i: -180.0), ("2 h before", lambda i: -120.0),
         ("1 h before", lambda i: -60.0), ("30 min before", lambda i: -30.0), ("10 min before", lambda i: -10.0), ("2 min before", lambda i: -2.0)]
print("| list made at | weights (ours, TAB then, move) | runners bet | winners | staked | profit | ROI | months up | of them not on an earlier list: runners, profit, ROI |\n|---|---|---|---|---|---|---|---|---|")
earlier = np.zeros(n, bool)
for label, tf in TIMES:
    tt = np.array([tf(i) for i in range(n)])
    valid = np.isfinite(tt) & (tt >= nine - 1e-9) & (tt <= -2.0 + 1e-9)          # after 9am race day, before the jump
    Tt = np.array([price_at(tab[i], tt[i]) if valid[i] else np.nan for i in range(n)])
    Mt = np.array([price_at(maj[i], tt[i]) if valid[i] else np.nan for i in range(n)])
    # a ghost is in the market only until it is scratched: its last price move is the best guide Betwatch's pull gives
    lastmove = np.array([tab[i][0][-1] if tab[i] is not None else -1e9 for i in range(n)])
    inm = (P > 0) & np.isfinite(Tt) & (Tt > 1.011) & np.isfinite(first) & (first > 1) & (~ghost | (lastmove >= tt))
    ok = race_ok(inm)
    L = lambda x: np.log(np.where(ok & np.isfinite(x) & (x > 0), x, 1.0))
    X = np.column_stack([L(P), -L(Tt), L(Tt) - L(first)]); months = sorted(set(month[ok])); p = np.zeros(n); b = np.zeros(3)
    for mo in months[4:]:
        b = fit_cl(X, ok & (month < mo)); te = ok & (month == mo); p[te] = softmax_by_race(X @ b, ok)[te]
    test = ok & np.isin(month, months[4:]); fp = np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan)
    hit, st, pl = bets(fp, test, Mt[:, None]); h = hit[:, 0]
    mos = sorted(set(month[h])); up = sum(pl[month == mo].sum() > 0 for mo in mos); new = h & ~earlier
    print(f"| {label} | {b[0]:+.2f}, {b[1]:+.2f}, {b[2]:+.2f} | {int(h.sum())} | {int((h & won).sum())} | ${st.sum():,.0f} | ${pl.sum():+,.0f} | {pl.sum() / max(st.sum(), 1):+.0%} | {up} of {len(mos)} | "
          f"{int(new.sum())}, ${pl[new].sum():+,.0f}, {pl[new].sum() / max(st[new].sum(), 1):+.0%} |", flush=True)
    earlier |= h
