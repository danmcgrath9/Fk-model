"""This week, every runner: how close are our prices to Betfair SP, and who picked winners better?
python wk_vs_bsp.py RESULTS_TXT   (meetings from fwd_test.MEETINGS). Log loss on the winner (lower = better), and KL(BSP||ours)."""
import json, math, re, sys, collections, os
sys.argv += ["/dev/null"]
src = open(os.path.join(os.path.dirname(__file__), "fwd_test.py")).read()
MEETINGS = eval(src[src.index("MEETINGS = [") + 11: src.index("]\nnorm") + 1])
L = os.path.join(os.path.dirname(__file__), "../../data/live_bets")
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
res, cur = {}, None
for l in open(sys.argv[1]):
    m = re.match(r"## (\S+):", l)
    if m: cur = m.group(1); continue
    m = re.match(r"R(\d+) (.+?)\s+finish (\S+)\s+SP (\S+)\s+BSP (\S+)", l)
    if m and cur and m.group(3) != "None" and m.group(5) != "None":
        res[(cur, int(m.group(1)), norm(m.group(2)))] = (int(m.group(3)), float(m.group(5)))
T = collections.Counter(); print("| Meeting | Races | Log loss ours | Log loss BSP | Log loss opening | KL(BSP, ours) | Our top pick won | BSP fav won |"); print("|---|---|---|---|---|---|---|---|")
for label, mid, pre, prices in MEETINGS:
    op = {}
    for l in open(f"{L}/{prices}"):
        pa = [x.strip() for x in l.split("#")[0].split(",")]
        if len(pa) >= 3 and pa[0].isdigit():
            try: op[(int(pa[0]), norm(pa[1]))] = float(pa[2])
            except ValueError: pass
    by = collections.defaultdict(list)
    for r in json.load(open(f"{L}/{pre}-v6.json")):
        k = (mid, r["race"], norm(r["horse"]))
        if k in res: by[r["race"]].append((r["p"], res[k][1], res[k][0], op.get((r["race"], norm(r["horse"])))))
    c = collections.Counter()
    for rn, rs in by.items():
        if not any(f == 1 for _, _, f, _ in rs) or len(rs) < 4: continue
        sp = sum(p for p, *_ in rs); sb = sum(1 / b for _, b, *_ in rs)
        po = [1 / o if o else None for *_, o in rs]; so = sum(x for x in po if x) if all(po) else None
        w = [i for i, x in enumerate(rs) if x[2] == 1][0]
        c["n"] += 1; c["ours"] -= math.log(rs[w][0] / sp); c["bsp"] -= math.log((1 / rs[w][1]) / sb)
        if so: c["op_n"] += 1; c["op"] -= math.log(po[w] / so); c["ours_op"] -= math.log(rs[w][0] / sp)
        c["kl"] += sum((1 / b / sb) * math.log((1 / b / sb) / (p / sp)) for p, b, *_ in rs)
        c["top"] += max(range(len(rs)), key=lambda i: rs[i][0]) == w; c["fav"] += min(range(len(rs)), key=lambda i: rs[i][1]) == w
    if not c["n"]: continue
    T.update(c); n = c["n"]
    print(f"| {label} | {n} | {c['ours']/n:.3f} | {c['bsp']/n:.3f} | {c['op']/c['op_n'] if c['op_n'] else float('nan'):.3f} ({c['op_n']}) | {c['kl']/n:.3f} | {c['top']}/{n} | {c['fav']}/{n} |")
n = T["n"]
print(f"| **Week** | **{n}** | **{T['ours']/n:.3f}** | **{T['bsp']/n:.3f}** | **{T['op']/T['op_n']:.3f}** ({T['op_n']}; ours on the same races {T['ours_op']/T['op_n']:.3f}) | **{T['kl']/n:.3f}** | **{T['top']}/{n}** | **{T['fav']}/{n}** |")
