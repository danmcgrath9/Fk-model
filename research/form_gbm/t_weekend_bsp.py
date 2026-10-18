"""The live meetings against BSP (18 Oct 2026, founder: "a backtest with the data we pulled this weekend, for getting closer
to bsp ... why bsp is moving"). Every meeting in fwd_betmatic.MEETINGS (5 to 18 Oct), with the weekend (Thu 15 to Sun 18
Oct, eight meetings, every one with a 9:35am race-morning pull) shown on its own.

Per runner: OURS = the model's price as first committed for the meeting (git history, made before the market), RE-PRICE =
the race-morning re-price (the current v6 file: final field, blended with the open), OPEN = Form King's average opening
price, MORNING = Form King's best price at the race-day pull (9:35am for the weekend; earlier meetings vary), BSP and the
finish from meeting_results.py. Races are used only when every starter has all five, chances normalised within the race.

    python3.13 t_weekend_bsp.py RESULTS_TXT [...]"""
import json, os, re, subprocess, sys, collections
import numpy as np
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
from opens import parse_opens
L = os.path.join(here, "../../data/live_bets"); REPO = os.path.join(here, "../..")
src = open(os.path.join(here, "fwd_betmatic.py")).read()
MEETINGS = eval(src[src.index("MEETINGS = [") + len("MEETINGS = "): src.index("]   # add each meeting") + 1])
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
def git_first(path):
    h = subprocess.run(["git", "-C", REPO, "log", "--diff-filter=A", "--format=%h", "--", path], capture_output=True, text=True).stdout.split()
    if not h: return None
    r = subprocess.run(["git", "-C", REPO, "show", f"{h[-1]}:{path}"], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else None
res, cur = {}, None
for p in sys.argv[1:]:
    for l in open(p):
        mm = re.match(r"## (\S+):", l)
        if mm: cur = mm.group(1); continue
        mm = re.match(r"R(\d+) (.+?)\s+finish (\S+)\s+SP (\S+)\s+BSP (\S+)", l)
        if mm and cur and mm.group(3) != "None" and mm.group(5) != "None":
            res[(cur, int(mm.group(1)), norm(mm.group(2)))] = (int(mm.group(3)), float(mm.group(5)))
rows = []   # meeting label, weekend?, race, horse, ours, reprice, open, morning, bsp, won
for label, mid, pre, g, snap in MEETINGS:
    B = f"{pre}-{g}" if g else pre
    first = git_first(f"data/live_bets/{B}-v6.json")
    nowf = f"{L}/{B}-v6.json"
    if first is None or not os.path.exists(nowf): continue
    ours = {(int(r["race"]), norm(r["horse"])): r["p"] for r in first}
    rep = {(int(r["race"]), norm(r["horse"])): r["p"] for r in json.load(open(nowf))}
    mk = {}
    for l in open(f"{L}/{pre}-prices.txt"):
        pa = [x.strip() for x in l.split("#")[0].split(",")]
        if len(pa) >= 4 and pa[0].isdigit() and not pa[2].upper().startswith("SCR"):
            try: now = float(pa[2])
            except ValueError: continue
            fk, tab = parse_opens(", ".join(pa[4:]) if len(pa) > 4 else "")
            mk[(int(pa[0]), norm(pa[1]))] = (fk, now)
    wk = any(d in label for d in ("15 Oct", "16 Oct", "17 Oct", "18 Oct"))
    byrace = collections.defaultdict(list)
    for (m_, rn, hn), (fin, bsp) in res.items():
        if m_ != mid: continue
        o, mo = mk.get((rn, hn), (None, None))
        byrace[rn].append((hn, ours.get((rn, hn)), rep.get((rn, hn)), o, mo, bsp, fin == 1))
    for rn, rs in byrace.items():
        if not rn or len(rs) < 3 or any(x is None or (isinstance(x, float) and not x > 0) for r in rs for x in r[1:6]): continue
        if not all(r[3] > 1 and r[4] > 1 and r[5] > 1 for r in rs) or sum(r[6] for r in rs) != 1: continue
        for r in rs: rows.append((label, wk, rn) + r)
print(f"runners {len(rows)}; races {len({(r[0], r[2]) for r in rows})}; weekend races {len({(r[0], r[2]) for r in rows if r[1]})}")
lab = np.array([r[0] for r in rows]); WK = np.array([r[1] for r in rows]); RN = np.array([r[2] for r in rows])
key = np.unique(np.char.add(lab, np.char.mod("|%d", RN)), return_inverse=True)[1]; nR = key.max() + 1
A = lambda i: np.array([float(r[i]) for r in rows])
po, pr, op, mo, bs = A(4), A(5), A(6), A(7), A(8); won = np.array([r[9] for r in rows])
def nz(q): return q / np.bincount(key, weights=q, minlength=nR)[key]
Q = dict(ours=nz(po), reprice=nz(pr), open=nz(1 / op), morning=nz(1 / mo), bsp=nz(1 / bs))
names = {"open": "opening market (Form King average)", "ours": "our model, priced before the market", "reprice": "our race-morning re-price (blended with the open)",
         "morning": "race-morning market (best price)", "bsp": "BSP"}
def table(sel, title):
    races = np.unique(key[sel]); print(f"\n### {title}: {len(races)} races, {sel.sum()} runners\n")
    print("| price | KL to BSP | winner log loss |\n|---|---|---|")
    qb = Q["bsp"]
    for k in ("open", "ours", "reprice", "morning", "bsp"):
        q = Q[k]; kl = np.sum((qb * np.log(qb / q))[sel]) / len(races); ll = -np.log(q[sel & won]).mean()
        print(f"| {names[k]} | {kl:.4f} | {ll:.4f} |")
    lo, lb, lm, lr = (np.log(Q[k][sel]) for k in ("open", "bsp", "morning", "reprice"))
    lu = np.log(Q["ours"][sel]); d = lu - lo; y = lb - lo
    sl = np.polyfit(d, y, 1)[0]
    big = np.abs(d) > np.log(1.25)
    agree = (np.sign(d[big]) == np.sign(y[big])).mean()
    frac_m = np.polyfit(y, lm - lo, 1)[0]
    res_sl = np.polyfit(lr - lm, lb - lm, 1)[0]; res_c = np.corrcoef(lr - lm, lb - lm)[0, 1]
    print(f"\n- BSP's move from the open, against our price's distance from the open: slope {sl:.2f} (1 = BSP went all the way to our price, 0 = it ignored it)")
    print(f"- where we were 25%+ off the open ({big.sum()} runners), BSP moved our way {agree:.0%} of the time")
    print(f"- share of the open-to-BSP move already made by the race-morning pull: {frac_m:.0%}")
    print(f"- after the morning pull, our re-price vs the morning market still points the way to BSP: slope {res_sl:.2f}, correlation {res_c:.2f}")
    return y, d
table(np.ones(len(rows), bool), "Every live meeting, 5 to 18 Oct")
y, d = table(WK, "The weekend, Thu 15 to Sun 18 Oct (eight meetings, 9:35am race-morning pulls)")
# why it moved, weekend and all: the morning-to-BSP leg against the open-to-morning leg (momentum or reversal)
for sel, t in ((np.ones(len(rows), bool), "all"), (WK, "weekend")):
    a = np.log(Q["morning"][sel] / Q["open"][sel]); bb = np.log(Q["bsp"][sel] / Q["morning"][sel])
    print(f"{t}: morning-to-BSP move against open-to-morning move: slope {np.polyfit(a, bb, 1)[0]:+.2f}, correlation {np.corrcoef(a, bb)[0, 1]:+.2f}")
# the bets actually filled at the open (forward test), weekend
fills = []
for l in open(f"{L}/forward-test-betmatic.md"):
    pa = [x.strip() for x in l.strip().strip("|").split("|")]
    if len(pa) == 12 and pa[1].startswith("R") and pa[1][1:].isdigit():
        fills.append((pa[0], int(pa[1][1:]), norm(pa[2])))
idx = {(r[0], r[2], norm(r[3])): i for i, r in enumerate(rows)}
print("\n### Our filled bets: price at the open, race morning and BSP\n")
print("| sample | bets in the table | median open / BSP | median morning / BSP | share where the morning price was still over BSP | share firmed open to morning |\n|---|---|---|---|---|---|")
for t, keep in (("every live meeting", lambda f: True), ("the weekend", lambda f: any(dd in f[0] for dd in ("15 Oct", "16 Oct", "17 Oct", "18 Oct")))):
    ii = [idx[f] for f in fills if f in idx and keep(f)]
    if not ii: continue
    ii = np.array(ii)
    print(f"| {t} | {len(ii)} | {np.median(op[ii] / bs[ii]):.2f} | {np.median(mo[ii] / bs[ii]):.2f} | {(mo[ii] > bs[ii]).mean():.0%} | {(mo[ii] < op[ii]).mean():.0%} |")
# the race-morning price we should hold: our price blended with the MORNING market instead of the open (grid, two halves by date)
print("\n### Race morning: our price blended with the morning market (weights fitted on one half of the meetings, scored on the other)\n")
order = [m[0] for m in MEETINGS]; mi = np.array([order.index(x) for x in lab]); hf = (mi >= np.median(mi)).astype(int)
def rn(z): e = np.exp(z - z.max()); return nz(e)
def blend(a, c): return nz(np.exp(a * np.log(Q["ours"]) + c * np.log(Q["morning"])))
qb = Q["bsp"]
def klr(q, s): return np.sum((qb * np.log(qb / q))[s]) / len(np.unique(key[s]))
grid = [(a, c) for a in np.arange(0, 1.01, 0.05) for c in np.arange(0, 1.31, 0.05)]
out = np.zeros(len(rows)); ws = []
for h in (0, 1):
    a, c = min(grid, key=lambda w: klr(blend(*w), hf != h)); ws.append((a, c)); q = blend(a, c); out[hf == h] = q[hf == h]
out = nz(out)
allm = np.ones(len(rows), bool)
for t, s in (("every live meeting", allm), ("the weekend", WK)):
    print(f"- {t}: KL to BSP, morning market {klr(Q['morning'], s):.4f}, ours + morning {klr(out, s):.4f}; winner log loss {-np.log(Q['morning'][s & won]).mean():.4f} vs {-np.log(out[s & won]).mean():.4f}")
print(f"- weights (ours, morning) by half: {', '.join(f'{a:.2f}/{c:.2f}' for a, c in ws)}")
