"""When to bet: the open book settled at every minute after the market opens (12 Nov 2026, founder: "test all the minutes
from July then?"). The 10 Nov challenger's out-of-fold three-model blend (p_oof_chal.npy, 1 Jul 2025 - 9 Nov 2026), the
live rule (edge 1.2, our price $1.60-$15, minimum 0.95 x the edge price, three steps, the 6x ceiling from 12 Nov, first
starters out), on every race with timed flucs (scripts/fluc_minutes.py output, about 1,670 races: Jul-Oct 2025 and
Sep-Nov 2026). No deduction, 1u = one unit of the live stake.
  A. THE SAME BETS: decided at the open, struck at the price m minutes later (the cost of being late).
  B. THE SHEET PLACED AT m: decided and struck at the price m minutes after the open (what a late sheet would take).
    python3.13 t_minutes.py FLUC_MINUTES.md   (night folder)"""
import csv, io, sys
import numpy as np
import stake_rule

z = np.load("ds/model_ds.npz", allow_pickle=True); P = np.load("p_oof_chal.npy").astype(float)
ri = z["race_idx"]; nR = len(z["race_id"]); date = z["date"].astype(str)[ri]; rid = z["race_id"].astype(str)[ri]
hid = z["horse_id"].astype(str); won = np.asarray(z["finish"], float) == 1
o = np.asarray(z["open"], float); fsr = z["X"][:, list(z["cols"]).index("firstStarter")] == 1
okp = np.isfinite(o) & (o > 1); race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0
s = open(sys.argv[1]).read(); a = s.find("CSV-BEGIN") + 9; b = s.find("CSV-END")
rows = list(csv.DictReader(io.StringIO(s[a:b].strip())))
cols = [c for c in rows[0].keys() if c.startswith("m")] + ["jump"]
key = {(r["race_id"], r["horse_id"]): r for r in rows}
idx = np.array([key.get((rid[i], hid[i])) is not None for i in range(len(ri))])
timed_races = set(ri[idx])
M = {c: np.array([float(key[(rid[i], hid[i])][c]) if idx[i] and key[(rid[i], hid[i])][c] else np.nan for i in range(len(ri))]) for c in cols}
base = idx & race_ok[ri] & ~fsr & (P > 0) & np.isin(ri, list(timed_races))
qq = 1 / np.maximum(P, 1e-9); mo = 0.95 * (1.2 / np.maximum(P, 1e-9) ** 0.82) ** (1 / 0.78)
CEIL, TIERS = 6.0, (1.0, 1.25, 1.5)
BLOCKS = (("Jul-Oct 2025", "2025-07-01", "2026-01-01"), ("Sep-Nov 2026", "2026-01-01", "2027-01-01"))


def stake(i, price):
    ts = [mo[i] * k for k in TIERS if mo[i] * k < CEIL * qq[i]]; tot = prev = 0.0
    for k, t in enumerate(ts):
        tp = ts[k + 1] if k + 1 < len(ts) else t
        s_ = stake_rule.stake(P[i] ** 0.82 * tp ** -0.22, tp); add = max(0.0, s_ - prev); prev = max(prev, s_)
        if price >= t: tot += add
    return tot


def book(decide, strike):
    out = []
    for i in np.where(base & (qq >= 1.6) & (qq <= 15) & np.isfinite(decide) & (decide >= mo) & (decide < CEIL * qq) & np.isfinite(strike))[0]:
        st = stake(i, decide[i])
        if st > 0: out.append((i, st, st * (strike[i] - 1) if won[i] else -st))
    return out


def cell(B, lo="0", hi="9"):
    B = [x for x in B if lo <= date[x[0]] < hi]
    st = sum(x[1] for x in B); pl = sum(x[2] for x in B)
    return len(B), st, pl


print(f"{len(timed_races)} races with timed flucs in the blend's months; "
      f"{int(base.sum())} runners priced\n")
print("| minutes after the open | A: same bets, profit | ROI | B: sheet placed then: bets | staked | profit | ROI | "
      + " | ".join(f"B {n} ROI" for n, _, _ in BLOCKS) + " |")
print("|---|---|---|---|---|---|---|" + "---|" * len(BLOCKS))
openB = book(o, o)
for c in cols:
    A = [(i, st, st * (M[c][i] - 1) if won[i] else -st) for i, st, _ in openB if np.isfinite(M[c][i])]
    na, sa, pa = cell(A); B = book(M[c], M[c]); nb, sb, pb = cell(B)
    blk = [cell(B, lo, hi) for _, lo, hi in BLOCKS]
    lab = "the jump (last price)" if c == "jump" else c[1:]
    print(f"| {lab} | {pa:+.0f}u | {pa / max(sa, 1e-9):+.0%} | {nb} | {sb:.0f}u | {pb:+.0f}u | {pb / max(sb, 1e-9):+.0%} | "
          + " | ".join(f"{p / max(st_, 1e-9):+.0%}" for _, st_, p in blk) + " |")
no, so, po = cell(openB)
print(f"\nAt Form King's open (the dataset's open): {no} bets, {so:.0f}u staked, {po:+.0f}u ({po / max(so, 1e-9):+.0%}).")
