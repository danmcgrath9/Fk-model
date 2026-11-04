"""Since going live (Fri 9 Oct to Wed 4 Nov 2026): what the lay rule and the favourite-back rule would have taken, from each
meeting's live model file (the v6.json committed nearest before race day) and Form King's results and BSPs. Lays: BSP $15-$40
and >= 1.6x ours, first starters out, 1u at BSP, 8% commission; for 28 Oct onward the paper lay sheets as settled are used
instead. Backs: the BSP favourite at $4-$7 when ours >= 1.6x BSP, first starters out, 1u at BSP, 8% commission."""
import glob, json, os, re, subprocess, collections
L = "/home/user/fk-model/data/live_bets"; R = "/tmp/claude-0/-home-user-cafe-copilot/3bac7eba-1a73-583c-b23d-aae29b750b5b/scratchpad/nov/live_res"
nm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
res = {}
def load(path, mid=None):
    cur = mid; d = {}
    for l in open(path):
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
for f in sorted(glob.glob(f"{R}/*.md")): load(f)
load(f"{L}/2026-11-04-kyneton-results.txt", "kyneton-20261104")
files = collections.defaultdict(list)
for f in glob.glob(f"{L}/2026-1*-v6.json"):
    b = os.path.basename(f); day = b[:10]
    if not ("2026-10-09" <= day <= "2026-11-04"): continue
    pre, tag = b[:-8].rsplit("-", 1)
    if tag in ("now", "of") and "now" in b: continue
    ts = subprocess.run(["git", "log", "-1", "--format=%cI", "--", f], capture_output=True, text=True, cwd="/home/user/fk-model").stdout.strip() or "9999"
    files[pre].append((ts, tag, f))
lays = collections.OrderedDict(); backs = collections.OrderedDict(); used = []
for pre, lst in sorted(files.items()):
    day = pre[:10]; mid = f"{pre[11:]}-{day.replace('-', '')}"
    if mid not in res: continue
    before = [x for x in lst if x[0][:10] <= day]; ts, tag, f = max(before) if before else min(lst)
    fsf = f"{L}/{pre}-{tag}-first-starters.json"
    fs = {nm(str(x).split("|")[-1]) for x in (json.load(open(fsf)) if os.path.exists(fsf) else [])}
    used.append(f"{pre}:{tag}")
    v = json.load(open(f)); rr = res[mid]
    by = collections.defaultdict(list)
    for r in v:
        k = (int(r["race"]), nm(r["horse"]))
        if k in rr and rr[k][0] is not None and rr[k][1]: by[int(r["race"])].append((r, rr[k]))
    L_, B_ = [], []
    for rc, ents in by.items():
        tot = sum(r.get("p_model", r["p"]) for r, _ in ents)
        if tot <= 0: continue
        fav = min(b for _, (_, b) in ents)
        for r, (fin, bsp) in ents:
            ours = tot / r.get("p_model", r["p"]); won = fin == "1"; k = nm(r["horse"])
            if k in fs: continue
            if 15 <= bsp <= 40 and bsp >= 1.6 * ours: L_.append((rc, r["horse"], bsp, won, -(bsp - 1) if won else 0.92))
            if abs(bsp - fav) < 1e-9 and 4 <= bsp < 7 and ours >= 1.6 * bsp: B_.append((rc, r["horse"], ours, bsp, won, (bsp - 1) * 0.92 if won else -1.0))
    lays[pre] = L_; backs[pre] = B_
def tot(xs, j): return len(xs), sum(1 for x in xs if x[j - 1 if j == 4 else 3] ) if False else 0
print("model files:", "; ".join(used))
# lays: computed before 28 Oct, the settled paper sheets from 28 Oct
lay_rows = [(p, x) for p, xs in lays.items() if p[:10] < "2026-10-28" for x in xs]
n = len(lay_rows); w = sum(1 for _, x in lay_rows if x[3]); pl = sum(x[4] for _, x in lay_rows)
print(f"\nLAYS 9-27 Oct (computed): {n} lays, {w} winners, {pl:+.2f}u")
for p, x in lay_rows:
    if x[3]: print(f"   winner: {p} R{x[0]} {x[1]} BSP ${x[2]}")
by_m = collections.OrderedDict()
for p, x in lay_rows: a = by_m.setdefault(p[:7], [0, 0, 0.0]); a[0] += 1; a[1] += x[3]; a[2] += x[4]
print("   by month:", {k: (a[0], a[1], round(a[2], 2)) for k, a in by_m.items()})
# cross-check the computed rule on 28 Oct-4 Nov against the settled sheets (73 lays, 2 winners, +24.82u)
chk = [(p, x) for p, xs in lays.items() if p[:10] >= "2026-10-28" for x in xs]
print(f"   cross-check, computed 28 Oct-4 Nov: {len(chk)} lays, {sum(1 for _, x in chk if x[3])} winners, {sum(x[4] for _, x in chk):+.2f}u (settled sheets: 73 lays, 2 winners, +24.82u)")
b_rows = [(p, x) for p, xs in backs.items() for x in xs]
print(f"\nBACK FAVES 9 Oct-4 Nov: {len(b_rows)} bets, {sum(1 for _, x in b_rows if x[4])} won, {sum(x[5] for _, x in b_rows):+.2f}u")
for p, x in b_rows: print(f"   {p} R{x[0]} {x[1]:<22} ours ${x[2]:.2f} BSP ${x[3]:.2f} {'WON' if x[4] else 'lost'} {x[5]:+.2f}u")
