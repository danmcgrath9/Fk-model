"""Wide search for Betfair SP rules, with a luck baseline (10 Nov 2026, founder: "There's got be more things you can test
than that").

Every rule is a BSP price band plus one or two conditions, from: our model (BSP against our price, our rank), the market
(BSP against Form King's open, favourite), the race (field size, metro or not, distance) and the runner (barrier).
Scored on three separate periods: BACKTEST H1 (3 Jun - 31 Jul), H2 (1 Aug - 8 Oct), LIVE (9 Oct on, each meeting's own
live model file). A rule HOLDS if it makes money in all three with 25+ bets in each. 1u, 8% commission, first starters
out.

The luck baseline: in each period, each band's own win rate against BSP (laying or backing EVERY runner in the band) is
taken as "no skill", and every rule is re-run 200 times with winners drawn at that rate. The number of rules that hold
in those draws is how many would hold by luck alone. A rule's own p is how often a draw did as well as it did in all
three periods at once.
    python3.13 t_wide_search.py"""
import collections, json, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import track_rules as T
S = "/tmp/claude-0/-home-user-cafe-copilot/3bac7eba-1a73-583c-b23d-aae29b750b5b/scratchpad/model"
METRO = {"flemington", "caulfield", "caulfieldheath", "mooneevalley", "sandownhillside", "sandownlakeside"}
nm = T.nm
rng = np.random.default_rng(7)

# ---- backtest ------------------------------------------------------------------------------------------------------
z = np.load(f"{S}/ds/model_ds_v10.npz", allow_pickle=True); p10 = np.load(f"{S}/v10_profit_preds.npz")["p10"]
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str)
bs = z["bsp"].astype(float); op = z["open"].astype(float); won = z["finish"] == 1
cols = list(z["cols"]); X = z["X"]; fs = X[:, cols.index("firstStarter")] == 1; bar = X[:, cols.index("barrier")]
ok = np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = ((np.bincount(ri, weights=ok.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (rdate < "2026-10-09")
           & (np.bincount(ri, weights=won.astype(float), minlength=nR) == 1))
m = race_ok[ri]; idx = np.where(m)[0]
s = np.bincount(ri, weights=np.where(m, p10, 0), minlength=nR); ours = s[ri] / np.where(p10 > 0, p10, np.nan)


def ranks(vals, races):
    """rank within race, 1 = lowest value."""
    out = np.zeros(len(vals), int)
    order = np.lexsort((vals, races))
    r_prev, k = None, 0
    for i in order:
        k = k + 1 if races[i] == r_prev else 1; r_prev = races[i]; out[i] = k
    return out


rr_ = ri[idx]
BT = dict(bsp=bs[idx], ours=ours[idx], open=op[idx], won=won[idx], fs=fs[idx], race=rr_,
          field=cnt[rr_], barrier=bar[idx], dist=z["distance"][rr_].astype(float),
          metro=np.array([nm(t) in METRO for t in z["track"][rr_].astype(str)]),
          per=np.where(rdate[rr_] < "2026-08-01", "H1", "H2"))
BT["mrank"] = ranks(BT["ours"], rr_); BT["brank"] = ranks(BT["bsp"], rr_)

# ---- live ----------------------------------------------------------------------------------------------------------
res, mf = T.results(), T.model_files()
L = collections.defaultdict(list); rid = 0
for pre, (ts, tag, f) in sorted(mf.items()):
    mid = f"{pre[11:]}-{pre[:10].replace('-', '')}"
    if mid not in res: continue
    rr, opn = res[mid], T.opens(pre)
    try: fsl = {str(x) for x in json.load(open(f.replace("-v6.json", "-first-starters.json")))}
    except Exception: fsl = set()
    by = collections.defaultdict(list)
    for r in json.load(open(f)):
        k = (int(r["race"]), nm(r["horse"]))
        if k in rr and rr[k][0] is not None and rr[k][1] and rr[k][1] > 1: by[int(r["race"])].append((r, rr[k]))
    track = re.sub(r"[^a-z]", "", pre[11:])
    for rc, ents in by.items():
        tot = sum(r.get("p_model", r["p"]) for r, _ in ents)
        if tot <= 0 or sum(fin == "1" for _, (fin, _) in ents) != 1: continue
        rid += 1
        for r, (fin, b) in ents:
            L["bsp"].append(b); L["ours"].append(tot / r.get("p_model", r["p"])); L["open"].append(opn.get((rc, nm(r["horse"])), np.nan))
            L["won"].append(fin == "1"); L["fs"].append(f"{rc}|{r['horse']}" in fsl); L["race"].append(rid)
            L["field"].append(len(ents)); L["barrier"].append(float(r.get("barrier") or 0)); L["dist"].append(float(r.get("distance") or np.nan))
            L["metro"].append(any(track.startswith(t) for t in METRO))
LV = {k: np.array(v) for k, v in L.items()}; LV["per"] = np.array(["LIVE"] * len(LV["bsp"]))
LV["mrank"] = ranks(LV["ours"], LV["race"]); LV["brank"] = ranks(LV["bsp"], LV["race"])
print(f"backtest {len(BT['bsp'])} runners (H1 {np.sum(BT['per']=='H1')}, H2 {np.sum(BT['per']=='H2')}); live {len(LV['bsp'])} runners "
      f"in {rid} races; live distance known on {np.isfinite(LV['dist']).mean():.0%}, open on {np.isfinite(LV['open']).mean():.0%}")

# ---- the grid -------------------------------------------------------------------------------------------------------
COND = {   # name -> fn(D) -> mask
    "any": lambda D: np.ones(len(D["bsp"]), bool),
    "model likes it (BSP>=1.3x ours)": lambda D: D["bsp"] >= 1.3 * D["ours"],
    "model likes it a lot (BSP>=1.6x ours)": lambda D: D["bsp"] >= 1.6 * D["ours"],
    "model against (BSP<=ours/1.3)": lambda D: D["bsp"] * 1.3 <= D["ours"],
    "model strongly against (BSP<=ours/1.6)": lambda D: D["bsp"] * 1.6 <= D["ours"],
    "our top pick": lambda D: D["mrank"] == 1,
    "our top 3": lambda D: D["mrank"] <= 3,
    "our bottom half": lambda D: D["mrank"] > D["field"] / 2,
    "drifted 1.25x": lambda D: D["bsp"] >= 1.25 * D["open"],
    "drifted 1.5x": lambda D: D["bsp"] >= 1.5 * D["open"],
    "drifted 2x": lambda D: D["bsp"] >= 2 * D["open"],
    "firmed 1.25x": lambda D: D["bsp"] * 1.25 <= D["open"],
    "firmed 1.5x": lambda D: D["bsp"] * 1.5 <= D["open"],
    "BSP favourite": lambda D: D["brank"] == 1,
    "BSP 2nd-3rd pick": lambda D: (D["brank"] >= 2) & (D["brank"] <= 3),
}
CTX = {
    "": lambda D: np.ones(len(D["bsp"]), bool),
    "small field (<=8)": lambda D: D["field"] <= 8,
    "mid field (9-12)": lambda D: (D["field"] >= 9) & (D["field"] <= 12),
    "big field (13+)": lambda D: D["field"] >= 13,
    "metro": lambda D: D["metro"],
    "country/provincial": lambda D: ~D["metro"],
    "sprint (<=1200m)": lambda D: D["dist"] <= 1200,
    "1300-1600m": lambda D: (D["dist"] > 1200) & (D["dist"] <= 1600),
    "1700m+": lambda D: D["dist"] > 1600,
    "inside barrier (1-4)": lambda D: (D["barrier"] >= 1) & (D["barrier"] <= 4),
    "wide barrier (10+)": lambda D: D["barrier"] >= 10,
}
PAIRS = [("model likes it (BSP>=1.3x ours)", "drifted 1.25x"), ("model likes it (BSP>=1.3x ours)", "firmed 1.25x"),
         ("model against (BSP<=ours/1.3)", "drifted 1.25x"), ("model against (BSP<=ours/1.3)", "firmed 1.25x"),
         ("our top pick", "firmed 1.25x"), ("our top pick", "drifted 1.25x"), ("BSP favourite", "model against (BSP<=ours/1.3)"),
         ("BSP favourite", "model likes it (BSP>=1.3x ours)")]
BANDS = {"LAY": ((6, 8), (8, 12), (12, 15), (15, 25), (25, 40), (40, 60)), "BACK": ((1.5, 2.5), (2.5, 4), (4, 7), (7, 12), (12, 20))}

rules = []
for side, bands in BANDS.items():
    for lo, hi in bands:
        for cn in COND:
            for xn in CTX:
                if cn == "any" and xn == "": continue    # the band alone is the baseline
                rules.append((side, lo, hi, cn, xn))
        for a, b in PAIRS:
            rules.append((side, lo, hi, f"{a} + {b}", ""))


def mask(D, side, lo, hi, cn, xn):
    base = ~D["fs"] & (D["bsp"] >= lo) & (D["bsp"] < hi) & CTX[xn](D)
    if " + " in cn:
        a, b = cn.split(" + ")
        return base & np.nan_to_num(COND[a](D), nan=0).astype(bool) & np.nan_to_num(COND[b](D), nan=0).astype(bool)
    return base & np.nan_to_num(COND[cn](D), nan=0).astype(bool)


def pl(b, w, side):
    return np.where(w, -(b - 1), 0.92) if side == "LAY" else np.where(w, (b - 1) * 0.92, -1.0)


PERIODS = (("H1", BT), ("H2", BT), ("LIVE", LV))
# the band baseline: actual winners / BSP-expected for every runner in the band, per period and side
base_ae = {}
for side, bands in BANDS.items():
    for lo, hi in bands:
        for per, D in PERIODS:
            sel = ~D["fs"] & (D["bsp"] >= lo) & (D["bsp"] < hi) & (D["per"] == per)
            base_ae[(lo, hi, per)] = D["won"][sel].sum() / max(np.sum(1 / D["bsp"][sel]), 1e-9)

MIN_N, SIMS = 25, 200
out, sim_holds = [], np.zeros(SIMS)
for side, lo, hi, cn, xn in rules:
    per_stats, sim_pos = [], np.ones(SIMS, bool)
    for per, D in PERIODS:
        sel = mask(D, side, lo, hi, cn, xn) & (D["per"] == per)
        b, w = D["bsp"][sel], D["won"][sel]
        per_stats.append((len(b), int(w.sum()), float(np.sum(1 / b)), float(pl(b, w, side).sum())))
        if len(b) >= MIN_N:
            q = np.clip(base_ae[(lo, hi, per)] / b, 0, 1)
            sw = rng.random((SIMS, len(b))) < q
            sp = np.where(sw, (-(b - 1)) if side == "LAY" else (b - 1) * 0.92, 0.92 if side == "LAY" else -1.0).sum(1)
            sim_pos &= sp > (per_stats[-1][3] if False else 0)
            per_stats[-1] = per_stats[-1] + (float(np.mean(sp >= per_stats[-1][3])),)
    if min(p[0] for p in per_stats) < MIN_N: continue
    sim_holds += sim_pos
    if all(p[3] > 0 for p in per_stats):
        joint = float(np.prod([p[4] for p in per_stats]))   # chance a no-skill draw does this well in all three
        out.append((joint, side, lo, hi, cn, xn, per_stats))
tried = sum(1 for side, lo, hi, cn, xn in rules
            if min(int((mask(D, side, lo, hi, cn, xn) & (D["per"] == per)).sum()) for per, D in PERIODS) >= MIN_N)
print(f"{len(rules)} rules in the grid, {tried} with {MIN_N}+ bets in every period; {len(out)} made money in all three. "
      f"By luck alone: {sim_holds.mean():.0f} (90% of draws {np.percentile(sim_holds, 5):.0f}-{np.percentile(sim_holds, 95):.0f})\n")
print("p = chance a no-skill draw beats it in all three periods at once (smaller is better; with this many rules, under 0.001 is worth a look)")
print("p      side band     rule | H1: bets won (BSP said) units | H2 | LIVE | all")
for joint, side, lo, hi, cn, xn, ps in sorted(out)[:40]:
    n = sum(p[0] for p in ps); wn = sum(p[1] for p in ps); e = sum(p[2] for p in ps); u = sum(p[3] for p in ps)
    cells = " | ".join(f"{p[0]:4d} {p[1]:3d} ({p[2]:5.1f}) {p[3]:+7.2f}u" for p in ps)
    print(f"{joint:.5f} {side:4} ${lo}-${hi:<3} {cn}{' | ' + xn if xn else ''}\n         {cells} | {n} bets {wn} won ({e:.1f}) {u:+.2f}u")
