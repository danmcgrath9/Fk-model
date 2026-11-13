"""The 9am rule over every month, with TAB's 9am prices from Betwatch (13 Nov 2026). Form King's stored flucs have no
timed prices for Nov 2025 - Aug 2026, so the first test of the rule (58 bets, +53%) only had the months either side.
Betwatch's current API holds TAB's flucs with timestamps for every Victorian runner (scripts/betwatch_pull.py).

The rule exactly as it runs live (blend_9am.py): the 10 Nov challenger's out-of-fold price (p_oof_chal.npy) mixed with
TAB's 9am price, log p = 0.20 log(ours) + 1.00 log(1 / 9am price), renormalised over the race's runners with a 9am price
(at least 4 of them); a runner whose 9am price is at least 1.05x the blend's price, blend price $1.60-$15, first starters
out, is a bet. Each bet is sized to win $1,000 a bookie ($2,000 at Flemington, Caulfield, Moonee Valley and Sandown) at
the 9am price: a winner returns the to-win amount, a loser costs the stake. Also shown at 1u flat and at BSP.
Runners are matched to the dataset by date, race number and name.
    python3.13 t_9am_betwatch.py BW1.md [BW2.md ...]   (night folder)"""
import collections, csv, io, re, sys
import numpy as np

norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
z = np.load("ds/model_ds.npz", allow_pickle=True); P = np.load("p_oof_chal.npy").astype(float)
ri = z["race_idx"]; nR = len(z["race_id"]); rid = z["race_id"].astype(str); date = z["date"].astype(str)[ri]
track = z["track"].astype(str)[ri]; name = z["name"].astype(str)
rno = np.array([int(r.rsplit("_", 1)[1]) for r in rid])[ri]
won = np.asarray(z["finish"], float) == 1; bs = np.asarray(z["bsp"], float)
fs = z["X"][:, list(z["cols"]).index("firstStarter")] == 1
METRO = ("flemington", "caulfield", "moonee valley", "the valley", "sandown")

bw = {}
for f in sys.argv[1:]:
    s = open(f).read(); a = s.find("CSV-BEGIN") + 9; b = s.find("CSV-END")
    for r in csv.DictReader(io.StringIO(s[a:b].strip())):
        if r["scratched"] == "1" or not r["tab_0900"]: continue
        bw[(r["date"], int(r["race"]), norm(r["name"]))] = float(r["tab_0900"])
p9 = np.array([bw.get((date[i], rno[i], norm(name[i])), np.nan) for i in range(len(ri))])
print(f"{len(bw)} Betwatch runners with a 9am TAB price; matched {int(np.isfinite(p9).sum())} of {len(ri)} dataset runners "
      f"({min(date)} to {max(date)})")

# the blend, per race, over the runners with a 9am price
ok = np.isfinite(p9) & (p9 > 1) & (P > 0)
cnt = np.bincount(ri, weights=ok, minlength=nR)
tp = np.bincount(ri, weights=np.where(ok, P, 0), minlength=nR)
w = np.where(ok, np.exp(0.20 * np.log(np.where(ok, P, 1) / np.maximum(tp[ri], 1e-12)) + 1.00 * np.log(1 / np.where(ok, p9, 2))), 0)
sw = np.bincount(ri, weights=w, minlength=nR)
blend_price = np.where(ok, sw[ri] / np.maximum(w, 1e-300), np.nan)
bet = ok & (cnt[ri] >= 4) & ~fs & (blend_price >= 1.6) & (blend_price <= 15) & (p9 >= 1.05 * blend_price)
lim = np.array([2000.0 if any(track[i].lower().startswith(m) for m in METRO) else 1000.0 for i in range(len(ri))])
stake = lim / (p9 - 1)
mbl = np.where(won, lim, -stake)
flat = np.where(won, p9 - 1, -1.0)
atb = np.where(won, (bs - 1) * 0.92, -1.0)


def row(lab, m):
    m = m & bet; n = int(m.sum())
    if not n: print(f"| {lab} | 0 | | | | | | |"); return
    st = stake[m].sum(); pr = mbl[m].sum(); fb = m & np.isfinite(bs) & (bs > 1)
    print(f"| {lab} | {n} | {int(won[m].sum())} | ${np.median(p9[m]):.2f} | ${st:,.0f} | ${pr:+,.0f} | {pr / st:+.0%} | "
          f"{flat[m].mean():+.0%} | {atb[fb].mean():+.0%} |")


print("\n| period | bets | won | median 9am price | staked a bookie | profit a bookie | ROI | 1u flat | same bets at BSP |")
print("|---|---|---|---|---|---|---|---|---|")
for lo, hi, lab in (("2025-07-01", "2025-11-01", "Jul-Oct 2025 (timed before)"), ("2025-11-01", "2026-03-01", "Nov 2025-Feb 2026 (the gap)"),
                    ("2026-03-01", "2026-07-01", "Mar-Jun 2026 (the gap)"), ("2026-07-01", "2026-09-01", "Jul-Aug 2026 (the gap)"),
                    ("2026-09-01", "2026-12-01", "Sep-Nov 2026 (timed before)")):
    row(lab, (date >= lo) & (date < hi))
row("**All**", np.ones(len(ri), bool))
row("the gap only (Nov 2025-Aug 2026)", (date >= "2025-11-01") & (date < "2026-09-01"))
print("\n| month | bets | won | profit a bookie |\n|---|---|---|---|")
for mo in sorted(set(d[:7] for d in date)):
    m = bet & np.char.startswith(date, mo)
    if m.any(): print(f"| {mo} | {int(m.sum())} | {int(won[m].sum())} | ${mbl[m].sum():+,.0f} |")
print(f"\nmonths in profit: {sum(mbl[bet & np.char.startswith(date, mo)].sum() > 0 for mo in sorted(set(d[:7] for d in date)) if (bet & np.char.startswith(date, mo)).any())} of "
      f"{sum((bet & np.char.startswith(date, mo)).any() for mo in sorted(set(d[:7] for d in date)))}")
print(f"race days with a 9am price: {len(set(date[ok]))}; bets a race day: {bet.sum() / max(len(set(date[ok])), 1):.2f}")
