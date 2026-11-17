"""The 9am list, second version, SHADOW ONLY (18 Nov 2026 research, night/README.md "18 Nov"; nothing here is the
founder's list until he says so: blend_9am.py is still the list that is pushed and bet).

What the research found on 13 test months with late scratchings handled properly (night/r9/):
  - our price carries weight at 9am (about 0.27), the market's average carries most (0.90), and the MOVE since the
    open carries real information the 9am price has not finished pricing (-0.215: a horse that has firmed since the
    open wins more often than its 9am price says, a drifter less; t about 3 on 3,800 races);
  - a runner on BOTH lists (the live blend on the best price, and this one) made +64% on 407 bookie bets; a runner on
    one list only made about +12%.
Rule: log p = 0.267 log(ours) + 0.903 log(1 / average price now) - 0.215 log(average price now / opening price),
renormalised over the race's runners with a price (at least 4); fair price $1.60-$15; first starters and scratched
runners out; listed when the BEST price now is at least 1.05x the fair price. Stake to win $1,000 a bookie ($2,000 metro).
Grade A = also on the live list (blend_9am.py's rule), B = this list only.
    python3.13 blend_9am_v2.py PREFIX TAG FLUC.md      (FLUC.md: scripts/fluc_meeting.py output from the morning run)
Writes data/live_bets/PREFIX-9am-v2.csv and prints the table."""
import csv, io, json, math, os, re, sys
here = os.path.dirname(os.path.abspath(__file__)); L = os.path.join(here, "../../data/live_bets")
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
W_OURS, W_MKT, W_MOVE, TAKE = 0.267, 0.903, -0.215, 1.05          # night/r9/f_live.py, the final fit on 17 months
pre, tag, fluc = sys.argv[1:4]
venue = pre[11:].replace("-", " ").title()
lim = 2000.0 if pre[11:].split("-")[0] in ("flemington", "caulfield", "moonee", "sandown") else 1000.0
s = open(fluc).read(); a = s.find("CSV-BEGIN") + 9; b = s.find("CSV-END")
mk = {}
for r in csv.DictReader(io.StringIO(s[a:b].strip())):
    try:
        if r["scratched"] == "1" or not r["avg_now"] or float(r["avg_now"]) <= 1: continue
        mk[(int(r["race"]), norm(r["name"]))] = dict(avg=float(r["avg_now"]), best=float(r["best_now"] or r["avg_now"]),
                                                    open=float(r["open"]) if r["open"] and float(r["open"]) > 1 else None, num=r["number"])
    except ValueError:
        continue
v6 = json.load(open(f"{L}/{pre}-{tag}-v6.json"))
fs = set()
if os.path.exists(f"{L}/{pre}-{tag}-first-starters.json"):
    x = json.load(open(f"{L}/{pre}-{tag}-first-starters.json")); fs = {norm(str(h).split("|")[-1]) for h in (x if isinstance(x, list) else x.keys())}
by = {}
for r in v6: by.setdefault(int(r["race"]), []).append(r)
rows = []
for rc, rs in sorted(by.items()):
    pr = [r for r in rs if r["p"] > 0 and (rc, norm(r["horse"])) in mk]
    if len(pr) < 4: continue
    tp = sum(r["p"] for r in pr)
    w2, w1 = {}, {}
    for r in pr:
        m = mk[(rc, norm(r["horse"]))]; mv = math.log(m["avg"] / m["open"]) if m["open"] else 0.0
        w2[norm(r["horse"])] = math.exp(W_OURS * math.log(r["p"] / tp) - W_MKT * math.log(m["avg"]) + W_MOVE * mv)
        w1[norm(r["horse"])] = math.exp(0.20 * math.log(r["p"] / tp) - 1.00 * math.log(m["best"]))     # the live list's blend
    s2, s1 = sum(w2.values()), sum(w1.values())
    for r in pr:
        k = norm(r["horse"]); m = mk[(rc, k)]; fair = s2 / w2[k]; live_bp = s1 / w1[k]
        if k in fs or not (1.6 <= fair <= 15) or m["best"] < TAKE * fair: continue
        on_live = (1.6 <= live_bp <= 15) and m["best"] >= 1.05 * live_bp
        rows.append(dict(date=pre[:10], venue=venue, race=rc, number=m["num"], horse=r["horse"], our_price=f"{tp / r['p']:.2f}",
                         avg_now=f"{m['avg']:.2f}", open=f"{m['open']:.2f}" if m["open"] else "", fair_price=f"{fair:.2f}", best_now=f"{m['best']:.2f}",
                         take_at_or_above=f"{TAKE * fair:.2f}", grade="A" if on_live else "B", to_win=f"{lim:.0f}", stake_at_best=f"{lim / (m['best'] - 1):.0f}"))
out = f"{L}/{pre}-9am-v2.csv"
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["date", "venue", "race", "number", "horse", "our_price", "avg_now", "open", "fair_price", "best_now", "take_at_or_above", "grade", "to_win", "stake_at_best"])
    w.writeheader(); w.writerows(rows)
print(f"9AM LIST v2 (shadow): {out}: {len(rows)} horses ({sum(r['grade'] == 'A' for r in rows)} also on the live list)")
for r in rows:
    print(f"  R{r['race']} #{r['number']} {r['horse']}: ours ${r['our_price']}, average now ${r['avg_now']}, open ${r['open'] or '-'}, fair ${r['fair_price']}, "
          f"best now ${r['best_now']}, take at ${r['take_at_or_above']}+ [{r['grade']}]")
