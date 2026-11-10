"""BACK rules only, the same three-period test as t_both_samples.py (10 Nov 2026, founder: "Are there any backing
strategies"). Backs at BSP, 1u, 8% commission on a winner; a rule holds only if it makes money in backtest H1, H2 and
live with 25+ bets in each. Conditions: the band alone, the BSP favourite, our top pick, model value (BSP >= x ours),
model against (BSP <= ours / x), market moves from Form King's open, and model + market together."""
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
top_o = np.full(nR, np.inf); np.minimum.at(top_o, ri[m], ours[m])
BT = dict(bsp=bs[m], ours=ours[m], open=op[m], won=won[m], fs=fs[m], fav=np.isclose(bs[m], fav_b[ri[m]]), top=np.isclose(ours[m], top_o[ri[m]]),
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
          won=np.array([r["won"] for r in rows]), fs=np.array([r["fs"] for r in rows]), fav=np.array([r["fav"] for r in rows]), top=np.array([r["top"] for r in rows]),
          per=np.array(["LIVE"] * len(rows)))
print(f"backtest: {m.sum()} runners in {race_ok.sum()} races (H1 {np.sum(BT['per']=='H1')}, H2 {np.sum(BT['per']=='H2')}); "
      f"live: {len(rows)} runners, opening price on {np.isfinite(LV['open']).mean():.0%}\n")

def score(D, sel, side):
    b, w = D["bsp"][sel], D["won"][sel]
    pl = np.where(w, -(b - 1), 0.92) if side == "LAY" else np.where(w, (b - 1) * 0.92, -1.0)
    return int(sel.sum()), int(w.sum()), float(np.sum(1 / b)), float(pl.sum())

BANDS = ((1.5, 2.5), (2.5, 4), (4, 7), (7, 12), (12, 20))
rules = []
for lo, hi in BANDS:
    band = lambda D, lo=lo, hi=hi: ~D["fs"] & (D["bsp"] >= lo) & (D["bsp"] < hi)
    fo = lambda D, y: D["bsp"] * y <= D["open"]
    rules += [("BACK", (lo, hi), "every runner", band),
              ("BACK", (lo, hi), "BSP favourite", lambda D, b=band: b(D) & D["fav"]),
              ("BACK", (lo, hi), "our top pick", lambda D, b=band: b(D) & D["top"]),
              ("BACK", (lo, hi), "top pick, firmed 1.25x", lambda D, b=band: b(D) & D["top"] & fo(D, 1.25)),
              ("BACK", (lo, hi), "firmed 1.25x from open", lambda D, b=band: b(D) & fo(D, 1.25)),
              ("BACK", (lo, hi), "firmed 1.5x from open", lambda D, b=band: b(D) & fo(D, 1.5)),
              ("BACK", (lo, hi), "drifted 1.25x from open", lambda D, b=band: b(D) & (D["bsp"] >= 1.25 * D["open"]))]
    for x in (1.2, 1.5, 2.0):
        rules += [("BACK", (lo, hi), f"BSP >= {x}x ours", lambda D, b=band, x=x: b(D) & (D["bsp"] >= x * D["ours"])),
                  ("BACK", (lo, hi), f"BSP >= {x}x ours, firmed 1.25x", lambda D, b=band, x=x: b(D) & (D["bsp"] >= x * D["ours"]) & fo(D, 1.25))]
    for x in (1.3, 1.6):
        rules += [("BACK", (lo, hi), f"BSP <= ours/{x}", lambda D, b=band, x=x: b(D) & (D["bsp"] * x <= D["ours"])),
                  ("BACK", (lo, hi), f"fav, BSP <= ours/{x}", lambda D, b=band, x=x: b(D) & D["fav"] & (D["bsp"] * x <= D["ours"]))]

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
