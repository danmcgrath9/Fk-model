"""Score the Vic-trained live pipeline on every state in Dave's archive sample (23 Oct 2026).
Results, the average opening price and Betfair SP come from the archive's own race files (point-in-time, pre-race
open; results written after). Per state: KL to BSP of our price and of the open, winner log loss, and the betting plan
(value 20c+ at the open, ours $1.60-$15, open under 3x ours, no first starters, no race with a first starter at $6 or
shorter at the open), flat 1u, settled at the open (16c deduction, the backtest's allowance) and at BSP (8% commission).
python score_states.py ARCHIVE_DIR PRICED_DIR"""
import json, glob, os, sys, collections
import numpy as np
root, pdir = sys.argv[1], sys.argv[2]
# results keyed by (raceId, breedingId)
res = {}; fs_race = collections.defaultdict(list); state_of = {}
idx = json.load(open(os.path.join(root, "index.json")))
for d in idx["days"]:
    for m in d["meetings"]:
        md = os.path.join(root, "meetings", m["meetingId"])
        for rid in m["raceIds"]:
            rp = os.path.join(md, "races", f"{rid}.json")
            if not os.path.exists(rp): continue
            A = json.load(open(rp)); state_of[str(rid)] = m.get("state")
            for e in A["entries"]:
                if e.get("scratched"): continue
                hr = e.get("horseResult") or {}; od = e.get("odds") or {}
                fin = hr.get("finishPosition"); bsp = hr.get("betfairStartingPrice"); op = od.get("avgOpen")
                res[(str(rid), str(e.get("breedingId")))] = dict(fin=fin, bsp=bsp, open=op, fs=bool(e.get("firstStarter")), name=(e.get("horse") or {}).get("name") if isinstance(e.get("horse"), dict) else e.get("horse"))
                if e.get("firstStarter") and op and op <= 6: fs_race[str(rid)].append(op)
DED, COMM = 0.16, 0.08
by_state = collections.defaultdict(lambda: dict(races=0, klm=[], klo=[], llm=[], llo=[], bets=[]))
skipped = collections.Counter()
for f in sorted(glob.glob(os.path.join(pdir, "*.v6.json"))):
    rows = json.load(open(f)); by = collections.defaultdict(list)
    for r in rows: by[r["race_id"]].append(r)
    for rid, rs in by.items():
        st = state_of.get(rid, "?"); S = by_state[st]
        run = [(r, res.get((rid, r["horse_id"]))) for r in rs]
        run = [(r, x) for r, x in run if x is not None]
        if len(run) < 3: skipped[(st, "unmatched")] += 1; continue
        if any(x["fin"] is None for _, x in run) or not any(x["fin"] == 1 for _, x in run): skipped[(st, "no result")] += 1; continue
        if any(not x["open"] or x["open"] <= 1 for _, x in run): skipped[(st, "no open")] += 1; continue
        p = np.array([r["p"] for r, _ in run]); p /= p.sum()
        o = np.array([1 / x["open"] for _, x in run]); o /= o.sum()
        have_bsp = all(x["bsp"] and x["bsp"] > 1 for _, x in run)
        w = [i for i, (_, x) in enumerate(run) if x["fin"] == 1][0]
        S["races"] += 1; S["llm"].append(-np.log(p[w])); S["llo"].append(-np.log(o[w]))
        if have_bsp:
            q = np.array([1 / x["bsp"] for _, x in run]); q /= q.sum()
            S["klm"].append(float(np.sum(q * np.log(q / p)))); S["klo"].append(float(np.sum(q * np.log(q / o))))
        if fs_race.get(rid): continue  # race rule: a first starter at $6 or shorter at the open
        for i, (r, x) in enumerate(run):
            ours = 1 / p[i]; op = x["open"]
            if x["fs"] or not (1.6 <= ours <= 15) or p[i] * op < 1.2 or op >= 3 * ours: continue
            won = x["fin"] == 1
            S["bets"].append(dict(won=won, open=op, bsp=x["bsp"], ours=ours,
                                  pl_open=(op - 1) * (1 - DED) if won else -1.0,
                                  pl_bsp=((x["bsp"] - 1) * (1 - COMM) if won else -1.0) if x["bsp"] and x["bsp"] > 1 else np.nan))
print("skipped races:", dict(skipped))
print("\n| state | races | KL to BSP: ours | KL to BSP: open | ours closer? | winner log loss: ours | open | bets | won | ROI at open (16c ded) | ROI at BSP (8% comm) | beat BSP | median open/BSP |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
tot = dict(races=0, klm=[], klo=[], llm=[], llo=[], bets=[])
order = sorted(by_state, key=lambda s: -by_state[s]["races"])
for st in order + ["ALL non-VIC", "ALL"]:
    if st.startswith("ALL"):
        S = dict(races=0, klm=[], klo=[], llm=[], llo=[], bets=[])
        for s2, v in by_state.items():
            if st == "ALL" or s2 != "VIC":
                S["races"] += v["races"]
                for k in ("klm", "klo", "llm", "llo", "bets"): S[k] += v[k]
    else: S = by_state[st]
    b = S["bets"]; n = len(b)
    won = sum(x["won"] for x in b); roi_o = 100 * np.mean([x["pl_open"] for x in b]) if n else float("nan")
    pb = [x["pl_bsp"] for x in b if np.isfinite(x["pl_bsp"])]; roi_b = 100 * np.mean(pb) if pb else float("nan")
    beat = [x["open"] > x["bsp"] for x in b if x["bsp"] and x["bsp"] > 1]
    med = np.median([x["open"] / x["bsp"] for x in b if x["bsp"] and x["bsp"] > 1]) if beat else float("nan")
    klm = np.mean(S["klm"]) if S["klm"] else float("nan"); klo = np.mean(S["klo"]) if S["klo"] else float("nan")
    print(f"| {st} | {S['races']} ({len(S['klm'])} with BSP) | {klm:.4f} | {klo:.4f} | {'yes' if klm < klo else 'NO'} | {np.mean(S['llm']):.3f} | {np.mean(S['llo']):.3f} | {n} | {won} | {roi_o:+.1f}% | {roi_b:+.1f}% | {100*np.mean(beat) if beat else float('nan'):.0f}% | {med:.2f} |")
