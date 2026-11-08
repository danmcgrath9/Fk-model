"""All three books on Dave's all-states archive week (20-26 Aug 2026), the current rules (8 Nov 2026, founder: "do it for
ALL states what theoretical would be"). Our price = the Vic-trained live pipeline (priced_states/*.v6.json), the open =
the archive's average opening price, BSP and finish from the archive.
  Open book: ours $1.60-$15, open under 3x ours, minimum 0.95 x (E/p^0.82)^(1/0.78) with E 1.15 under $4 (ours) else 1.2,
    steps x1/x1.25/x1.5 sized by stake_rule, first starters never bet; metro tracks no bet at $12+ (the metro fix's market
    blend is NOT applied outside VIC); settled at the open less 7% on winnings; $50 a unit.
  Lays: BSP $15-$40 and at least 1.6x ours, 1 lay at BSP, first starters excluded; $200; commission 8% (NSW/ACT 10%).
  Backs: the BSP favourite at $4-$7 when ours >= 1.6x its BSP; $500 a unit; same commission.
VIC is IN-SAMPLE here (v10 trained through 14 Oct) and is shown only for the record."""
import json, glob, os, sys, collections
import numpy as np, stake_rule
root, pdir = sys.argv[1], sys.argv[2]
res, state_of, track_of = {}, {}, {}
idx = json.load(open(os.path.join(root, "index.json")))
for d in idx["days"]:
    for m in d["meetings"]:
        md = os.path.join(root, "meetings", m["meetingId"])
        for rid in m["raceIds"]:
            rp = os.path.join(md, "races", f"{rid}.json")
            if not os.path.exists(rp): continue
            A = json.load(open(rp)); state_of[str(rid)] = m.get("state"); track_of[str(rid)] = m["meetingId"].rsplit("-", 1)[0]
            for e in A["entries"]:
                if e.get("scratched"): continue
                hr = e.get("horseResult") or {}; od = e.get("odds") or {}
                res[(str(rid), str(e.get("breedingId")))] = dict(fin=hr.get("finishPosition"), bsp=hr.get("betfairStartingPrice"),
                                                                 open=od.get("avgOpen"), fs=bool(e.get("firstStarter")))
METRO = {"flemington", "caulfield", "moonee-valley", "sandown", "sandown-hillside", "sandown-lakeside", "randwick", "randwick-kensington",
         "rosehill", "rosehill-gardens", "canterbury", "canterbury-park", "warwick-farm", "eagle-farm", "doomben", "morphettville",
         "morphettville-parks", "ascot", "belmont", "belmont-park"}
B = collections.defaultdict(lambda: dict(races=0, ob=[], lay=[], back=[]))
for f in sorted(glob.glob(os.path.join(pdir, "*.v6.json"))):
    rows = json.load(open(f)); by = collections.defaultdict(list)
    for r in rows: by[r["race_id"]].append(r)
    for rid, rs in by.items():
        st = state_of.get(rid, "?"); X = B[st]
        run = [(r, res.get((rid, r["horse_id"]))) for r in rs]; run = [(r, x) for r, x in run if x is not None]
        if len(run) < 3 or any(x["fin"] is None for _, x in run) or not any(x["fin"] == 1 for _, x in run): continue
        if any(not x["open"] or x["open"] <= 1 for _, x in run): continue
        X["races"] += 1
        p = np.array([r["p"] for r, _ in run]); p /= p.sum(); n = len(run)
        comm = 0.10 if st in ("NSW", "ACT") else 0.08; metro = track_of.get(rid, "") in METRO
        bsps = [x["bsp"] for _, x in run if x["bsp"] and x["bsp"] > 1]
        fav = min(bsps) if len(bsps) == n else None
        for i, (r, x) in enumerate(run):
            ours, op, won, bsp = 1 / p[i], x["open"], x["fin"] == 1, x["bsp"]
            # open book
            if not x["fs"] and 1.6 <= ours <= 15 and op < 3 * ours and not (metro and op >= 12):
                E = 1.15 if ours < 4 else 1.2; mo = 0.95 * (E / p[i] ** 0.82) ** (1 / 0.78)
                if op >= mo:
                    tiers = [mo * k for k in (1.0, 1.25, 1.5) if mo * k < 3 * ours]; tot = prev = 0.0
                    for k, tt in enumerate(tiers):
                        tp = tiers[k + 1] if k + 1 < len(tiers) else tt
                        s_ = stake_rule.stake(p[i] ** 0.82 * tp ** -0.22, tp, False, n); add = max(0.0, s_ - prev); prev = max(prev, s_)
                        if op >= tt: tot += add
                    if tot > 0: X["ob"].append((tot, tot * (op - 1) * 0.93 if won else -tot, won))
            if not (bsp and bsp > 1): continue
            # lay book
            if not x["fs"] and 15 <= bsp <= 40 and bsp >= 1.6 * ours:
                X["lay"].append((-(bsp - 1) if won else (1 - comm), won))
            # back book
            if fav is not None and bsp == fav and 4 <= bsp <= 7 and ours >= 1.6 * bsp:
                X["back"].append(((bsp - 1) * (1 - comm) if won else -1.0, won))
def line(st, X):
    ob, lay, bk = X["ob"], X["lay"], X["back"]
    su = sum(s for s, _, _ in ob); pu = sum(p for _, p, _ in ob); lw = sum(w for _, w in lay); lu = sum(p for p, _ in lay)
    bu = sum(p for p, _ in bk); bw = sum(w for _, w in bk)
    d = pu * 50 + lu * 200 + bu * 500
    print(f"| {st} | {X['races']} | {len(ob)} bets, {sum(w for *_, w in ob)} won, {pu:+.1f}u on {su:.1f}u ({100*pu/su if su else 0:+.0f}%) | ${pu*50:+,.0f} "
          f"| {len(lay)}, {lw} won, {lu:+.2f}u | ${lu*200:+,.0f} | {len(bk)}, {bw} won, {bu:+.2f}u | ${bu*500:+,.0f} | **${d:+,.0f}** |")
print("| State | Races | Open book | $ | Lays | $ | Fav backs | $ | Total |")
print("|---|---|---|---|---|---|---|---|---|")
order = sorted(B, key=lambda s: -B[s]["races"])
for st in order: line(st + (" (in-sample)" if st == "VIC" else ""), B[st])
tot = dict(races=0, ob=[], lay=[], back=[])
for s, v in B.items():
    if s == "VIC": continue
    tot["races"] += v["races"]
    for k in ("ob", "lay", "back"): tot[k] += v[k]
line("ALL non-VIC", tot)
