"""THE 9AM BETS (founder, 18 Nov 2026: "Bet the new version from tomorrow at $50 units", then "yes, open book units from
tomorrow"). From Thu 19 Nov this is the list the founder bets at 9am, himself, at the best price; nothing on it goes to
BetMatic, and it is kept off the account BetMatic uses for the open book (these horses shorten by the jump 63% of the
time, the pattern that gets an account limited). blend_9am.py's list is still made and shown, for the record.

What the research found (night/RESEARCH_2026-11-18.md, the clean test: night/r9/m_exact.py and n_bsp.py, Victoria
Jul 2025 - Nov 2026, exact scratching times from Betwatch, races with a whole 9am book only):
  - about one horse in 14 races; 330 horses, 94 won where Betfair SP expected 75;
  - at the open book's units (below), one bet a horse at the best 9am price: $39,722 staked, +$20,927 (+53%), worst
    drawdown 65u, 13 of 17 months up; the same horses at Betfair SP after commission +24%. The 9am price beats BSP by only
    1.03x, so most of that is the horses out-running BSP: expect break-even to +20%, not +53%;
  - no split of the list held up when the test was cleaned, so it carries no grade: "also_on_live_list" is a fact.
Rule: log p = 0.267 log(ours) + 0.903 log(1 / average price now) - 0.215 log(average price now / opening price),
renormalised over the race's runners with a price (at least 4); fair price $1.60-$15; first starters and scratched
runners out; listed when the BEST price now is at least 1.05x the fair price.
STAKE: the open book's units (stake_rule.py: Kelly x125, x5/8, capped at 10u, $50 a unit), on this list's own edge:
units = min(10, 78.125 x (best / fair - 1) / (best - 1)), at the best price; one bet a horse. A lower price still at or
above the take price is a smaller edge, so "units at take" says what the stake falls to at the take price.
THE WHOLE-BOOK GUARD: a race whose average prices add to under 1.18 of a book (usual 1.33, never under 1.23 in our own
pulls) is left off and named: its prices pre-date a scratching, every runner reads as over the odds and a bet carries
the deduction. Those races were 222 of the first test's bets and a third of its profit.
    python3.13 blend_9am_v2.py PREFIX TAG FLUC.md      (FLUC.md: scripts/fluc_meeting.py output from the morning run)
Writes data/live_bets/PREFIX-9am-v2.csv and prints the table."""
import csv, io, json, math, os, re, sys
here = os.path.dirname(os.path.abspath(__file__)); L = os.path.join(here, "../../data/live_bets")
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
W_OURS, W_MKT, W_MOVE, TAKE = 0.267, 0.903, -0.215, 1.05          # night/r9/f_live.py, the final fit on 17 months
KELLY_UNITS, MAX_UNITS, UNIT = 125 * 5 / 8, 10.0, 50.0              # the open book's units (stake_rule.py), $50 a unit
units_at = lambda fair, price: round(min(MAX_UNITS, KELLY_UNITS * max(0.0, price / fair - 1) / (price - 1)), 2) if price > 1 else 0.0
pre, tag, fluc = sys.argv[1:4]
venue = pre[11:].replace("-", " ").title()
lim = 2000.0 if pre[11:].split("-")[0] in ("flemington", "caulfield", "moonee", "sandown") else 1000.0
s = open(fluc).read(); a = s.find("CSV-BEGIN") + 9; b = s.find("CSV-END")
mk = {}
for r in csv.DictReader(io.StringIO(s[a:b].strip())):
    try:
        if r["scratched"] == "1" or not r["avg_now"] or float(r["avg_now"]) <= 1: continue
        mk[(int(r["race"]), norm(r["name"]))] = dict(avg=float(r["avg_now"]), best=float(r["best_now"] or r["avg_now"]),
                                                    open=float(r["open"]) if r["open"] and float(r["open"]) > 1 else None, num=r["number"],
                                                    bookies=(r.get("best_bookies") or "").replace(",", " /"))
    except ValueError:
        continue
v6 = json.load(open(f"{L}/{pre}-{tag}-v6.json"))
fs = set()
if os.path.exists(f"{L}/{pre}-{tag}-first-starters.json"):
    x = json.load(open(f"{L}/{pre}-{tag}-first-starters.json")); fs = {norm(str(h).split("|")[-1]) for h in (x if isinstance(x, list) else x.keys())}
by = {}
for r in v6: by.setdefault(int(r["race"]), []).append(r)
book = {}
for (rc_, _), m_ in mk.items(): book[rc_] = book.get(rc_, 0.0) + 1 / m_["avg"]
rows = []; short = []
for rc, rs in sorted(by.items()):
    pr = [r for r in rs if r["p"] > 0 and (rc, norm(r["horse"])) in mk]
    if len(pr) < 4: continue
    if book.get(rc, 9.0) < 1.18:
        short.append(f"R{rc} ({book[rc]:.2f})"); continue
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
                         take_at_or_above=f"{TAKE * fair:.2f}", also_on_live_list="yes" if on_live else "no", best_bookies=m["bookies"],
                         stake_units=f"{units_at(fair, m['best']):.2f}", stake_dollars=f"{UNIT * units_at(fair, m['best']):.0f}",
                         units_at_take=f"{units_at(fair, TAKE * fair):.2f}"))
out = f"{L}/{pre}-9am-v2.csv"
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["date", "venue", "race", "number", "horse", "our_price", "avg_now", "open", "fair_price", "best_now", "take_at_or_above", "also_on_live_list", "best_bookies", "stake_units", "stake_dollars", "units_at_take"])
    w.writeheader(); w.writerows(rows)
print(f"THE 9AM BETS: {out}: {len(rows)} horses ({sum(r['also_on_live_list'] == 'yes' for r in rows)} also on the live list)"
      + (f"; LEFT OFF, the book is short (prices pre-date a scratching): {', '.join(short)}" if short else ""))
for r in rows:
    print(f"  R{r['race']} #{r['number']} {r['horse']}: ours ${r['our_price']}, average now ${r['avg_now']}, open ${r['open'] or '-'}, fair ${r['fair_price']}, "
          f"best now ${r['best_now']} ({r['best_bookies'] or '?'}), take at ${r['take_at_or_above']}+, {r['stake_units']}u (${r['stake_dollars']}) at the best price, "
          f"{r['units_at_take']}u at the take price" + (" (also on the live list)" if r["also_on_live_list"] == "yes" else ""))
