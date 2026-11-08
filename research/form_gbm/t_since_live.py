"""SINCE LIVE, 9 Oct - 8 Nov (8 Nov 2026, founder: "Why can't you just look at results from 9 October and tell me?"): t_bsp_candidates_live.py from 9 Oct. (8 Nov 2026, founder: "Are there any other lay strategies or bsp strategies") Candidate BSP strategies from the research, checked
on the live weeks 14 Oct - 8 Nov. Built from t_fav47_live.py: the favourite-back rule on the LIVE weeks, 14 Oct to 3 Nov 2026 (races the holdout never saw): our price from each
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

# the week of 2-8 Nov is in data/live_bets/*-results.txt (meeting_results.py output without the ## header)
for f in glob.glob(f"{L}/2026-11-0*-results.txt"):
    if "founder" in f or "partial" in f: continue
    b = os.path.basename(f)[:-12]; day = b[:10]; mid = f"{b[11:]}-{day.replace('-', '')}"
    d = {}
    for l in open(f):
        m = re.match(r"R(\d+)\s+(.+?)\s+finish\s+(\S+)\s+SP\s+(\S+)\s+BSP\s+(\S+)", l.strip())
        if m:
            try: bsp = float(m.group(5))
            except ValueError: bsp = None
            d[(int(m.group(1)), nm(m.group(2)))] = (m.group(3) if m.group(3) != "None" else None, bsp)
    if d: res[mid] = d
# model files: one per meeting, committed nearest before race day (fallback: earliest)
files = collections.defaultdict(list)
for f in glob.glob(f"{L}/2026-1*-v6.json"):
    b = os.path.basename(f); day = b[:10]
    if not ("2026-10-09" <= day <= "2026-11-08"): continue
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
    try: fs = {str(x) for x in json.load(open(f.replace("-v6.json", "-first-starters.json")))}
    except Exception: fs = set()
    by = collections.defaultdict(list)
    for r in v:
        k = (int(r["race"]), nm(r["horse"]))
        if k in rr and rr[k][0] is not None and rr[k][1] and rr[k][1] > 1: by[int(r["race"])].append((r, rr[k]))
    for rc, ents in by.items():
        tot = sum(r.get("p_model", r["p"]) for r, _ in ents)
        if tot <= 0 or not any(fin == "1" for _, (fin, _) in ents): continue
        fav_bsp = min(b for _, (_, b) in ents); top = min(tot / r.get("p_model", r["p"]) for r, _ in ents)
        for r, (fin, bsp) in ents:
            ours = tot / r.get("p_model", r["p"])
            rows.append(dict(pre=pre, race=rc, horse=r["horse"], ours=ours, bsp=bsp, won=fin == "1", fav=abs(bsp - fav_bsp) < 1e-9,
                             top=abs(ours - top) < 1e-9, fs=f"{rc}|{r['horse']}" in fs))
print(f"{len(used)} meetings, {len(rows)} runners with a result and BSP, {sum(r['won'] for r in rows)} winners\n")
def lay(g):
    pl = sum(-(r["bsp"] - 1) if r["won"] else 0.92 for r in g); w = sum(r["won"] for r in g); exp = sum(1 / r["bsp"] for r in g)
    return f"{len(g):4d} lays {w:3d} won (BSP said {exp:5.1f})  {pl:+7.2f}u  ({100*pl/len(g) if g else 0:+.0f}% on stake)  ${pl*200:+,.0f} at $200"
def back(g):
    pl = sum((r["bsp"] - 1) * 0.92 if r["won"] else -1 for r in g); w = sum(r["won"] for r in g); exp = sum(1 / r["bsp"] for r in g)
    return f"{len(g):4d} backs {w:3d} won (BSP said {exp:5.1f})  {pl:+7.2f}u  ({100*pl/len(g) if g else 0:+.0f}%)"
print("LAYS at BSP, BSP >= 1.6x ours, first starters out (1u, 8% commission)")
for lo, hi in ((8, 12), (12, 15), (15, 40), (40, 50), (50, 100), (8, 50)):
    g = [r for r in rows if not r["fs"] and lo <= r["bsp"] < hi and r["bsp"] >= 1.6 * r["ours"]]
    print(f"  ${lo}-${hi:<4} {lay(g)}")
print("  (the same bands with NO model, every runner: the plain longshot bias)")
for lo, hi in ((8, 15), (15, 40)):
    g = [r for r in rows if not r["fs"] and lo <= r["bsp"] < hi]
    print(f"  ${lo}-${hi:<4} {lay(g)}")
print("\nBACKS at BSP")
g = [r for r in rows if r["top"] and r["bsp"] >= r["ours"] and 1.6 <= r["ours"]]
print(f"  our top pick, BSP >= our price          {back(g)}")
for lo, hi in ((1.6, 3), (3, 5), (5, 8)):
    print(f"     top pick, ours ${lo}-${hi:<4}               {back([r for r in g if lo <= r['ours'] < hi])}")
g = [r for r in rows if r["fav"] and 4 <= r["bsp"] < 7 and r["ours"] >= 1.6 * r["bsp"]]
print(f"  $4-$7 favourite, ours >= 1.6x (live rule) {back(g)}")
g = [r for r in rows if r["fav"] and 4 <= r["bsp"] < 7 and r["ours"] >= 1.3 * r["bsp"]]
print(f"  $4-$7 favourite, ours >= 1.3x            {back(g)}")
print("\nmodel files used:", "; ".join(used))
