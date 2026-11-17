"""b_nomodel.py: how much of the 9am edge needs OUR price at all? (18 Nov 2026)
Same walk-forward fit as a_model.py. Market-only fits (no model: they could be bet in any state), the move split into
its parts, and a second definition of the open (the first price any major showed) as a check on the move."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
with np.errstate(all="ignore"):
    first = np.array([p[1][0] if p is not None else np.nan for p in tab])
    mfirst = np.array([p[1][0] if p is not None else np.nan for p in maj])
    t_eve = np.array([price_at(tab[i], nine[i] - 900) for i in range(n)])        # TAB at 6pm the evening before
n7 = np.isfinite(B7).sum(1)
base = (P > 0) & np.isfinite(T9) & (T9 > 1) & (n7 >= 4) & np.isfinite(first) & (first > 1)
ok = race_ok(base)
L = lambda x: np.log(np.where(ok & np.isfinite(x) & (x > 0), x, 1.0))
lo, lm, lt = L(P), -L(MED7), -L(T9)
mv = L(T9) - L(first)
mv_m = np.where(np.isfinite(mfirst), L(MED7) - L(mfirst), mv)                       # median now against the first major price
mv_eve = np.where(np.isfinite(t_eve), L(T9) - L(t_eve), 0.0)                        # overnight: 6pm to 9am
mv_early = mv - mv_eve                                                               # open to 6pm the evening before
drift = np.maximum(mv, 0); firm = np.minimum(mv, 0)
F = dict(lo=lo, lm=lm, lt=lt, mv=mv, mv_m=mv_m, mv_eve=mv_eve, mv_early=mv_early, drift=drift, firm=firm)
MODELS = [("market only", ["lm"]), ("market + move (NO MODEL)", ["lm", "mv"]), ("ours + market", ["lo", "lm"]), ("ours + market + move", ["lo", "lm", "mv"]),
          ("ours + market + move (open = first major price)", ["lo", "lm", "mv_m"]), ("ours + market + overnight move + earlier move", ["lo", "lm", "mv_eve", "mv_early"]),
          ("ours + market + drift + firm", ["lo", "lm", "drift", "firm"])]
months = sorted(set(month[ok])); BURN = 4; test = np.isin(month, months[BURN:]) & ok
print("| model | weights (last fit) | test log loss | runners | bookie bets | winners | staked | profit | ROI | months up |\n|---|---|---|---|---|---|---|---|---|---|")
keep = {}
for label, fs_ in MODELS:
    X = np.column_stack([F[f] for f in fs_]); p = np.zeros(n)
    for mo in months[BURN:]:
        b = fit_cl(X, ok & (month < mo)); te = ok & (month == mo); p[te] = softmax_by_race(X @ b, ok)[te]
    keep[label] = p; fp = np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan); hit, st, pl = bets(fp, test, B7)
    mos = sorted(set(month[hit.any(1)])); up = sum(pl[month == mo].sum() > 0 for mo in mos)
    print(f"| {label} | " + ", ".join(f"{f} {x:+.2f}" for f, x in zip(fs_, b)) + f" | {logloss(p, test):.4f} | {int(hit.any(1).sum())} | {int(hit.sum())} | "
          f"{int((hit.any(1) & won).sum())} | ${st.sum():,.0f} | ${pl.sum():+,.0f} | {pl.sum() / max(st.sum(), 1):+.1%} | {up} of {len(mos)} |")
np.save(os.path.join(HERE, "fair_nomodel.npy"), keep["market + move (NO MODEL)"]); np.save(os.path.join(HERE, "fair_move.npy"), keep["ours + market + move"])
# resample race DAYS to put a range on the two rules that matter
rng = np.random.default_rng(7)
for label in ("market + move (NO MODEL)", "ours + market + move"):
    p = keep[label]; fp = np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan); hit, st, pl = bets(fp, test, B7)
    days = np.array(sorted(set(date[test]))); di = {d: i for i, d in enumerate(days)}
    idx = np.array([di.get(d, -1) for d in date]); plr = pl.sum(1); str_ = st.sum(1); m = idx >= 0
    pd_ = np.bincount(idx[m], weights=plr[m], minlength=len(days)); sd_ = np.bincount(idx[m], weights=str_[m], minlength=len(days))
    bs_ = rng.integers(0, len(days), (4000, len(days))); tot = pd_[bs_].sum(1); roi = tot / np.maximum(sd_[bs_].sum(1), 1)
    print(f"\n{label}: profit ${pd_.sum():+,.0f} on {len(days)} race days; resampled days: 5th-95th pct ${np.percentile(tot, 5):+,.0f} to ${np.percentile(tot, 95):+,.0f}, "
          f"ROI {np.percentile(roi, 5):+.0%} to {np.percentile(roi, 95):+.0%}; chance of a loss over the 13 months {np.mean(tot < 0):.1%}")
    mo_pl = [pl[month == mo].sum() for mo in sorted(set(month[test]))]
    print("  by month: " + ", ".join(f"{mo[2:]} ${v / 1000:+.0f}k" for mo, v in zip(sorted(set(month[test])), mo_pl)))
