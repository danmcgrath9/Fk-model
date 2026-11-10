"""Is the lay backtest holding up live? (10 Nov 2026, founder: "Are we sure about this backtest on the lays? It's not really working from what we've seen"). The live rows as t_since_live.py builds them (each meeting's live model file, Form King BSP and finish), 9 Oct - 9 Nov, against the v10 holdout (t_lay_trigger.py): winners vs BSP-expected (A/E), profit, by trigger slice, and how likely the live winners are if the backtest edge were real."""
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
    if not ("2026-10-09" <= day <= "2026-11-09"): continue
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
import math
def poi_ge(k, lam):   # P(X >= k), X ~ Poisson(lam)
    return 1 - sum(math.exp(-lam) * lam ** i / math.factorial(i) for i in range(k))
def line(g):
    n = len(g); w = sum(r["won"] for r in g); e = sum(1 / r["bsp"] for r in g)
    pl = sum(-(r["bsp"] - 1) if r["won"] else 0.92 for r in g)
    return n, w, e, pl
BACKTEST = {(15, 40, 1.5): (933, 19, 38.9, 405.01), (8, 12, 1.6): (164, 8, 16.3, 72.46)}
for lo, hi, x in ((15, 40, 1.5), (8, 12, 1.6)):
    g = [r for r in rows if not r["fs"] and lo <= r["bsp"] <= hi and r["bsp"] >= x * r["ours"]]
    n, w, e, pl = line(g); bn, bw, be, bpl = BACKTEST[(lo, hi, x)]
    print(f"${lo}-${hi} at {x}x   LIVE {n} lays, {w} won, BSP said {e:.1f}, A/E {w/e:.2f}, {pl:+.2f}u ({100*pl/n:+.0f}% on stake)")
    print(f"{'':16}BACKTEST {bn} lays, {bw} won, BSP said {be:.1f}, A/E {bw/be:.2f}, {bpl:+.2f}u ({100*bpl/bn:+.0f}%)")
    lam = e * bw / be
    print(f"{'':16}if the backtest edge were real, live winners expected {lam:.1f}; P({w} or more) = {poi_ge(w, lam):.3f}")
    # break-even A/E for these prices: EV = sum((1-p)*0.92 - p*(b-1)) = 0 with p = k/b
    a = sum(0.92 for r in g); bsum = sum((0.92 + r['bsp'] - 1) / r['bsp'] for r in g)
    print(f"{'':16}break-even A/E at these prices {a/bsum:.2f}\n")
print("By trigger slice, LIVE ($15-$40):")
xs = (1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 2.0, 2.5, 99)
for a_, b_ in zip(xs, xs[1:]):
    g = [r for r in rows if not r["fs"] and 15 <= r["bsp"] <= 40 and a_ * r["ours"] <= r["bsp"] < b_ * r["ours"]]
    n, w, e, pl = line(g)
    if n: print(f"  {a_}-{b_ if b_ < 99 else '+'}  {n:4d} lays {w:3d} won (BSP said {e:5.1f})  A/E {w/e if e else 0:.2f}  {pl:+7.2f}u")
g = [r for r in rows if not r["fs"] and 15 <= r["bsp"] <= 40]
n, w, e, pl = line(g); print(f"  every runner $15-$40 (no model): {n} lays {w} won (BSP said {e:.1f}) A/E {w/e:.2f} {pl:+.2f}u")
