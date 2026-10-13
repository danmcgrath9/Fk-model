"""Bet at the open, then top up after scratchings (14 Oct 2026, founder: "Bet at opening. Adjust our market after
scratchings and we can top up bets. Can you do a back test on that").

Stage 1, at the open: the BetMatic orders (pre-open minimum odds, 5% shade, 8 price steps sized at the next step;
betmatic_orders.py), filled where the open is at or over the minimum; winnings take the scratching deduction.
Stage 2, after scratchings: our market re-priced on the final field (the blend with every starter's open, renormalised),
and every bet that was value at the open is topped up to the full sheet stake at the later price, IF that later price
is still at or over the take-at (1.2 / our chance); a value-at-open bet the orders missed is struck in full the same
way. No deduction on stage 2 (struck after the scratchings).

A: holdout and older races, later price = Betfair SP less 8% commission (the only later price the dataset holds;
   sharp, so this is the hard case).
B: the live timed sample (82 races 3-11 Oct, live model prices), later price = the corporate fluc 6 hours before the
   jump (race morning, after scratchings), stage 1 with the race's measured deduction (15.9c where not measured).
Caveat both ways: the datasets hold the final fields only, so stage 1's pre-open chance is computed without the
runners later scratched (slightly too generous), and the open is Form King's average open."""
import numpy as np, collections, csv, json, math, re, sys
import stake_rule
STEPS = (1, 1.1, 1.2, 1.3, 1.45, 1.6, 1.8, 2.0)


def ladder(pm, op, only, fld, cap):
    """Stake the 8-step orders fill at opening price op (0 if the open is under the minimum)."""
    mo = 0.95 * (1.2 / pm ** 0.82) ** (1 / 0.78); ts = [mo * s for s in STEPS if mo * s < cap]
    tot = prev = 0.0
    for k, t in enumerate(ts):
        tp = ts[k + 1] if k + 1 < len(ts) else t
        s = stake_rule.stake(pm ** 0.82 * tp ** -0.22, tp, only, fld); add = max(0.0, s - prev); prev = max(prev, s)
        if op >= t: tot += add
    return tot


def run(rows, label):
    """rows: dicts with pm (model chance), pb (blend with the open, final field), op (open), p2 (later price, net of
    commission where it applies), won, ded (stage-1 deduction), only, fld."""
    S = collections.defaultdict(lambda: [0, 0.0, 0.0])
    def add(k, st, price, won, d):
        if st <= 0: return
        S[k][0] += 1; S[k][1] += st; S[k][2] += st * (price - 1) * (1 - d) if won else -st
    for r in rows:
        pm, pb, op, p2 = r["pm"], r["pb"], r["op"], r["p2"]
        ours_b = 1 / pb
        sheet = 1.6 <= ours_b <= 15 and op >= 1.2 * ours_b and op < 3 * ours_b
        if sheet: add("sheet at the open (exact, final field)", stake_rule.stake(pb, op, r["only"], r["fld"]), op, r["won"], r["ded"])
        s1 = ladder(pm, op, r["only"], r["fld"], 3 / pm) if 1.6 <= 1 / pm <= 15 and op < 3 / pm else 0.0
        add("stage 1 only: orders at the open", s1, op, r["won"], r["ded"])
        add("stage 1 + 2: orders, then top-up", s1, op, r["won"], r["ded"])
        if sheet and p2 and p2 >= 1.2 * ours_b:
            full = stake_rule.stake(pb, p2, r["only"], r["fld"]); top = max(0.0, full - s1)
            add("stage 1 + 2: orders, then top-up", top, p2, r["won"], 0.0)
            add("  (stage 2 slice on its own)", top, p2, r["won"], 0.0)
    print(f"\n{label}\n| method | bets | staked (u) | profit (u) | staked ROI |\n|---|---|---|---|---|")
    for k in ("sheet at the open (exact, final field)", "stage 1 only: orders at the open", "stage 1 + 2: orders, then top-up", "  (stage 2 slice on its own)"):
        n, st, pl = S[k]; print(f"| {k} | {n} | {st:.0f} | {pl:+.0f} | {100 * pl / st if st else 0:+.1f}% |")


def part_a():
    import bench as b
    D = b.load(); ri = D["race_idx"]; nR = D["n_races"]; z = np.load("blend_hold.npz")
    o = np.asarray(D["open"], float); bs = np.asarray(D["bsp"], float); won = np.asarray(D["finish"], float) == 1
    okp = np.isfinite(o) & (o > 1); fld = np.bincount(ri, minlength=nR)[ri]; race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0
    track = D["track"][ri].astype(str); meet = np.char.add(track, np.char.add("|", D["date"][ri].astype(str))); jk = D["jockey"].astype(str)
    cnt = collections.Counter(zip(meet, jk)); only = np.array([cnt[(m, x)] == 1 for m, x in zip(meet, jk)])
    def norm(v):
        s = np.bincount(ri, weights=v, minlength=nR); return v / np.where(s[ri] > 0, s[ri], 1)
    def blend(p):
        v = np.where(okp, np.exp(0.82 * np.log(np.maximum(p, 1e-9)) + 0.22 * np.log(1 / np.where(okp, o, 2))), 0); return np.where(race_ok[ri], norm(v), 0)
    old, new = b.split(0.7); hold_r = np.zeros(nR, bool); hold_r[np.where(new)[0] if new.dtype == bool else list(new)] = True
    for name, pm, ins in (("HOLD", z["p2"], hold_r[ri]), ("OLD", norm(np.load("p_oof_blend9.npy")), ~hold_r[ri])):
        pb = blend(pm); base = ins & race_ok[ri] & np.isfinite(bs) & (pm > 0) & (pb > 0)
        rows = [dict(pm=pm[i], pb=pb[i], op=o[i], p2=1 + (bs[i] - 1) * 0.92, won=won[i], ded=0.159, only=only[i], fld=fld[i]) for i in np.where(base)[0]]
        run(rows, f"A. {name}: later price = Betfair SP less 8% commission; stage 1 deduction 15.9c (the measured average)")


def part_b(timing, live, files):
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower()); f = lambda v: float(v) if v not in ("", None) else None
    T = list(csv.DictReader(open(timing))); pm = {}
    for fn in files.values():
        for r in json.load(open(f"{live}/{fn}")): pm[(r["race_id"], r["horse_id"])] = r.get("p_model", r["p"])
    by = collections.defaultdict(list)
    for t in T:
        k = (t["race_id"], t["horse_id"])
        if k in pm and f(t["open"]) and t["finish"]: by[t["race_id"]].append((t, pm[k]))
    rows = []
    for rid, rs in by.items():
        w = [math.exp(0.82 * math.log(p) + 0.22 * math.log(1 / f(t["open"]))) for t, p in rs]; s = sum(w)
        for (t, p), x in zip(rs, w):
            rows.append(dict(pm=p, pb=x / s, op=f(t["open"]), p2=f(t["b6"]), won=t["finish"] == "1", ded=0.159, only=False, fld=len(rs)))
    run(rows, f"B. live timed sample ({len(by)} races): later price = corporate fluc 6h before the jump; stage 1 deduction 15.9c")


if __name__ == "__main__":
    part_a()
    if len(sys.argv) > 1:
        S = sys.argv[1]
        part_b(f"{S}/timing2.csv", "/home/user/fk-model/data/live_bets", {
            "PAKS": "2026-10-05-pakenham-v6.json", "MILD": "2026-10-06-mildura-v6.json", "GEEL": "2026-10-07-geelong-v6.json",
            "KYNE": "2026-10-08-kyneton-g4-v6.json", "BRAT": "2026-10-09-ballarat-g4-v6.json", "CRAN": "2026-10-09-cranbourne-g4-v6.json",
            "CAUL": "2026-10-10-caulfield-g4-v6.json", "SEYM": "2026-10-11-seymour-g4-v6.json"})
