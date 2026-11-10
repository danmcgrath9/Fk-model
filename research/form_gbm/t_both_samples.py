"""Rules that hold on BOTH the backtest and the live weeks (10 Nov 2026, founder: "it's too small a sample, it still may
work, what works on the back test and the live test as well, so research on that").

Three periods, each scored on its own: BACKTEST H1 (v10 holdout, 3 Jun - 31 Jul), BACKTEST H2 (1 Aug - 8 Oct; the
holdout's last days overlap the live weeks and are cut), LIVE (9 Oct - 9 Nov, each meeting's live model file, Form King
BSP, finish and opening price, as t_lay_check_live.py). A fixed grid of simple rules, written down before looking:
LAYS and BACKS at BSP by BSP band, conditioned on the model (BSP vs our price), on the market (BSP vs the opening price,
a drift or a firm), or on nothing (the band alone). 1u, 8% commission. A rule "holds" only if it makes money in all
three periods with at least 25 bets in each. Printed: every rule that holds, and how many held out of how many tried,
against the number that would hold by luck (each period a coin flip: 1 in 8).
    python3.13 t_both_samples.py   (needs the scratchpad model dataset and the live files)"""
import collections, glob, json, os, re, subprocess, sys
import numpy as np
S = "/tmp/claude-0/-home-user-cafe-copilot/3bac7eba-1a73-583c-b23d-aae29b750b5b/scratchpad/model"
L = "/home/user/fk-model/data/live_bets"
nm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())

# ---- backtest rows ---------------------------------------------------------------------------------------------
z = np.load(f"{S}/ds/model_ds_v10.npz", allow_pickle=True); p10 = np.load(f"{S}/v10_profit_preds.npz")["p10"]
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
bs = z["bsp"].astype(float); op = z["open"].astype(float); won = z["finish"] == 1
cols = list(z["cols"]); fs = z["X"][:, cols.index("firstStarter")] == 1
ok = np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = ((np.bincount(ri, weights=ok.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (rdate < "2026-10-09")
           & (np.bincount(ri, weights=won.astype(float), minlength=nR) == 1))
m = race_ok[ri]; s = np.bincount(ri, weights=np.where(m, p10, 0), minlength=nR)
ours = np.where(m, s[ri] / np.where(p10 > 0, p10, np.nan), np.nan)
fav_b = np.full(nR, np.inf); np.minimum.at(fav_b, ri[m], bs[m])
BT = dict(bsp=bs[m], ours=ours[m], open=op[m], won=won[m], fs=fs[m], fav=np.isclose(bs[m], fav_b[ri[m]]),
          per=np.where(date[m] < "2026-08-01", "H1", "H2"))

# ---- live rows (as t_lay_check_live.py) plus the opening price from each meeting's prices file ----------------------
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "t_lay_check_live.py")).read()
ns = {}; exec(src.split("import math")[0].split('"""', 2)[2], ns)
rows = ns["rows"]
opens = {}
for pre in {r["pre"] for r in rows}:
    f = f"{L}/{pre}-prices.txt"
    if not os.path.exists(f): continue
    for l in open(f):
        pa = [x.strip() for x in l.split("#")[0].split(",")]
        mo = re.search(r"fk_open\s+([\d.]+)", l)
        if len(pa) >= 3 and pa[0].isdigit() and mo: opens[(pre, int(pa[0]), nm(pa[1]))] = float(mo.group(1))
LV = dict(bsp=np.array([r["bsp"] for r in rows]), ours=np.array([r["ours"] for r in rows]),
          open=np.array([opens.get((r["pre"], r["race"], nm(r["horse"])), np.nan) for r in rows]),
          won=np.array([r["won"] for r in rows]), fs=np.array([r["fs"] for r in rows]), fav=np.array([r["fav"] for r in rows]),
          per=np.array(["LIVE"] * len(rows)))
print(f"backtest: {m.sum()} runners in {race_ok.sum()} races (H1 {np.sum(BT['per']=='H1')}, H2 {np.sum(BT['per']=='H2')}); "
      f"live: {len(rows)} runners, opening price on {np.isfinite(LV['open']).mean():.0%}\n")

def score(D, sel, side):
    b, w = D["bsp"][sel], D["won"][sel]
    pl = np.where(w, -(b - 1), 0.92) if side == "LAY" else np.where(w, (b - 1) * 0.92, -1.0)
    return int(sel.sum()), int(w.sum()), float(np.sum(1 / b)), float(pl.sum())

LAY_BANDS = ((8, 12), (12, 15), (15, 25), (25, 40), (40, 60))
BACK_BANDS = ((1.5, 3), (3, 5), (5, 8), (8, 15))
rules = []   # (side, band, label, fn(D) -> mask)
for lo, hi in LAY_BANDS:
    band = lambda D, lo=lo, hi=hi: ~D["fs"] & (D["bsp"] >= lo) & (D["bsp"] < hi)
    rules.append(("LAY", (lo, hi), "every runner", band))
    for x in (1.3, 1.6, 2.0):
        rules.append(("LAY", (lo, hi), f"BSP >= {x}x ours", lambda D, b=band, x=x: b(D) & (D["bsp"] >= x * D["ours"])))
        rules.append(("LAY", (lo, hi), f"BSP <= ours/{x}", lambda D, b=band, x=x: b(D) & (D["bsp"] * x <= D["ours"])))
    for y in (1.25, 1.5, 2.0):
        rules.append(("LAY", (lo, hi), f"drifted {y}x from open", lambda D, b=band, y=y: b(D) & (D["bsp"] >= y * D["open"])))
        rules.append(("LAY", (lo, hi), f"firmed {y}x from open", lambda D, b=band, y=y: b(D) & (D["bsp"] * y <= D["open"])))
for lo, hi in BACK_BANDS:
    band = lambda D, lo=lo, hi=hi: ~D["fs"] & (D["bsp"] >= lo) & (D["bsp"] < hi)
    rules.append(("BACK", (lo, hi), "every runner", band))
    rules.append(("BACK", (lo, hi), "BSP favourite", lambda D, b=band: b(D) & D["fav"]))
    for x in (1.2, 1.5, 2.0):
        rules.append(("BACK", (lo, hi), f"BSP >= {x}x ours", lambda D, b=band, x=x: b(D) & (D["bsp"] >= x * D["ours"])))
        rules.append(("BACK", (lo, hi), f"fav, BSP >= {x}x ours", lambda D, b=band, x=x: b(D) & D["fav"] & (D["bsp"] >= x * D["ours"])))
    for y in (1.25, 1.5):
        rules.append(("BACK", (lo, hi), f"firmed {y}x from open", lambda D, b=band, y=y: b(D) & (D["bsp"] * y <= D["open"])))
        rules.append(("BACK", (lo, hi), f"drifted {y}x from open", lambda D, b=band, y=y: b(D) & (D["bsp"] >= y * D["open"])))

MIN_N = 25
held, tried = [], 0
for side, (lo, hi), label, fn in rules:
    out = {}
    for per, D in (("H1", BT), ("H2", BT), ("LIVE", LV)):
        sel = fn(D) & (D["per"] == per)
        out[per] = score(D, sel, side)
    if min(o[0] for o in out.values()) < MIN_N: continue
    tried += 1
    if all(o[3] > 0 for o in out.values()): held.append((side, lo, hi, label, out))
print(f"{tried} rules with {MIN_N}+ bets in every period; {len(held)} made money in all three (luck alone: about {tried/8:.0f})\n")
print("side  band      rule                       | H1: bets won (BSP said) units | H2: ... | LIVE: ...")
for side, lo, hi, label, out in sorted(held, key=lambda h: -h[4]["LIVE"][3]):
    cells = " | ".join(f"{n:4d} {w:3d} ({e:5.1f}) {p:+7.2f}u" for n, w, e, p in out.values())
    print(f"{side:4}  ${lo}-${hi:<4}  {label:26} | {cells}")
