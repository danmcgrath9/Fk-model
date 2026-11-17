"""a_model.py: a walk-forward model of the 9am market plus our price (18 Nov 2026).
The live 9am rule is log p = 0.20 log(ours) + 1.00 log(1 / price now). Here the weights are FITTED, month by month, on
earlier months only (burn-in Jul-Oct 2025), as a conditional logit over each race, with more of the 9am market in it:
  lo    log our chance            lt   log 1/TAB 9am          lm   log 1/median of the seven majors at 9am
  dtm   lt - lm (TAB against the majors)                      mv   log(TAB 9am / TAB first price): the move before 9am
  la    log 1/median of every bookmaker at 9am                lmn  log 1/shortest major (the firmest view)
Test months Nov 2025 - Nov 2026. Reported: winner log loss, and the money at the minimum bet limits: a bet to win
$1,000 ($2,000 metro) with every major whose own 9am price is at least 1.05x the model's fair price ($1.60-$15)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from common import *

with np.errstate(all="ignore"):
    ALL = [np.array(list((d or {}).values()), float) for d in bk9]
    MEDA = np.array([np.median(a) if len(a) >= 4 else np.nan for a in ALL])
    MIN7 = np.nanmin(np.where(np.isfinite(B7), B7, np.inf), 1); MIN7[~np.isfinite(MIN7)] = np.nan
    first = np.array([p[1][0] if p is not None else np.nan for p in tab])
n7 = np.isfinite(B7).sum(1)
base = (P > 0) & np.isfinite(T9) & (T9 > 1) & (n7 >= 4) & np.isfinite(MEDA) & np.isfinite(first) & (first > 1)
ok = race_ok(base)
L = lambda x: np.log(np.where(ok, x, 1.0))
lo, lt, lm, la, lmn = L(P), -L(T9), -L(MED7), -L(MEDA), -L(MIN7)
mv = L(T9) - L(first); dtm = lt - lm
F = dict(lo=lo, lt=lt, lm=lm, la=la, lmn=lmn, mv=mv, dtm=dtm)
MODELS = [("market only (median majors)", ["lm"]), ("ours + TAB", ["lo", "lt"]), ("ours + median majors", ["lo", "lm"]),
          ("ours + median + TAB gap", ["lo", "lm", "dtm"]), ("ours + median + move", ["lo", "lm", "mv"]),
          ("ours + median + TAB gap + move", ["lo", "lm", "dtm", "mv"]),
          ("ours + median all + shortest major + gap + move", ["lo", "la", "lmn", "dtm", "mv"])]
months = sorted(set(month[ok])); BURN = 4; test = np.isin(month, months[BURN:]) & ok
print(f"runners {int(ok.sum())}, races {len(np.unique(ri[ok]))}, months {months[0]} to {months[-1]}; test from {months[BURN]}: "
      f"{len(np.unique(ri[test]))} races")
fair = {}
fixed = {"LIVE 0.20 ours + 1.00 TAB": 0.20 * lo + lt, "0.20 ours + 1.00 median majors": 0.20 * lo + lm}
for k, s in fixed.items():
    fair[k] = softmax_by_race(s, ok)
print("\n| model | weights fitted on all but the last month | test log loss | against the live blend |\n|---|---|---|---|")
ll0 = logloss(fair["LIVE 0.20 ours + 1.00 TAB"], test)
for k in fixed:
    print(f"| {k} | fixed | {logloss(fair[k], test):.4f} | {logloss(fair[k], test) - ll0:+.4f} |")
for label, fs_ in MODELS:
    X = np.column_stack([F[f] for f in fs_]); p = np.zeros(n); b = None
    for mo in months[BURN:]:
        tr = ok & (month < mo); b = fit_cl(X, tr)
        te = ok & (month == mo); p[te] = softmax_by_race(X @ b, ok)[te]
    fair[label] = p
    print(f"| {label} | " + ", ".join(f"{f} {x:+.2f}" for f, x in zip(fs_, b)) + f" | {logloss(p, test):.4f} | {logloss(p, test) - ll0:+.4f} |")
# paired t on the per-race difference in winner log chance, best fitted against live
w = test & won
for label in ("ours + median majors", "ours + median + TAB gap + move"):
    d = np.log(fair[label][w]) - np.log(fair["LIVE 0.20 ours + 1.00 TAB"][w])
    print(f"{label} against live, per race: {d.mean():+.4f} (SE {d.std() / np.sqrt(len(d)):.4f}, t {d.mean() / (d.std() / np.sqrt(len(d))):.1f})")

print("\n### Money on the test months: every major at its own 9am price, 1.05x the fair price, to win the limit\n"
      "Late scratchings are in the 9am market, their bets void, winners paid after the deduction.\n\n" + MONEY_HEAD)
ok_old = race_ok(base & ~ghost); P0n = softmax_by_race(np.log(np.where(ok_old, P0, 1.0)), ok_old)
p_old = softmax_by_race(0.20 * np.log(np.where(ok_old, P0n, 1.0)) - np.log(np.where(ok_old, T9, 2.0)), ok_old)
hit, st, pl = bets(np.where(p_old > 0, 1 / np.maximum(p_old, 1e-12), np.nan), test & ok_old, B7, ded=False)
print(money_row("THE OLD TEST of the live rule: late scratchings left out of the race, no deduction", hit, st, pl, test))
for label, p in fair.items():
    fp = np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan)
    hit, st, pl = bets(fp, test, B7)
    print(money_row(label, hit, st, pl, test))
np.save(os.path.join(HERE, "fair_models.npy"), np.column_stack([fair[k] for k in fair])); open(os.path.join(HERE, "fair_models.txt"), "w").write("\n".join(fair))
for label in ("LIVE 0.20 ours + 1.00 TAB", "0.20 ours + 1.00 median majors", "ours + median + TAB gap + move"):
    p = fair[label]; fp = np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan); hit, st, pl = bets(fp, test, B7)
    print(f"\n{label}, by period\n" + MONEY_HEAD)
    for a, b_, lab in PERIODS:
        m = test & (date >= a) & (date < b_)
        if m.any(): print(money_row(lab, hit, st, pl, m))
