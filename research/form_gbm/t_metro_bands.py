"""Metro backtest by unit band and by weekday (1 Nov 2026, founder: "look at the amount of bets by unit bands and their ROI
and does metro also include wednesdays?"). v10 holdout from 3 Jun; metro = Flemington, Caulfield, Moonee Valley, Sandown,
every meeting at those tracks whatever the day. Metro fix stakes at full size (the live sheet halves them)."""
import numpy as np, collections, datetime as dt
pm_cur = None
exec(open("t_metro_fix.py").read().split("H1 = ")[0])
_t = open("t_metro_orders.py").read()
exec("C, W = 0.986, 0.8\ndef run2(" + _t.split("def run2(")[1].split("pm_cur = pm0")[0])
base = lambda t: t.replace(" Synthetic","").replace(" Hillside","").replace(" Lakeside","").replace(" Heath","").replace(" Park","").strip()
def table(r, key, order=None, title=""):
    g = collections.defaultdict(lambda: [0, 0.0, 0.0, 0])
    for i, s in r:
        k = key(i, s); a = g[k]; a[0] += 1; a[1] += s; a[2] += s * ((o[i] - 1) * 0.93 if won[i] else -1); a[3] += int(won[i])
    print(title)
    for k in (order or sorted(g)):
        if k in g: n, st, pl, w = g[k]; print(f"  {k:22s} {n:4d} bets {w:3d} won  {st:6.1f}u  {pl:+7.1f}u  {100*pl/st:+6.1f}%")
for lab, r in (("METRO FIX (live)", run2(metro, False)), ("METRO, NO FIX (as before 31 Oct)", run(pm0, metro))):
    bands = [(0, .5, "under 0.5u"), (.5, 1, "0.5-1u"), (1, 2, "1-2u"), (2, 3, "2-3u"), (3, 5, "3-5u"), (5, 99, "5u+")]
    bk = lambda i, s: next(b[2] for b in bands if b[0] <= s < b[1])
    print(f"\n{lab}, stake band at full stake (live sheet halves: 1-2u full = 0.5-1u bet)")
    table(r, bk, [b[2] for b in bands])
    table(r, lambda i, s: dt.date.fromisoformat(rdate[ri[i]]).strftime("%a"), ["Sat", "Wed", "Fri", "Thu", "Tue", "Sun", "Mon"], " by weekday")
    table(r, lambda i, s: base(trk[ri[i]]), title=" by track")
days = collections.Counter(dt.date.fromisoformat(d).strftime("%a") for d in set(zip(*[rdate[ri[metro & m]]]))[0] if False) if False else None
mt = sorted({(rdate[r], base(trk[r])) for r in np.unique(ri[metro & m])})
print("\nmetro meetings in the holdout by weekday:", collections.Counter(dt.date.fromisoformat(d).strftime("%a") for d, _ in mt))
