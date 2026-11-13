"""When to bet, on TAB's own price path from the open to the jump, every month from Jul 2025 (13 Nov 2026, founder: "we
can more properly do all the times up to race start? From odds opening?"). t_minutes.py could only use the months with
Form King flucs; Betwatch (scripts/betwatch_pull.py) holds every TAB price move with its time for every Victorian runner.

The 10 Nov challenger's out-of-fold three-model blend (p_oof_chal.npy), the live rule (edge 1.2, our price $1.60-$15,
minimum 0.95 x the edge price, three steps, the 6x ceiling, first starters out), no deduction, 1u = one unit of the live
stake. The race's open is the first TAB price on any of its runners; a runner's price at a time is its last TAB move at or
before it (blank before its first). Times: minutes after the race's open, 9am Melbourne on race day, minutes before the
jump, and the last price.
  A. THE SAME BETS: decided at TAB's open, struck at the price at that time (the cost of being late).
  B. THE SHEET PLACED THEN: decided and struck at the price at that time.
    python3.13 t_times_betwatch.py [--best] BW1.md [BW2.md ...]   (night folder)
--best: the best price across every bookmaker (--maj: across the major bookmakers only, maj_path) at each moment (best_path) instead of TAB's own path (13 Nov 2026,
founder: "I think it gives more than tab?"); the open is then the first price from any bookmaker."""
import bisect, collections, csv, datetime as dt, io, re, sys
import numpy as np
import stake_rule

norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
z = np.load("ds/model_ds.npz", allow_pickle=True); P = np.load("p_oof_chal.npy").astype(float)
ri = z["race_idx"]; nR = len(z["race_id"]); rid = z["race_id"].astype(str); date = z["date"].astype(str)[ri]
name = z["name"].astype(str); rno = np.array([int(r.rsplit("_", 1)[1]) for r in rid])[ri]
won = np.asarray(z["finish"], float) == 1; fsr = z["X"][:, list(z["cols"]).index("firstStarter")] == 1
qq = 1 / np.maximum(P, 1e-9); mo = 0.95 * (1.2 / np.maximum(P, 1e-9) ** 0.82) ** (1 / 0.78)
CEIL, TIERS = 6.0, (1.0, 1.25, 1.5)
T = lambda s: dt.datetime.strptime(s, "%Y-%m-%d %H:%M")

BEST = "--best" in sys.argv or "--maj" in sys.argv
PC, FC = ("maj_path", "maj_first_mel") if "--maj" in sys.argv else ("best_path", "best_first_mel") if BEST else ("path", "tab_first_mel")
paths, race_open, jump = {}, {}, {}
for f in [a for a in sys.argv[1:] if not a.startswith("--")]:
    s = open(f).read(); a = s.find("CSV-BEGIN") + 9; b = s.find("CSV-END")
    for r in csv.DictReader(io.StringIO(s[a:b].strip())):
        if r["scratched"] == "1" or not r.get(PC): continue
        t0 = T(r[FC])
        pts = [(t0 + dt.timedelta(minutes=float(x.split(":")[0])), float(x.split(":")[1])) for x in r[PC].split(";")]
        k = (r["date"], int(r["race"]), norm(r["name"])); paths[k] = pts
        rk = (r["date"], int(r["race"]))
        race_open[rk] = min(race_open.get(rk, t0), t0)
        if r["jump_mel"]: jump[rk] = T(r["jump_mel"])


def price_at(i, when):
    pts = paths.get((date[i], rno[i], norm(name[i])))
    if not pts or when is None: return np.nan
    j = bisect.bisect_right([p[0] for p in pts], when) - 1
    return pts[j][1] if j >= 0 else np.nan


have = np.array([(date[i], rno[i], norm(name[i])) in paths for i in range(len(ri))])
rk_of = [(date[i], rno[i]) for i in range(len(ri))]
race_has = collections.Counter(ri[have]); race_size = np.bincount(ri, minlength=nR)
full = np.array([race_has.get(r, 0) >= 0.8 * race_size[r] for r in range(nR)])   # races where we matched most runners
base = have & full[ri] & ~fsr & (P > 0) & (qq >= 1.6) & (qq <= 15)
print(f"{len(paths)} {PC} price paths; dataset runners matched {int(have.sum())} of {len(ri)}; "
      f"races used {int(full.sum())} of {nR}; {min(date[base]) if base.any() else "-"} to {max(date[base]) if base.any() else "-"}")


def stake(i, price):
    ts = [mo[i] * k for k in TIERS if mo[i] * k < CEIL * qq[i]]; tot = prev = 0.0
    for k, t in enumerate(ts):
        tp = ts[k + 1] if k + 1 < len(ts) else t
        s_ = stake_rule.stake(P[i] ** 0.82 * tp ** -0.22, tp); add = max(0.0, s_ - prev); prev = max(prev, s_)
        if price >= t: tot += add
    return tot


def at(fn):
    return np.array([price_at(i, fn(i)) if base[i] else np.nan for i in range(len(ri))])


opn = at(lambda i: race_open.get(rk_of[i]) + dt.timedelta(seconds=1) if rk_of[i] in race_open else None)
openA = [(i, stake(i, opn[i])) for i in np.where(base & np.isfinite(opn) & (opn >= mo) & (opn < CEIL * qq))[0]]
openA = [(i, s) for i, s in openA if s > 0]
BLOCKS = (("2025", "2025-07-01", "2026-01-01"), ("2026", "2026-01-01", "2027-01-01"))


def score(bets, strike):
    out = collections.defaultdict(lambda: [0, 0.0, 0.0])
    for i, st in bets:
        if not np.isfinite(strike[i]): continue
        pl = st * (strike[i] - 1) if won[i] else -st
        for lab, lo, hi in (("all", "0", "9"),) + BLOCKS:
            if lo <= date[i] < hi: c = out[lab]; c[0] += 1; c[1] += st; c[2] += pl
    return out


TIMES = [("the open", lambda i: race_open.get(rk_of[i], None) and race_open[rk_of[i]] + dt.timedelta(seconds=1))]
for m in (1, 2, 5, 10, 15, 30, 60, 120, 240, 480, 720, 1440, 2880):
    TIMES.append((f"{m} min after the open" if m < 60 else f"{m // 60} h after the open",
                  (lambda m: lambda i: race_open.get(rk_of[i]) and race_open[rk_of[i]] + dt.timedelta(minutes=m))(m)))
TIMES.append(("9am race day", lambda i: dt.datetime.fromisoformat(date[i]).replace(hour=9)))
for m in (60, 30, 10, 5, 1):
    TIMES.append((f"{m} min before the jump", (lambda m: lambda i: jump.get(rk_of[i]) and jump[rk_of[i]] - dt.timedelta(minutes=m))(m)))
TIMES.append(("the last price", lambda i: jump.get(rk_of[i]) and jump[rk_of[i]] + dt.timedelta(minutes=5)))

print("\n| when | A: same bets | staked | profit | ROI | A 2025 | A 2026 | B: sheet then: bets | profit | ROI | B 2025 | B 2026 |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
for lab, fn in TIMES:
    px = at(fn)
    A = score(openA, px)
    Bb = [(i, stake(i, px[i])) for i in np.where(base & np.isfinite(px) & (px >= mo) & (px < CEIL * qq))[0]]
    B = score([(i, s) for i, s in Bb if s > 0], px)
    f = lambda c: f"{c[2] / c[1]:+.0%}" if c[1] else "-"
    print(f"| {lab} | {A['all'][0]} | {A['all'][1]:.0f}u | {A['all'][2]:+.0f}u | {f(A['all'])} | {f(A['2025'])} | {f(A['2026'])} | "
          f"{B['all'][0]} | {B['all'][2]:+.0f}u | {f(B['all'])} | {f(B['2025'])} | {f(B['2026'])} |")
print("\nmonths (A at the open):")
for mo_ in sorted(set(d[:7] for d in date[base])):
    c = [0, 0.0, 0.0]
    for i, st in openA:
        if date[i].startswith(mo_): c[0] += 1; c[1] += st; c[2] += st * (opn[i] - 1) if won[i] else -st
    if c[0]: print(f"  {mo_}: {c[0]} bets, {c[2]:+.0f}u on {c[1]:.0f}u ({c[2] / c[1]:+.0%})")
