"""The 9am rule with every major bookmaker's own 9am price (13 Nov 2026, founder: "I think it gives more than tab?").
t_9am_betwatch.py tests the rule on TAB's 9am price alone; live, the list is bet with every bookie that is at or above the
take price ("we can get on for $1,000 - $2,000 win with all bookies"). Betwatch's pull (scripts/betwatch_pull.py) keeps
each bookmaker's last price at or before 9:00am Melbourne on race day (bk_0900).

The rule as it runs live (blend_9am.py): log p = 0.20 log(ours) + 1.00 log(1 / market 9am price), renormalised over the
race's runners with a price (at least 4), blend price $1.60-$15, first starters out, take at or above 1.05x the blend
price. The market price in the blend is shown two ways: TAB's 9am price, and the median of the majors' 9am prices.
Bets, each sized to win $1,000 ($2,000 at Flemington, Caulfield, Moonee Valley and Sandown):
  TAB only         one bet at TAB's 9am price when it is at or above the take price
  every major      one bet with EACH major bookmaker whose 9am price is at or above the take price, at its own price
  best major       one bet at the best major price, when it is at or above the take price
Majors: TAB, Sportsbet, Ladbrokes, Neds, PointsBet, Unibet, Betr (the small bookies hold the best price often but will
not take $1,000). Runners matched to the dataset by date, race number and name.
    python3.13 t_9am_bookies.py BW1.md [BW2.md ...]   (night folder)"""
import collections, csv, io, re, sys
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
lim = np.array([2000.0 if any(track[i].lower().startswith(m) for m in METRO) else 1000.0 for i in range(len(ri))])

bk9 = {}
for f in sys.argv[1:]:
    s = open(f).read(); a = s.find("CSV-BEGIN") + 9; b = s.find("CSV-END")
    for r in csv.DictReader(io.StringIO(s[a:b].strip())):
        if r["scratched"] == "1" or not r.get("bk_0900"): continue
        d = {}
        for x in r["bk_0900"].split(";"):
            if ":" in x:
                k, v = x.rsplit(":", 1)
                if k in MAJORS and float(v) > 1: d[k] = float(v)
        if d: bk9[(r["date"], int(r["race"]), norm(r["name"]))] = d
B = np.full((len(ri), len(MAJORS)), np.nan)
for i in range(len(ri)):
    d = bk9.get((date[i], rno[i], norm(name[i])))
    if d:
        for j, k in enumerate(MAJORS):
            if k in d: B[i, j] = d[k]
have = np.isfinite(B).any(1)
print(f"{len(bk9)} Betwatch runners with a major's 9am price; matched {int(have.sum())} of {len(ri)} dataset runners; "
      f"{min(date[have]) if have.any() else '-'} to {max(date[have]) if have.any() else '-'}")
print("9am prices held, by bookmaker: " + ", ".join(f"{k} {int(np.isfinite(B[:, j]).sum())}" for j, k in enumerate(MAJORS)))


def blend(mkt):
    ok = np.isfinite(mkt) & (mkt > 1) & (P > 0)
    cnt = np.bincount(ri, weights=ok, minlength=nR)
    tp = np.bincount(ri, weights=np.where(ok, P, 0), minlength=nR)
    w = np.where(ok, np.exp(0.20 * np.log(np.where(ok, P, 1) / np.maximum(tp[ri], 1e-12)) + 1.00 * np.log(1 / np.where(ok, mkt, 2))), 0)
    sw = np.bincount(ri, weights=w, minlength=nR)
    bp = np.where(ok, sw[ri] / np.maximum(w, 1e-300), np.nan)
    return ok & (cnt[ri] >= 4) & ~fs & (bp >= 1.6) & (bp <= 15), bp


PERIODS = (("2025-07-01", "2025-11-01", "Jul-Oct 2025"), ("2025-11-01", "2026-03-01", "Nov 2025-Feb 2026"),
           ("2026-03-01", "2026-07-01", "Mar-Jun 2026"), ("2026-07-01", "2026-09-01", "Jul-Aug 2026"),
           ("2026-09-01", "2026-12-01", "Sep-Nov 2026"), ("0", "9", "**All**"))


def report(title, mkt):
    elig, bp = blend(mkt); take = 1.05 * bp
    tab = B[:, 0]; best = np.nanmax(np.where(np.isfinite(B), B, -1), 1); best[best < 0] = np.nan
    hit = elig[:, None] & np.isfinite(B) & (B >= take[:, None])            # (runner, bookie) bets
    st_b = np.where(hit, lim[:, None] / (B - 1), 0); pl_b = np.where(hit, np.where(won[:, None], lim[:, None], -st_b), 0)
    t_ok = elig & np.isfinite(tab) & (tab >= take); b_ok = elig & np.isfinite(best) & (best >= take)
    st_t = np.where(t_ok, lim / (tab - 1), 0); pl_t = np.where(t_ok, np.where(won, lim, -st_t), 0)
    st_x = np.where(b_ok, lim / (best - 1), 0); pl_x = np.where(b_ok, np.where(won, lim, -st_x), 0)
    print(f"\n### {title}\n")
    print("| period | TAB only: bets | profit | ROI | every major: runners | bookie bets | staked | profit | ROI | best major: bets | profit | ROI | same runners at BSP |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for lo, hi, lab in PERIODS:
        m = (date >= lo) & (date < hi); r_any = m & hit.any(1); fb = r_any & np.isfinite(bs) & (bs > 1)
        f = lambda pl, st: f"{pl / st:+.0%}" if st else "-"
        print(f"| {lab} | {int((m & t_ok).sum())} | ${pl_t[m].sum():+,.0f} | {f(pl_t[m].sum(), st_t[m].sum())} | "
              f"{int(r_any.sum())} | {int(hit[m].sum())} | ${st_b[m].sum():,.0f} | ${pl_b[m].sum():+,.0f} | {f(pl_b[m].sum(), st_b[m].sum())} | "
              f"{int((m & b_ok).sum())} | ${pl_x[m].sum():+,.0f} | {f(pl_x[m].sum(), st_x[m].sum())} | "
              f"{np.where(won[fb], (bs[fb] - 1) * 0.92, -1).mean():+.0%} |" if fb.any() else
              f"| {lab} | {int((m & t_ok).sum())} | | | 0 | | | | | | | | |")
    print("\n| bookmaker | bets | won | profit | ROI | median price |\n|---|---|---|---|---|---|")
    for j, k in enumerate(MAJORS):
        h = hit[:, j]
        if h.any(): print(f"| {k} | {int(h.sum())} | {int(won[h].sum())} | ${pl_b[h, j].sum():+,.0f} | {pl_b[h, j].sum() / st_b[h, j].sum():+.0%} | ${np.median(B[h, j]):.2f} |")
    mos = sorted(set(d[:7] for d in date[hit.any(1)]))
    print("\n| month | every major: bookie bets | profit | best major: bets | profit |\n|---|---|---|---|---|")
    for mo in mos:
        m = np.char.startswith(date, mo)
        print(f"| {mo} | {int(hit[m].sum())} | ${pl_b[m].sum():+,.0f} | {int((m & b_ok).sum())} | ${pl_x[m].sum():+,.0f} |")
    print(f"\nmonths in profit, every major: {sum(pl_b[np.char.startswith(date, mo)].sum() > 0 for mo in mos)} of {len(mos)}")


report("Market price in the blend = TAB's 9am price", B[:, 0])
med = np.nanmedian(np.where(np.isfinite(B), B, np.nan), 1) if have.any() else np.full(len(ri), np.nan)
report("Market price in the blend = the median of the majors' 9am prices", med)
