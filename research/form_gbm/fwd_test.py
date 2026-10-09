"""Forward test: every bet the CURRENT rules flag at each meeting's opening prices, settled against the real results.
Not just the bets taken or tweeted: the model's whole book, so the live record cannot hide a bad run behind selection.

python fwd_test.py RESULTS_TXT OUT_MD   (meetings listed in MEETINGS below; RESULTS_TXT from scripts/meeting_results.py)
Stakes: stake_rule.py (live staking, most 5u). Also flat 1u, and closing-line value (opening price / Betfair SP)."""
import csv, json, re, subprocess, sys, os, collections, tempfile
L = os.path.join(os.path.dirname(__file__), "../../data/live_bets")
# (label, meeting id in results, v6/angles prefix, opening prices file = the first snapshot with a market up)
MEETINGS = [
    ("Mon 5 Oct Pakenham", "pakenham-synthetic-20261005", "2026-10-05-pakenham", "2026-10-05-pakenham-prices.txt"),
    ("Tue 6 Oct Mildura (G4)", "mildura-20261006", "2026-10-06-mildura-g4", "2026-10-06-mildura-prices-monday.txt"),
    ("Wed 7 Oct Geelong (Soft)", "geelong-20261007", "2026-10-07-geelong-s6", "2026-10-07-geelong-prices-monday.txt"),
    ("Thu 8 Oct Kyneton (G4)", "kyneton-20261008", "2026-10-08-kyneton-g4", "2026-10-08-kyneton-prices-wed.txt"),
    ("Fri 9 Oct Ballarat (G4)", "ballarat-20261009", "2026-10-09-ballarat-g4", "2026-10-09-ballarat-prices.txt"),
    ("Fri 9 Oct Cranbourne (G4)", "cranbourne-20261009", "2026-10-09-cranbourne-g4", "2026-10-09-cranbourne-prices-thu930.txt"),
]
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
res_p, out_p = sys.argv[1:3]
res, cur = {}, None
for l in open(res_p):
    m = re.match(r"## (\S+):", l)
    if m: cur = m.group(1); continue
    m = re.match(r"R(\d+) (.+?)\s+finish (\S+)\s+SP (\S+)\s+BSP (\S+)", l)
    if m and cur:
        f = None if m.group(3) == "None" else int(m.group(3))
        bsp = None if m.group(5) == "None" else float(m.group(5))
        res[(cur, int(m.group(1)), norm(m.group(2)))] = (f, bsp)
here = os.path.dirname(os.path.abspath(__file__))
lines = ["# Forward test: the model's whole book at opening prices, settled", "",
         "Every bet the current rules flag at each meeting's opening prices (not just the bets taken or tweeted).",
         "Live stakes from stake_rule.py ($100 a unit, most 5u); flat = 1u a bet. CLV = opening price over Betfair SP (above 1 = we beat the close).", "",
         "| Meeting | Bets | Won | Staked | P/L live | P/L flat | Avg CLV | Beat BSP |", "|---|---|---|---|---|---|---|---|"]
detail = ["", "## Every bet", "", "| Meeting | Race | Horse | Open | Ours | Stake | Finish | BSP | P/L |", "|---|---|---|---|---|---|---|---|---|"]
T = collections.Counter(); clvs_all = []
for label, mid, pre, prices in MEETINGS:
    if not any(k[0] == mid and v[0] is not None for k, v in res.items()):
        lines.append(f"| {label} | results not stored yet | | | | | | |"); continue
    tmp = tempfile.mktemp(suffix=".csv"); tp = tempfile.mktemp(suffix=".txt")
    with open(tp, "w") as fo:  # strip trailing notes ("SCR  # scratched by ...") that paper_open cannot parse
        for l in open(f"{L}/{prices}"):
            if l.startswith("#"): fo.write(l); continue
            pa = [x.strip() for x in l.split("#")[0].split(",")]
            fo.write(", ".join(pa[:2] + ["SCR"]) + "\n" if "SCR" in [x.upper() for x in pa[2:]] else ", ".join(pa) + "\n")
    _r = subprocess.run([sys.executable, os.path.join(here, "paper_open.py"), f"{L}/{pre}-v6.json", tp, f"{L}/{pre}-angles.json", tmp, "",
                    f"{L}/{pre}-first-starters.json", f"{L}/{pre}-first-up-blocks.json"], check=False, capture_output=True); assert os.path.exists(tmp), (label, _r.stderr.decode()[-400:])
    seen = set(); n = w = 0; st_t = pl = flat = 0.0; clv = []
    for r in csv.DictReader(open(tmp)):
        if r["plan"] == "top_pick" or (r["race"], r["horse"]) in seen: continue
        seen.add((r["race"], r["horse"]))
        f, bsp = res.get((mid, int(r["race"]), norm(r["horse"])), (None, None))
        op, st = float(r["price"]), float(r["stake"])
        if f is None:  # scratched: refunded
            detail.append(f"| {label} | R{r['race']} | {r['horse']} | ${op:g} | ${float(r['model_price']):.2f} | {st:g}u | scratched | | 0 |"); continue
        won = f == 1; p = st * (op - 1) if won else -st
        n += 1; w += won; st_t += st; pl += p; flat += (op - 1) if won else -1
        if bsp: clv.append(op / bsp)
        detail.append(f"| {label} | R{r['race']} | {r['horse']} | ${op:g} | ${float(r['model_price']):.2f} | {st:g}u | {f} | {'$%.2f' % bsp if bsp else ''} | {p:+.2f} |")
    os.remove(tmp); os.remove(tp)
    clvs_all += clv
    T.update(n=n, w=w); T["st"] += st_t; T["pl"] += pl; T["flat"] += flat
    lines.append(f"| {label} | {n} | {w} | {st_t:.2f}u | {pl:+.2f}u | {flat:+.2f}u | {sum(clv)/len(clv) if clv else 0:.2f} | {sum(c > 1 for c in clv)}/{len(clv)} |")
roi = T["pl"] / T["st"] * 100 if T["st"] else 0
lines.append(f"| **Total** | **{T['n']}** | **{T['w']}** | **{T['st']:.2f}u** | **{T['pl']:+.2f}u ({roi:+.0f}%)** | **{T['flat']:+.2f}u** | "
             f"**{sum(clvs_all)/len(clvs_all) if clvs_all else 0:.2f}** | **{sum(c > 1 for c in clvs_all)}/{len(clvs_all)}** |")
open(out_p, "w").write("\n".join(lines + detail) + "\n")
print("\n".join(lines))
