"""Plunge horses (3 Nov 2026, founder: "these horses that we underrate, what's the key types? How can we get better at
these? Because we'd take more units on early"). v10 holdout 3 Jun - 13 Oct. A PLUNGE is BSP at or under 0.6x the open
(the horse at least nearly halves in price). For each feature bucket: how often our bets plunge, and our A/E (winners
against what our price expected; over 1.00 = we underrate them)."""
import numpy as np
src = open("t_all_rules.py").read().split('summ(plan(pm0), "all rules')[0]
exec(src)
X = z["X"]; cols = list(map(str, z["cols"])); col = lambda c: X[:, cols.index(c)].astype(float)
b = plan(pmS); idx = np.array([i for i, _ in b]); st = np.array([s for _, s in b])
ratio = bs / o; ours_all = 1 / np.where(np.isfinite(pmS) & (pmS > 0), pmS, np.nan)
band = m & ~fs & (ours_all >= 1.6) & (ours_all <= 15)
A = np.where(band)[0]   # every runner we could rate in the band
def ae(ii):
    w = won[ii].sum(); return w, pmS[ii].sum(), (1 / bs[ii]).sum()
def report(lab, buckets, sel_name, sel):
    print(f"\n{lab} [{sel_name}]")
    print(f"  {'bucket':34s} {'n':>5s} {'plunge':>7s} {'BSP/open':>8s} {'won':>4s} {'ours exp':>8s} {'A/E ours':>8s} {'A/E BSP':>7s}")
    for bl, k in buckets:
        ii = sel[k[sel]] if k.dtype == bool else sel[k]
        if len(ii) < 25: print(f"  {bl:34s} {len(ii):5d}  (too few)"); continue
        w, eo, eb = ae(ii); pr = (ratio[ii] <= 0.6).mean()
        print(f"  {bl:34s} {len(ii):5d} {100*pr:6.0f}% {np.median(ratio[ii]):8.2f} {w:4d} {eo:8.1f} {w/eo:8.2f} {w/eb:7.2f}")
def terciles(c, name):
    v = col(c); q = np.nanpercentile(v[A], [33.3, 66.7])
    return [(f"{name} low (<= {q[0]:.2g})", v <= q[0]), (f"{name} mid", (v > q[0]) & (v <= q[1])), (f"{name} high (> {q[1]:.2g})", v > q[1]), (f"{name} missing", ~np.isfinite(v))]
def flag(c, name):
    v = col(c); return [(f"{name}: yes", v > 0), (f"{name}: no", ~(v > 0))]
def bands(v, cuts, name, fmt="{:g}"):
    out = []; lo = -np.inf
    for hi in cuts + [np.inf]:
        out.append((f"{name} {fmt.format(lo) if np.isfinite(lo) else ''}-{fmt.format(hi) if np.isfinite(hi) else ''}", (v > lo) & (v <= hi))); lo = hi
    return out
days = np.exp(col("raw_days_log")) if "raw_days_log" in cols else col("daysSinceLastRace")
starts = col("raw_starts")
feats = [
    ("open price", bands(o, [3, 5, 8, 12, 20], "open $")),
    ("our price", bands(ours_all, [3, 5, 8], "ours $")),
    ("open / ours (overlay at the open)", bands(o / ours_all, [1.2, 1.5, 2.0, 2.5], "open/ours x")),
    ("days since last run", bands(days, [14, 28, 60, 120], "days")),
    ("first up", flag("raw_first_up", "first up")),
    ("career starts", bands(starts, [2, 5, 10, 20], "starts")),
    ("age", bands(col("raw_age"), [2, 3, 4], "age")),
    ("trialled recently", flag("trialled_recently", "trialled")),
    ("gear change first time", flag("gear_first_time", "first-time gear")),
    ("blinkers first time", flag("blinkers_first", "blinkers first")),
    ("jockey's only ride at the meeting", flag("jockeysOnlyRideAtMeeting", "only ride")),
    ("trainer's only runner at the meeting", flag("trainersOnlyRaceAtMeeting", "only runner")),
    ("jockey 12-month win %", terciles("jockeyForm_lastTwelveMonthWinPercentage", "jockey win%")),
    ("trainer 12-month win %", terciles("trainerForm_lastTwelveMonthWinPercentage", "trainer win%")),
    ("last start market move (fl_last_move)", terciles("fl_last_move", "last-start move")),
    ("times backed in last 5 (fl_n_backed5)", bands(col("fl_n_backed5"), [0, 1, 2], "backed in last 5")),
    ("beat the market last start", flag("raw_beat_market_last", "beat market last")),
    ("last start finish", bands(col("raw_last"), [1, 3, 6], "last finish")),
    ("class (raw_mkt_class)", terciles("raw_mkt_class", "mkt class")),
    ("class drop (raw_class_win)", terciles("raw_class_win", "class_win")),
    ("barrier", bands(col("raw_barrier"), [3, 6, 9, 12], "barrier")),
    ("early speed (sm_early_speed)", terciles("sm_early_speed", "early speed")),
    ("dual acceptor", flag("raw_dual_acceptor", "dual acceptor")),
    ("metro", [("metro", metro), ("country", ~metro)]),
]
print("THE LIVE BOOK (our sheet bets at the open): which of them plunge, and where we underrate")
for lab, bk in feats: report(lab, bk, "sheet bets", idx)
print("\n\nEVERY RUNNER WE RATE $1.60-$15 (first starters out): the same cuts")
for lab, bk in feats[:3] + feats[4:6] + feats[7:12] + feats[14:17] + feats[-1:]: report(lab, bk, "all rated runners", A)
