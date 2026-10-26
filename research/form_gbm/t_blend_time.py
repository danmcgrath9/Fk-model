"""Benter blend weights by time after the open (27 Oct 2026, founder: "Why don't you just test?").
chance = ours^a x market^b, renormalised per race; (a, b) fitted by max conditional log-likelihood of the winner on the
DESIGN races (to 13 Oct), scored on the CHECK races (14-26 Oct), at the open and 30/45/60/90 min after it. Market =
1/average price normalised per race. Then the 30-90 min check re-run with each time's own weights.
python3.13 t_blend_time.py ../fw_all.md"""
import sys
src = open("t_window_strat.py").read().split('W = ("m30"')[0]
exec(src)
import numpy as np
T = ("open", "m30", "m45", "m60", "m90")
def race_arrays(c, period):
    out = []
    by = collections.defaultdict(list)
    for x in rows: by[x["race"]].append(x)
    for k, xs in by.items():
        d = xs[0]["date"]
        if (period == "design") != (d <= "2026-10-13"): continue
        pr = np.array([x[c] for x in xs])
        if not np.all(np.isfinite(pr)) or np.any(pr <= 1): continue
        q = (1 / pr) / (1 / pr).sum(); p = np.array([x["p"] for x in xs]); w = np.array([x["won"] for x in xs])
        if w.sum() != 1: continue
        out.append((np.log(p), np.log(q), int(np.argmax(w))))
    return out
def ll(a, b, R):
    s = 0.0
    for lp, lq, wi in R:
        v = a * lp + b * lq; v -= v.max(); s += v[wi] - np.log(np.exp(v).sum())
    return -s / len(R)
grid_a = np.arange(0.0, 1.31, 0.05); grid_b = np.arange(0.0, 1.31, 0.05)
W = {}
print("| when | design races | fitted ours a | market b | b/(a+b) | check log loss: fitted | live 0.82/0.22 | ours alone | market alone |\n|---|---|---|---|---|---|---|---|---|")
for c in T:
    D = race_arrays(c, "design"); C = race_arrays(c, "check")
    best = min(((ll(a, b, D), a, b) for a in grid_a for b in grid_b), key=lambda t: t[0])
    _, a, b = best; W[c] = (a, b)
    print(f"| {c} | {len(D)} | {a:.2f} | {b:.2f} | {b/(a+b):.0%} | {ll(a,b,C):.4f} | {ll(0.82,0.22,C):.4f} | {ll(1,0,C):.4f} | {ll(0,1,C):.4f} |")
print(f"(check races at the open: {len(race_arrays('open','check'))}; lower log loss = better)")
# bets with each time's blend, normalised per race: value = blended chance x price >= E
def blend_bets(cols, wts, E_new=1.3, period="all", held=None, E_held=(1.15, 1.2)):
    by = collections.defaultdict(list)
    for x in rows: by[x["race"]].append(x)
    out = []
    for k, xs in by.items():
        d = xs[0]["date"]
        if period != "all" and (period == "design") != (d <= "2026-10-13"): continue
        done = set()
        for c in cols:
            pr = np.array([x[c] for x in xs])
            if not np.all(np.isfinite(pr)) or np.any(pr <= 1): continue
            a, b = wts[c]; q = (1 / pr) / (1 / pr).sum(); p = np.array([x["p"] for x in xs])
            v = p ** a * q ** b; v /= v.sum()
            for j, x in enumerate(xs):
                if j in done: continue
                t = pr[j]; mine = held is not None and id(x) in held
                if held is not None and not mine and False: pass
                if t / x["open"] >= 1.2 or not (1.6 <= 1 / x["p"] <= 15) or t >= 3 / x["p"]: continue
                E = (E_held[0] if t < 4 else E_held[1]) if mine else E_new
                if v[j] * t >= E:
                    s = stake_rule.stake(v[j], t); done.add(j)
                    if s > 0: out.append((x, t, s, c, mine))
    return out
O = bets("open", period="all"); took = {id(b[0]) for b in O}
Wc = ("m30", "m45", "m60", "m90")
live = {c: (0.82, 0.22) for c in T}
print("\n" + H)
for period in ("design", "check", "all"):
    for lab, wts in (("live weights 0.82/0.22", live), ("refit weights by time", W)):
        Bb = blend_bets(Wc, wts, period=period, held=took)
        print(summary([(x, t, s, c) for x, t, s, c, m in Bb], f"{period}: 30-90 min, {lab}, all"))
        print(summary([(x, t, s, c) for x, t, s, c, m in Bb if not m], f"{period}: 30-90 min, {lab}, NEW horses only"))
