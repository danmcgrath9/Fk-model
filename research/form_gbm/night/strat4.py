"""More cuts of the live sheet's bets (night of 10 Nov 2026): how many of our bets sit in the same race, the race's
number on the card, and the size of the scratching shortfall. Walk-forward trees, four periods, live sheet rules, fitted
deduction by race (deduction_model.py) so races that lost runners are not flattered.
    python3.13 strat4.py   (night folder)"""
import collections, numpy as np, sys
sys.argv = ["x"]
exec(open("strat3.py").read().split("P_wf = ")[0])
P_wf = np.where(date >= "2026-06-03", np.load("preds/base_A.npy"), np.load("preds/base_B.npy")).astype(float)
ded = np.load("ded_r.npy")[ri]; oos = date >= "2026-01-01"
I, S_, Pr = sheet(P_wf, oos, ceil=3.0); u = np.where(won[I], S_ * (Pr - 1) * (1 - ded[I]), -S_)
PERS = (("Jan-17Mar", "2026-01-01", "2026-03-18"), ("18Mar-2Jun", "2026-03-18", "2026-06-03"), ("3Jun-8Oct", "2026-06-03", "2026-10-09"), ("9Oct-9Nov", "2026-10-09", "2027-01-01"))
pr_ = np.select([(date[I] >= lo) & (date[I] < hi) for _, lo, hi in PERS], [0, 1, 2, 3], -1)
cnt = collections.Counter(ri[I]); k = np.array([cnt[r] for r in ri[I]])
rn = np.array([int(str(x).rsplit("_", 1)[-1]) if str(x).rsplit("_", 1)[-1].isdigit() else 0 for x in D["race_id"]])[ri[I]]
okop = np.isfinite(o) & (o > 1); book = np.bincount(ri, weights=np.where(okop, 1 / np.where(okop, o, 2), 0), minlength=nR)[ri[I]]
def table(title, groups):
    print(f"\n{title}\n| group | " + " | ".join(p[0] for p in PERS) + " | all: bets, staked, profit, ROI, flat ROI |\n|---|---|---|---|---|---|")
    for lab, m in groups:
        cells = [f"{int((m & (pr_ == j)).sum())} {u[m & (pr_ == j)].sum():+.0f}u {100*u[m & (pr_ == j)].sum()/max(S_[m & (pr_ == j)].sum(),1e-9):+.0f}%" for j in range(4)]
        fl = np.where(won[I[m]], (Pr[m] - 1) * (1 - ded[I[m]]), -1)
        print(f"| {lab} | " + " | ".join(cells) + f" | {int(m.sum())}, {S_[m].sum():.0f}u, {u[m].sum():+.0f}u, {100*u[m].sum()/max(S_[m].sum(),1e-9):+.0f}%, {100*fl.mean():+.0f}% |")
table("OUR BETS IN THE SAME RACE", [("the only bet in its race", k == 1), ("one of two", k == 2), ("one of three", k == 3), ("one of four or more", k >= 4)])
table("RACE NUMBER ON THE CARD", [("races 1-2", rn <= 2), ("races 3-4", (rn >= 3) & (rn <= 4)), ("races 5-6", (rn >= 5) & (rn <= 6)), ("races 7-8", (rn >= 7) & (rn <= 8)), ("race 9+", rn >= 9)])
table("OPENING BOOK OF THE RACE (under 100% = a fifth or more of the market scratched after the open)",
      [("under 90%", book < 0.9), ("90-100%", (book >= 0.9) & (book < 1.0)), ("100-110%", (book >= 1.0) & (book < 1.1)), ("110-125%", (book >= 1.1) & (book < 1.25)), ("125%+", book >= 1.25)])
# races where we bet 3+ runners: does the WHOLE race lose? (profit per race)
by = collections.defaultdict(float)
for r, x in zip(ri[I], u): by[r] += x
for lab, lo, hi in (("1 bet", 1, 1), ("2 bets", 2, 2), ("3+ bets", 3, 99)):
    rs = [r for r in by if lo <= cnt[r] <= hi]; v = np.array([by[r] for r in rs])
    print(f"races with {lab}: {len(rs)} races, {v.sum():+.0f}u, {v.mean():+.2f}u a race, profitable races {100*np.mean(v > 0):.0f}%")
