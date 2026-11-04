"""Put the order sheet's own minimum on every runner of a meeting page, so the page's "take at" carries ALL the rules.
5 Nov 2026, founder (on Feroce, whose page line said "take at $5.96 or better" while the sheet needed $7.00): "why isn't
the take at with ALL the rules". The old line was our page price + 20%, a leftover from the first market sheet; the
sheet asks for more (the blend with the market, the 1.15 edge under $4, the metro fix, the caps, first starters and the
first-up rule). Now:
  on the sheet      -> "take at $7.00 to $12.00"  (its lowest min_odds and highest max_odds, straight from the orders)
  never bet         -> "not a bet: <reason>"      (betmatic_orders.live_minimum's reason: first starter, first-up, band)
  minimum over cap  -> "not a bet at any price (needs $X, the cap is $Y)"
  already taken     -> "taken at the open, $2.50, 4.92u"  (the pre-open sheet's fills at Form King's open)
Both prices are the TAB price before any scratching deduction.
    python page_takeat.py PAGE.html ORDERS-ALL.csv DAYPREFIX GTAG
Run after betmatic_orders.py (pricemtg.sh does). Idempotent: a page already done is redone from the current sheet."""
import csv, html, json, re, sys
import betmatic_orders as bo

page, orders, prefix, gtag = sys.argv[1:5]
B = f"{bo.L}/{prefix}-{gtag}"
nm = lambda x: re.sub(r"[^a-z0-9]", "", html.unescape(x).lower())
is_metro = prefix[11:].replace("-", " ").lower() in bo.METRO

on = {}
for r in csv.DictReader(open(orders)):
    k = (int(r["race"]), nm(r["horse"]))
    lo, hi = on.get(k, (1e9, 0.0))
    on[k] = (min(lo, float(r["min_odds"])), max(hi, float(r["max_odds"])))

v = json.load(open(f"{B}-v6.json"))
tot = {}
for r in v:
    tot[int(r["race"])] = tot.get(int(r["race"]), 0.0) + r.get("p_model", r["p"])
fs = set(json.load(open(f"{B}-first-starters.json"))); fu = json.load(open(f"{B}-first-up-blocks.json"))
why = {}
for r in v:
    rc = int(r["race"]); pm = r.get("p_model", r["p"]) / tot[rc]; k = f"{rc}|{r['horse']}"
    lm = bo.live_minimum(pm, fu.get(k, ""), k in fs, is_metro)
    if lm["skip"]:
        why[(rc, nm(r["horse"]))] = f"not a bet: {lm['skip']}"
    else:
        need = min(lm["min_short"], lm["min_odds"])
        why[(rc, nm(r["horse"]))] = f"not a bet at any price (needs ${need:.2f}, the cap is ${lm['cap']:.2f})"

# A horse already TAKEN at the open (the pre-open sheet of record filled at Form King's opening price, the same rule as
# betmatic_html.py: an order fires only inside min_odds..max_odds) says so instead: the line is for new bets, and a bet
# taken is never dropped (founder, 5 Nov 2026, on Sass Appeal reading "not a bet": "we already took Sass Appeal").
from opens import parse_opens
taken = {}
sheet = f"{bo.L}/{prefix}-betmatic-preopen.csv"
try:
    opn = {}
    for l in open(f"{bo.L}/{prefix}-prices.txt"):
        pa = [x.strip() for x in l.split("#")[0].split(",")]
        if len(pa) >= 3 and pa[0].isdigit() and not pa[2].upper().startswith("SCR"):
            fk, tab = parse_opens(", ".join(pa[3:]))
            if fk or tab:
                opn[(int(pa[0]), nm(pa[1]))] = fk or tab
    for o in csv.DictReader(open(sheet)):
        k = (int(o["race"]), nm(o["horse"])); op = opn.get(k)
        if op is not None and float(o["min_odds"]) <= op and (not o.get("max_odds") or op <= float(o["max_odds"])):
            taken[k] = (op, taken.get(k, (op, 0.0))[1] + float(o["stake_units"]))
except FileNotFoundError:
    pass   # no sheet of record yet (priced before the market): nothing taken

s = open(page).read()
TA = re.compile(r"<span class='ta'>.*?</span>|take at \$[\d,.]+ or better")
parts = re.split(r"(<h2 id='r\d+'>|<div class='r'>)", s)
race, done, miss = 0, 0, []
for i, p in enumerate(parts):
    m = re.match(r"<h2 id='r(\d+)'>", p)
    if m:
        race = int(m.group(1)); continue
    if i == 0 or parts[i - 1] != "<div class='r'>":
        continue
    n = re.search(r"<span class='nm'>(.*?)</span>", p)
    if not n or not TA.search(p):
        continue
    k = (race, nm(n.group(1)))
    if k in taken:
        op, u = taken[k]; txt = f"taken at the open, ${op:.2f}, {u:.2f}u"
    elif k in on:
        lo, hi = on[k]; txt = f"take at ${lo:.2f} to ${hi:.2f}"
    else:
        txt = why.get(k)
        if txt is None:
            miss.append(f"R{race} {html.unescape(n.group(1))}"); continue
    parts[i] = TA.sub(lambda _: f"<span class='ta'>{html.escape(txt)}</span>", p, count=1); done += 1
open(page, "w").write("".join(parts))
print(f"{page}: take-at from the order sheet on {done} runners ({sum(1 for k in on)} on the sheet)"
      + (f"; not in the model file, left as they were: {', '.join(miss)}" if miss else ""))
