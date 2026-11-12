"""Tracker for the 9am types (12 Nov 2026, founder: "I don't like them, they make no logical sense. But keep track").
From night/t_types.py on the timed races: horses still overs at 9am on race day (the 9am price at least 1.3x our price)
paid among our 2nd-3rd picks (+42%, both blocks), barrier 4-8 (+19%) and senior riders (+10%). Tracked here on every
settled live meeting, 1u flat at the 9am price, no deduction, first starters out. Not bet.

    python3.13 track_9am.py FLUC_AT_09.md [FLUC_AT_09.md ...]   (scripts/fluc_at.py 09:00 output, any number of files)
Rebuilds data/live_bets/9am-tracker.csv from every file given plus the rows already in it (a meeting's rows are replaced
when it is given again), and prints the totals by type. Our price and rank come from each meeting's live -v6.json (the
newest committed on or before race day, as track_rules.py picks it), the barrier from its -v5s1.json, the result from its
results file. The senior-rider type needs the apprentice flag, which the live files do not carry, so it is not tracked.
ALSO THE 9AM BLEND (12 Nov 2026, founder: "you realise we can get on for $1,000 - $2,000 win with all bookies if we do
that"; night/t_blend_bsp.py): our price mixed with the 9am market, log p = 0.20 log(ours) + 1.00 log(1/9am price),
renormalised per race; a runner whose 9am price is at least 1.05x the blend's price is a "blend 9am" bet. Settled to win
$1,000 per bookie ($2,000 at the metro tracks), the minimum bet limit, as mbl_pl."""
import math
import collections, csv, io, json, os, sys
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import track_rules as T

L = T.L; nm = T.nm; OUT = os.path.join(L, "9am-tracker.csv")
res, mf = T.results(), T.model_files()
pre_of = {}
for pre in mf:
    day = pre[:10].replace("-", ""); slug = pre[11:]
    for k in res:
        if k.endswith(day) and k.startswith(slug): pre_of[k] = pre
flu = collections.defaultdict(dict)
for f in sys.argv[1:]:
    s = open(f).read(); a = s.find("CSV-BEGIN") + 9; b = s.find("CSV-END")
    for r in csv.DictReader(io.StringIO(s[a:b].strip())):
        if r["at_price"]: flu[r["meeting_id"]][(int(r["race"]), nm(r["name"]))] = float(r["at_price"])
rows = [r for r in (csv.DictReader(open(OUT)) if os.path.exists(OUT) else []) if r["meeting_id"] not in flu]
for mid, px in flu.items():
    pre = pre_of.get(mid); R = res.get(mid)
    if not pre or not R: continue
    ts, tag, f6 = mf[pre]
    v6 = json.load(open(f6)); fs = set()
    ffs = f6.replace("-v6.json", "-first-starters.json")
    if os.path.exists(ffs):
        x = json.load(open(ffs)); fs = {nm(str(h).split("|")[-1]) for h in (x if isinstance(x, list) else x.keys())}
    bar = {}
    f5 = f6.replace("-v6.json", "-v5s1.json")
    if os.path.exists(f5):
        for r in json.load(open(f5)): bar[(int(r["race"]), nm(r["horse"]))] = r.get("barrier")
    by = collections.defaultdict(list)
    for r in v6: by[int(r["race"])].append(r)
    lim = 2000.0 if any(pre[11:].startswith(m) for m in ("flemington", "caulfield", "moonee-valley", "sandown")) else 1000.0
    for rc, rs in by.items():
        tot = sum(x["p"] for x in rs); rs = sorted(rs, key=lambda x: -x["p"])
        priced = [x for x in rs if x["p"] > 0 and px.get((rc, nm(x["horse"])))]
        blend = {}
        if len(priced) >= 4:   # the runners with a 9am price (a scratched runner has none), as night/t_blend_bsp.py
            tp = sum(x["p"] for x in priced)
            w = {nm(x["horse"]): math.exp(0.20 * math.log(x["p"] / tp) + 1.00 * math.log(1 / px[(rc, nm(x["horse"]))])) for x in priced}
            sw = sum(w.values()); blend = {h: sw / v for h, v in w.items()}
        for rank, r in enumerate(rs, 1):
            k = (rc, nm(r["horse"])); p9 = px.get(k); ours = tot / r["p"] if r["p"] > 0 else None
            ob = blend.get(k[1]); is_blend = bool(ob and p9 and 1.6 <= ob <= 15 and p9 >= 1.05 * ob)
            over = bool(p9 and ours and 1.6 <= ours <= 15 and p9 >= 1.3 * ours)
            if not p9 or k[1] in fs or not (over or is_blend): continue
            fin, bsp = R.get(k, (None, None))
            if fin is None and bsp is None: continue
            won = fin == "1"; b = bar.get(k)
            types = [t for t, ok in (("overs 1.3x", over), ("our 2nd-3rd", over and 2 <= rank <= 3),
                                     ("barrier 4-8", over and b is not None and 4 <= int(b) <= 8), ("blend 9am", is_blend)) if ok]
            rows.append(dict(date=pre[:10], meeting_id=mid, race=rc, horse=r["horse"], our_price=f"{ours:.2f}" if ours else "", our_rank=rank,
                             barrier="" if b is None else b, price_9am=p9, ratio=f"{p9 / ours:.2f}", finish=fin or "",
                             pl=f"{(p9 - 1) if won else -1.0:+.2f}", blend_price=f"{ob:.2f}" if ob else "",
                             mbl_pl=f"{lim if won else -lim / (p9 - 1):+.0f}" if is_blend else "", types="; ".join(types)))
rows.sort(key=lambda r: (r["date"], r["meeting_id"], int(r["race"])))
F = ["date", "meeting_id", "race", "horse", "our_price", "our_rank", "barrier", "price_9am", "ratio", "finish", "pl", "blend_price", "mbl_pl", "types"]
with open(OUT, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=F); w.writeheader(); w.writerows(rows)
print(f"{OUT}: {len(rows)} runners overs at 9am, {len({r['meeting_id'] for r in rows})} meetings")
print("| type | bets | won | profit (1u at 9am) | ROI |\n|---|---|---|---|---|")
rows_old = rows
for t in ("overs 1.3x", "our 2nd-3rd", "barrier 4-8", "blend 9am"):
    xs = [r for r in rows if t in r["types"]]
    pl = sum(float(r["pl"]) for r in xs)
    mbl = sum(float(r["mbl_pl"]) for r in xs if r.get("mbl_pl"))
    print(f"| {t} | {len(xs)} | {sum(r['finish'] == '1' for r in xs)} | {pl:+.1f}u | {pl / max(len(xs), 1):+.0%} |" + (f" ${mbl:+,.0f} a bookie at the limits" if t == "blend 9am" else ""))
