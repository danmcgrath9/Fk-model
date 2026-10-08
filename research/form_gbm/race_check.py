"""One race against the prices file with the live rules. python race_check.py DAYPREFIX GOING RACE"""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stake_rule
pre, g, race = sys.argv[1], sys.argv[2], int(sys.argv[3])
THR = 0.2   # metro 40c+ tried 7 Oct and reverted: no extra profit at the open (t_tracks.py)
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
M = [r for r in json.load(open(f"{pre}-{g}-v6.json")) if r["race"] == race]
fu = json.load(open(f"{pre}-{g}-first-up-blocks.json")); ang = json.load(open(f"{pre}-{g}-angles.json")); fs = set(json.load(open(f"{pre}-{g}-first-starters.json")))
pr = {}; scr = set()
for l in open(f"{pre}-prices.txt"):
    pa = [x.strip() for x in l.split(",")]
    if pa[0].isdigit() and int(pa[0]) == race:
        if pa[2] == "SCR": scr.add(norm(pa[1]))
        else: pr[norm(pa[1])] = float(pa[2])
M = [r for r in M if norm(r["horse"]) not in scr]; t = sum(r["p"] for r in M)
fsb = any(f"{race}|{r['horse']}" in fs and pr.get(norm(r["horse"]), 99) <= 6 for r in M)
for r in sorted(M, key=lambda r: -r["p"]):
    pp = r["p"] / t; o = pr.get(norm(r["horse"])); k = f"{race}|{r['horse']}"; f = fu.get(k, ""); early = f.startswith("EARLY")
    why = []
    if o is None: why.append("no price")
    else:
        v = pp * o - 1
        if k in fs: why.append("first starter")
        if fsb: why.append("first starter at $6 or shorter in race")
        if f and not early: why.append("no bet: " + f[:50])
        if early and o > 8: why.append("early only, over $8")
        if not 1.6 <= 1 / pp <= 15: why.append("our price outside $1.60-$15")
        if o >= 3 / pp: why.append("open 3x ours")
        if v < THR: why.append(f"value {v*100:+.0f}%")
    st = 0
    if o and not why:
        st = stake_rule.stake(pp, o, r.get("only_ride", False), len(M))
    print(f"{r['horse']:20s} ours ${1/pp:7.2f}  best ${o}  " + (f"BET {st}u, take at ${(1+THR)/pp:.2f}+ " if st else "") + ("; ".join(why)) + ("  [" + "; ".join(ang.get(k, [])) + "]" if st else ""))
