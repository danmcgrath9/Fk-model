"""Blend our price with the opening market (12 Oct 2026, t_blend_open.py): p = normalise(exp(0.82 log ours + 0.22 log open)),
per race. The weights are the BSP-fitted cross-fit on the holdout (0.815 / 0.225, rounded); the gain was KL to BSP
0.0801 -> 0.0765 and a price that is calibrated on its own bets. The open is the fifth field of the prices file
("fk_open 8.50", Form King's average opening price); a runner with no open keeps its model price and the race is
renormalised. The model price is kept as p_model. python blend_open.py MODEL_JSON PRICES_TXT"""
import json, math, re, sys, collections
W_OURS, W_OPEN = 0.82, 0.22
mj, pt = sys.argv[1:3]
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
op = {}
for l in open(pt):
    pa = [x.strip() for x in l.split("#")[0].split(",")]
    if len(pa) >= 5 and pa[0].isdigit():
        m = re.search(r"([\d.]+)\s*$", pa[4])
        if m:
            try:
                v = float(m.group(1))
                if v > 1: op[(int(pa[0]), norm(pa[1]))] = v
            except ValueError: pass
rows = json.load(open(mj))
by = collections.defaultdict(list)
for r in rows: by[r["race_id"]].append(r)
n_bl = 0
for rid, rs in by.items():
    for r in rs:
        r.setdefault("p_model", r["p"])
        o = op.get((r["race"], norm(r["horse"])))
        if o:
            r["p"] = math.exp(W_OURS * math.log(max(r["p_model"], 1e-9)) + W_OPEN * math.log(1 / o)); r["open_used"] = o; n_bl += 1
        else:
            r["p"] = r["p_model"]
    s = sum(r["p"] for r in rs)
    for r in rs: r["p"] = r["p"] / s
json.dump(rows, open(mj, "w"), indent=1)
print(f"blended {n_bl} of {len(rows)} runners with the open ({W_OURS} ours, {W_OPEN} open); every race renormalised to 100%")
