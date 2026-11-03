"""The favourite-back rule on the LIVE weeks, 14 Oct to 3 Nov 2026 (races the holdout never saw): our price from each
meeting's live model file (the v6.json committed nearest before race day), BSP and finish from the Form King results
exports on the experiments branch. Back the BSP favourite at $4-$7 when ours >= 1.3x (and 1.6x) BSP, flat 1u, 8% comm."""
import glob, json, os, re, subprocess, collections
L = "/home/user/fk-model/data/live_bets"; R = "/tmp/claude-0/-home-user-cafe-copilot/3bac7eba-1a73-583c-b23d-aae29b750b5b/scratchpad/nov/live_res"
nm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
# results: latest export per meeting id
res = {}   # mid -> {(race, name): (finish, bsp)}
for f in sorted(glob.glob(f"{R}/*.md")):
    cur = None; d = {}
    for l in open(f):
        m = re.match(r"## ([\w-]+-\d{8}): ", l)
        if m:
            if cur and d: res[cur] = d
            cur = m.group(1); d = {}; continue
        m = re.match(r"R(\d+)\s+(.+?)\s+finish\s+(\S+)\s+SP\s+(\S+)\s+BSP\s+(\S+)", l.strip())
        if m and cur:
            try: bsp = float(m.group(5))
            except ValueError: bsp = None
            d[(int(m.group(1)), nm(m.group(2)))] = (m.group(3) if m.group(3) != "None" else None, bsp)
    if cur and d: res[cur] = d
# model files: one per meeting, committed nearest before race day (fallback: earliest)
files = collections.defaultdict(list)
for f in glob.glob(f"{L}/2026-1*-v6.json"):
    b = os.path.basename(f); day = b[:10]
    if not ("2026-10-14" <= day <= "2026-11-03"): continue
    track = b[11:].rsplit("-", 2)[0] if b[11:].count("-") >= 2 else b[11:].split("-")[0]
    pre = b[:-8].rsplit("-", 1)[0]; tag = b[:-8].rsplit("-", 1)[1]
    ts = subprocess.run(["git", "log", "-1", "--format=%cI", "--", f], capture_output=True, text=True, cwd="/home/user/fk-model").stdout.strip()
    files[pre].append((ts, tag, f))
rows = []; used = []
for pre, lst in sorted(files.items()):
    day = pre[:10]; track = pre[11:]; mid = f"{track}-{day.replace('-', '')}"
    if mid not in res: print(f"no results for {mid}"); continue
    before = [x for x in lst if x[0][:10] <= day]; ts, tag, f = max(before) if before else min(lst)
    used.append(f"{pre} {tag}")
    v = json.load(open(f)); rr = res[mid]
    by = collections.defaultdict(list)
    for r in v:
        k = (int(r["race"]), nm(r["horse"]))
        if k in rr and rr[k][0] is not None and rr[k][1]: by[int(r["race"])].append((r, rr[k]))
    for rc, ents in by.items():
        tot = sum(r.get("p_model", r["p"]) for r, _ in ents)
        if tot <= 0: continue
        fav_bsp = min(b for _, (_, b) in ents)
        for r, (fin, bsp) in ents:
            ours = tot / r.get("p_model", r["p"])
            rows.append(dict(pre=pre, race=rc, horse=r["horse"], ours=ours, bsp=bsp, won=fin == "1", fav=abs(bsp - fav_bsp) < 1e-9))
print(f"{len(used)} meetings, {len(rows)} runners with a result and BSP, {sum(r['won'] for r in rows)} winners")
for k in (1.3, 1.6):
    g = [r for r in rows if r["fav"] and 4 <= r["bsp"] < 7 and r["ours"] >= k * r["bsp"]]
    ret = sum((1 + (r["bsp"] - 1) * 0.92) if r["won"] else 0 for r in g); exp = sum(1 / r["bsp"] for r in g); w = sum(r["won"] for r in g)
    print(f"\n=== favourite $4-$7, ours >= {k}x: {len(g)} bets, {w} winners (BSP expected {exp:.1f}), staked {len(g)}u, returned {ret:.2f}u, {ret-len(g):+.2f}u ({(100*(ret-len(g))/len(g)) if g else 0:+.0f}%)")
    for r in sorted(g, key=lambda x: x["pre"]):
        print(f"  {r['pre']:<24} R{r['race']:<2} {r['horse']:<22} ours ${r['ours']:5.2f}  BSP ${r['bsp']:5.2f}  {'WON' if r['won'] else 'lost'}")
# the same cells as controls: every $4-$7 favourite, and every favourite
g = [r for r in rows if r["fav"] and 4 <= r["bsp"] < 7]; w = sum(r["won"] for r in g); ret = sum((1 + (r["bsp"] - 1) * 0.92) if r["won"] else 0 for r in g)
print(f"\ncontrol, every $4-$7 favourite: {len(g)} bets, {w} won, {ret-len(g):+.2f}u ({100*(ret-len(g))/len(g):+.0f}%)")
g = [r for r in rows if r["fav"] and 4 <= r["bsp"] < 7 and r["ours"] < 1.3 * r["bsp"]]; w = sum(r["won"] for r in g); ret = sum((1 + (r["bsp"] - 1) * 0.92) if r["won"] else 0 for r in g)
print(f"control, $4-$7 favourites we rate near or shorter than BSP: {len(g)} bets, {w} won, {ret-len(g):+.2f}u ({100*(ret-len(g))/len(g):+.0f}%)")
print("\nmodel files used:", "; ".join(used))
