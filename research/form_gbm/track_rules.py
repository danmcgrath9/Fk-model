"""Paper tracker for every Betfair SP rule under watch (10 Nov 2026, founder: "Track all of those", after
t_both_samples.py found six rules that made money in backtest H1, H2 and the live weeks). Rebuilt from scratch on every
run, so it is safe to run as often as you like: run it after each meeting's results file lands
(data/live_bets/<prefix>-results.txt, scripts/meeting_results.py output).

Each meeting is priced by its own live model file (the -v6.json committed nearest before race day), with Form King's
BSP, finish and opening price (fk_open in the meeting's -prices.txt). 1u per bet at BSP, 8% commission; a lay is 1u of
the backer's stake. First starters never count.
    python3.13 track_rules.py            -> data/live_bets/rule-tracker.csv and a totals table
"""
import collections, csv, glob, json, os, re, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "../.."))
L = os.path.join(REPO, "data/live_bets"); ARCH = os.path.join(L, "results-archive")
START, TRACK_FROM = "2026-10-09", "2026-11-10"      # live since 9 Oct; tracking forward from 10 Nov
UNIT = 50.0
nm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())

# (key, side, description, test(r)) -- r has bsp, ours, open, fav
RULES = [
    ("L812x16", "LAY", "Lay $8-$12, BSP >= 1.6x ours (current)", lambda r: 8 <= r["bsp"] < 12 and r["bsp"] >= 1.6 * r["ours"]),
    ("L2540drift2", "LAY", "Lay $25-$40, drifted 2x from open", lambda r: 25 <= r["bsp"] < 40 and r["open"] and r["bsp"] >= 2 * r["open"]),
    ("L2540worse", "LAY", "Lay $25-$40, BSP <= ours/1.6", lambda r: 25 <= r["bsp"] < 40 and r["bsp"] * 1.6 <= r["ours"]),
    ("L812firm", "LAY", "Lay $8-$12, firmed 1.5x from open", lambda r: 8 <= r["bsp"] < 12 and r["open"] and r["bsp"] * 1.5 <= r["open"]),
    ("L1215drift", "LAY", "Lay $12-$15, drifted 1.25x from open", lambda r: 12 <= r["bsp"] < 15 and r["open"] and r["bsp"] >= 1.25 * r["open"]),
    ("B35firm", "BACK", "Back $3-$5, firmed 1.5x from open", lambda r: 3 <= r["bsp"] < 5 and r["open"] and r["bsp"] * 1.5 <= r["open"]),
    ("L1540x15", "LAY", "Lay $15-$40, BSP >= 1.5x ours (current, failing live)", lambda r: 15 <= r["bsp"] <= 40 and r["bsp"] >= 1.5 * r["ours"]),
    ("BfavX16", "BACK", "Back BSP fav $4-$7, ours >= 1.6x BSP (current)", lambda r: r["fav"] and 4 <= r["bsp"] < 7 and r["ours"] >= 1.6 * r["bsp"]),
]


def results():
    """{meeting id: {(race, name): (finish, bsp)}}: the archive (Oct, meeting_results.py exports with a ## header)
    then data/live_bets/<prefix>-results.txt (newer, wins)."""
    res = {}
    def parse(lines):
        d = {}
        for l in lines:
            m = re.match(r"R(\d+)\s+(.+?)\s+finish\s+(\S+)\s+SP\s+(\S+)\s+BSP\s+(\S+)", l.strip())
            if m:
                try: bsp = float(m.group(5))
                except ValueError: bsp = None
                d[(int(m.group(1)), nm(m.group(2)))] = (m.group(3) if m.group(3) not in ("None", "0") else None, bsp)
        return d
    for f in sorted(glob.glob(f"{ARCH}/*.md")):
        cur, buf = None, []
        for l in open(f):
            m = re.match(r"## ([\w-]+-\d{8}): ", l)
            if m:
                if cur and buf: res[cur] = parse(buf) or res.get(cur, {})
                cur, buf = m.group(1), []; continue
            buf.append(l)
        if cur and buf: res[cur] = parse(buf) or res.get(cur, {})
    for f in glob.glob(f"{L}/2026-*-results.txt"):
        if "partial" in f or "founder" in f: continue
        b = os.path.basename(f)[:-12]; day = b[:10]; mid = f"{b[11:]}-{day.replace('-', '')}"
        d = parse(open(f))
        if d: res[mid] = d
    return res


def model_files():
    """{prefix: newest -v6.json committed on or before race day (else the earliest)}."""
    files = collections.defaultdict(list)
    for f in glob.glob(f"{L}/2026-1*-v6.json"):
        b = os.path.basename(f); day = b[:10]
        if day < START: continue
        pre, tag = b[:-8].rsplit("-", 1)
        ts = subprocess.run(["git", "log", "-1", "--format=%cI", "--", f], capture_output=True, text=True, cwd=REPO).stdout.strip() or "9999"
        files[pre].append((ts, tag, f))
    out = {}
    for pre, lst in files.items():
        before = [x for x in lst if x[0][:10] <= pre[:10]]
        out[pre] = max(before) if before else min(lst)
    return out


def opens(pre):
    d = {}
    f = f"{L}/{pre}-prices.txt"
    if os.path.exists(f):
        for l in open(f):
            pa = [x.strip() for x in l.split("#")[0].split(",")]
            mo = re.search(r"fk_open\s+([\d.]+)", l)
            if len(pa) >= 3 and pa[0].isdigit() and mo: d[(int(pa[0]), nm(pa[1]))] = float(mo.group(1))
    return d


def main():
    res, mf = results(), model_files()
    bets, missing = [], []
    for pre, (ts, tag, f) in sorted(mf.items()):
        mid = f"{pre[11:]}-{pre[:10].replace('-', '')}"
        if mid not in res: missing.append(pre); continue
        rr, op = res[mid], opens(pre)
        try: fs = {str(x) for x in json.load(open(f.replace("-v6.json", "-first-starters.json")))}
        except Exception: fs = set()
        by = collections.defaultdict(list)
        for r in json.load(open(f)):
            k = (int(r["race"]), nm(r["horse"]))
            if k in rr and rr[k][0] is not None and rr[k][1] and rr[k][1] > 1: by[int(r["race"])].append((r, rr[k]))
        for rc, ents in by.items():
            tot = sum(r.get("p_model", r["p"]) for r, _ in ents)
            if tot <= 0 or not any(fin == "1" for _, (fin, _) in ents): continue
            fav = min(b for _, (_, b) in ents)
            for r, (fin, bsp) in ents:
                if f"{rc}|{r['horse']}" in fs: continue
                x = dict(bsp=bsp, ours=tot / r.get("p_model", r["p"]), open=op.get((rc, nm(r["horse"]))), fav=abs(bsp - fav) < 1e-9)
                for key, side, _, test in RULES:
                    if not test(x): continue
                    w = fin == "1"
                    pl = (-(bsp - 1) if w else 0.92) if side == "LAY" else ((bsp - 1) * 0.92 if w else -1.0)
                    bets.append(dict(date=pre[:10], meeting=pre[11:], rule=key, side=side, race=rc, horse=r["horse"],
                                     ours=round(x["ours"], 2), open=x["open"] or "", bsp=bsp, won=int(w), units=round(pl, 4)))
    with open(f"{L}/rule-tracker.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(bets[0]) if bets else ["date"]); w.writeheader(); w.writerows(bets)
    print(f"{len({b['date'] + b['meeting'] for b in bets})} meetings settled, {len(bets)} bets -> data/live_bets/rule-tracker.csv"
          + (f"; no results yet: {', '.join(missing)}" if missing else ""))
    print(f"\n{'rule':52} | since {START} (live)                     | since {TRACK_FROM} (tracking)")
    for key, side, desc, _ in RULES:
        cells = []
        for since in (START, TRACK_FROM):
            g = [b for b in bets if b["rule"] == key and b["date"] >= since]
            n, wn = len(g), sum(b["won"] for b in g); e = sum(1 / b["bsp"] for b in g); u = sum(b["units"] for b in g)
            cells.append(f"{n:4d} {wn:3d} won ({e:5.1f}) {u:+8.2f}u ${u*UNIT:+8,.0f}")
        print(f"{desc:52} | {cells[0]} | {cells[1]}")


if __name__ == "__main__":
    main()
