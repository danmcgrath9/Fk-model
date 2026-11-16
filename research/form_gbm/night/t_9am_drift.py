"""Can we tell which 9am-list horses will drift after 9am? (16 Nov 2026, founder: "is there a way we can tell its going to
drift? Because for instance on saturday, one came in from 9am and the other out")

The live 9am rule (blend_9am.py, TAB's 9am price in the blend): log p = 0.20 log(ours) + 1.00 log(1 / TAB 9am), renormalised
over the race's runners with a price (at least 4), blend price $1.60-$15, first starters out, bet when TAB's 9am price is
at least 1.05x the blend price, stake to win $1,000 ($2,000 at the metro tracks). For every selection over the 17 months
of Betwatch history: TAB's 9am price against TAB's last price before the jump (drift = last / 9am) and against Betfair SP,
and what at 9am might have told us which way it would go:
  pre-9am move   TAB's 9am price / TAB's first price (did it already drift or firm before 9am)
  TAB vs majors  TAB's 9am price / the median of the other majors' 9am prices (TAB the high outlier, or in line)
  our edge       TAB's 9am price / our own price (how far the market sat above us)
  overlay        TAB's 9am price / the blend price (the rule's own margin, 1.05 and up)
  price, time to the jump, metro or country
Each bucket: selections, share that firmed (last <= 0.95 x 9am) and drifted (last >= 1.05 x 9am), median last/9am,
strike rate, and ROI at the 9am price with the live staking (to win a fixed amount). Read only.
    python3.13 t_9am_drift.py BW1.md [BW2.md ...]   (night folder)"""
import csv, io, re, sys
from datetime import datetime
import numpy as np

MAJORS = ("tab", "sportsbet", "ladbrokes", "neds", "pointsbet", "unibet", "betr")
norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
z = np.load("ds/model_ds.npz", allow_pickle=True); P = np.load("p_oof_chal.npy").astype(float)
ri = z["race_idx"]; nR = len(z["race_id"]); rid = z["race_id"].astype(str); date = z["date"].astype(str)[ri]
track = z["track"].astype(str)[ri]; name = z["name"].astype(str)
rno = np.array([int(r.rsplit("_", 1)[1]) for r in rid])[ri]
won = np.asarray(z["finish"], float) == 1; bs = np.asarray(z["bsp"], float)
fs = z["X"][:, list(z["cols"]).index("firstStarter")] == 1
METRO = ("flemington", "caulfield", "moonee valley", "the valley", "sandown")
metro = np.array([any(track[i].lower().startswith(m) for m in METRO) for i in range(len(ri))])
lim = np.where(metro, 2000.0, 1000.0)

bw = {}
f2 = lambda x: float(x) if x not in ("", None) else np.nan
for f in sys.argv[1:]:
    s = open(f).read(); a = s.find("CSV-BEGIN") + 9; b = s.find("CSV-END")
    for r in csv.DictReader(io.StringIO(s[a:b].strip())):
        if r["scratched"] == "1" or not r.get("tab_0900"):
            continue
        maj = {}
        for x in (r.get("bk_0900") or "").split(";"):
            if ":" in x:
                k, v = x.rsplit(":", 1)
                if k in MAJORS[1:] and float(v) > 1: maj[k] = float(v)
        try:
            hrs = (datetime.strptime(r["jump_mel"], "%Y-%m-%d %H:%M") - datetime.strptime(r["date"] + " 09:00", "%Y-%m-%d %H:%M")).total_seconds() / 3600
        except ValueError:
            hrs = np.nan
        bw[(r["date"], int(r["race"]), norm(r["name"]))] = (f2(r["tab_first"]), f2(r["tab_0900"]), f2(r["tab_last"]),
                                                           np.median(list(maj.values())) if maj else np.nan, hrs)
n = len(ri)
first, t9, last, maj9, hrs = (np.full(n, np.nan) for _ in range(5))
for i in range(n):
    v = bw.get((date[i], rno[i], norm(name[i])))
    if v: first[i], t9[i], last[i], maj9[i], hrs[i] = v

ok = np.isfinite(t9) & (t9 > 1) & (P > 0)
cnt = np.bincount(ri, weights=ok, minlength=nR); tp = np.bincount(ri, weights=np.where(ok, P, 0), minlength=nR)
pn = np.where(ok, P / np.maximum(tp[ri], 1e-12), np.nan)
w = np.where(ok, np.exp(0.20 * np.log(np.where(ok, pn, 1)) + 1.00 * np.log(1 / np.where(ok, t9, 2))), 0)
bp = np.where(ok, np.bincount(ri, weights=w, minlength=nR)[ri] / np.maximum(w, 1e-300), np.nan)
sel = ok & (cnt[ri] >= 4) & ~fs & (bp >= 1.6) & (bp <= 15) & (t9 >= 1.05 * bp) & np.isfinite(last) & (last > 1)
drift = last / t9; ours = 1 / pn
stake = lim / (t9 - 1); pl = np.where(won, lim, -stake)
print(f"9am-rule selections with a TAB last price: {int(sel.sum())} ({min(date[sel])} to {max(date[sel])}); "
      f"won {int(won[sel].sum())}; ROI at the 9am price {pl[sel].sum() / stake[sel].sum():+.1%}")
fi, dr = drift <= 0.95, drift >= 1.05
print(f"after 9am: firmed {fi[sel].mean():.0%}, held {(~fi & ~dr)[sel].mean():.0%}, drifted {dr[sel].mean():.0%}; "
      f"median last/9am {np.median(drift[sel]):.2f}; with a Betfair SP: median BSP/9am {np.nanmedian(np.where(bs > 1, bs, np.nan)[sel] / t9[sel]):.2f}")


def table(title, x, edges, labels):
    print(f"\n### {title}\n\n| bucket | bets | firmed | drifted | median last/9am | won | ROI at 9am |\n|---|---|---|---|---|---|---|")
    for lo, hi, lab in zip(edges[:-1], edges[1:], labels):
        m = sel & np.isfinite(x) & (x >= lo) & (x < hi)
        if m.sum() < 5:
            print(f"| {lab} | {int(m.sum())} | | | | | |"); continue
        print(f"| {lab} | {int(m.sum())} | {fi[m].mean():.0%} | {dr[m].mean():.0%} | {np.median(drift[m]):.2f} | "
              f"{won[m].mean():.0%} | {pl[m].sum() / stake[m].sum():+.0%} |")


table("Hindsight: what happened after 9am (not knowable at 9am)", drift, [0, 0.8, 0.95, 1.05, 1.25, 99],
      ["firmed 20%+", "firmed 5-20%", "held", "drifted 5-25%", "drifted 25%+"])
table("Pre-9am move: TAB 9am / TAB's first price", t9 / first, [0, 0.8, 0.95, 1.05, 1.25, 99],
      ["firmed 20%+ before 9am", "firmed 5-20%", "held", "drifted 5-25%", "drifted 25%+ before 9am"])
table("TAB's 9am price / the other majors' median at 9am", t9 / maj9, [0, 0.97, 1.03, 1.10, 99],
      ["TAB under the others", "TAB in line", "TAB 3-10% over", "TAB 10%+ over the others"])
table("Our edge: TAB 9am / our own price", t9 / ours, [0, 1.2, 1.5, 2.0, 99],
      ["market under 1.2x ours", "1.2-1.5x", "1.5-2x", "market 2x+ our price"])
table("Overlay: TAB 9am / the blend price", t9 / bp, [1.05, 1.08, 1.12, 1.20, 99],
      ["1.05-1.08x", "1.08-1.12x", "1.12-1.20x", "1.20x+"])
table("TAB's 9am price", t9, [1, 2.5, 4, 7, 99], ["under $2.50", "$2.50-$4", "$4-$7", "$7+"])
table("Hours from 9am to the jump", hrs, [0, 4, 6, 99], ["under 4 hours", "4-6 hours", "6+ hours"])
table("Metro or country", metro.astype(float), [0, 0.5, 2], ["country", "metro"])

# how much of the drift direction any of it explains: Spearman correlation of each with log(last/9am)
def rank(a):
    o = np.argsort(a); r = np.empty(len(a)); r[o] = np.arange(len(a)); return r
print("\n### Rank correlation with the move after 9am (log last/9am; 0 = no help, +/-1 = perfect)\n")
y = np.log(drift)
for lab, x in (("pre-9am move", np.log(t9 / first)), ("TAB vs majors", np.log(t9 / maj9)), ("our edge", np.log(t9 / ours)),
               ("overlay", np.log(t9 / bp)), ("price", np.log(t9)), ("hours to jump", hrs)):
    m = sel & np.isfinite(x)
    print(f"- {lab}: {np.corrcoef(rank(x[m]), rank(y[m]))[0, 1]:+.2f} ({int(m.sum())} bets)")
