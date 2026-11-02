"""Put the BetMatic book for one meeting at the top of its market sheet (13 Oct 2026, founder: "update our artifact so
I can follow along"; the BetMatic standard in data/live_bets/TIPPING_RULES.md).

    python betmatic_html.py ORDERS.csv DAYPREFIX PAGE.html [--results RESULTS.txt]

Reads the pre-open order file (betmatic_orders.py) and the prices file, works out which orders filled at Form King's
open, and writes a "BetMatic" section into PAGE.html above the opening-price table: per horse the orders filled, the
price, the stake, the race's scratching deduction (deductions.py) and the price after it, the price now, and with
--results the result and P/L. Replaces an earlier BetMatic section, so it can be re-run every refresh.

2 Nov 2026 (founder: "up the top of our artifact, have it as what our bets are at open, deductions, our price now and
then what it is"): the box also carries the REAL bets BetMatic placed (every *-placed.jsonl for the day, amount and
price), TAB's deduction per race as the founder reported it (DAYPREFIX-deductions-actual.txt, "race, cents") and the
price after it (our price with deductions; founder, 2 Nov: "not our rated price but our price with deductions"),
"not in" for a race holding a scratching with no figure, and the price now. Units in their own column and a total;
open bets only, no top-ups (founder, 2 Nov). --results settles at our price with TAB's reported deductions.
"""
import argparse, csv, glob, html, json, os, re, sys, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
from opens import parse_opens
from deductions import race_deductions
L = os.path.join(here, "../../data/live_bets")
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
START, END = "<!-- betmatic -->", "<!-- /betmatic -->"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("orders"); ap.add_argument("prefix"); ap.add_argument("page"); ap.add_argument("--results")
    ap.add_argument("--since", help="an earlier prices file: a race with a scratching since it says so beside its deduction")
    ap.add_argument("--unit", type=float, default=50.0, help="dollars a unit, to show real bets in units")
    a = ap.parse_args()
    px = {}
    for l in open(f"{L}/{a.prefix}-prices.txt"):
        pa = [x.strip() for x in l.split("#")[0].split(",")]
        if len(pa) >= 3 and pa[0].isdigit():
            scr = pa[2].upper().startswith("SCR")
            fk, tab = (None, None) if scr else parse_opens(", ".join(pa[3:]))
            px[(int(pa[0]), norm(pa[1]))] = (None if scr else float(pa[2]), fk or tab, scr)
    won = {}
    if a.results:
        for l in open(a.results):
            m = re.match(r"R(\d+) (.+?)\s+finish (\S+)", l)
            if m: won[(int(m[1]), norm(m[2]))] = m[3] == "1"
    ded = {}   # deductions scrapped (founder, 1 Nov 2026: "Just completely scrap the deduction pay"): settle at the price taken
    by = collections.OrderedDict(); counts = collections.Counter()
    for o in csv.DictReader(open(a.orders)):
        k = (int(o["race"]), norm(o["horse"])); counts[k] += 1
        now, op, scr = px.get(k, (None, None, True))
        # an order fires only inside its band: min_odds <= open <= max_odds (BetMatic check_max_odds; 26 Oct 2026, the
        # one-step Lawborough order at $3.75-$3.99 was counted at a $4.40 open)
        if scr or op is None or op < float(o["min_odds"]) or (o.get("max_odds") and op > float(o["max_odds"])):
            continue
        b = by.setdefault(k, dict(race=int(o["race"]), horse=o["horse"], n=0, stake=0.0, open=op, now=now))
        b["n"] += 1; b["stake"] += float(o["stake_units"])
    # TAB's deductions as the founder reported them (no estimates); races holding a scratching with no figure say so
    rep = {}
    dfile = f"{L}/{a.prefix}-deductions-actual.txt"
    if os.path.exists(dfile):
        for l in open(dfile):
            pa = [x.strip() for x in l.split("#")[0].split(",")]
            if len(pa) >= 2 and pa[0].isdigit():
                rep[int(pa[0])] = float(pa[1]) / 100
    scr_races = {k[0] for k, (_, _, sc) in px.items() if sc}
    late = set()
    if a.since:
        before = set()
        for l in open(a.since):
            pa = [x.strip() for x in l.split("#")[0].split(",")]
            if len(pa) >= 3 and pa[0].isdigit() and pa[2].upper().startswith("SCR"):
                before.add((int(pa[0]), norm(pa[1])))
        late = {k[0] for k, (_, _, sc) in px.items() if sc and k not in before}
    # OPEN BETS ONLY (founder, 2 Nov 2026: "we aren't including top ups in there, its only the open"): the paper fills of
    # the order sheet at the open, and a real bet only when BetMatic placed it from THAT sheet (its ledger,
    # ORDERS-ledger.csv). After-open bets and top-ups are not on this table.
    real, seen = [], set()
    ledger = re.sub(r"\.csv$", "-ledger.csv", a.orders)
    lg = {}
    if os.path.exists(ledger):
        for r in csv.DictReader(open(ledger)):
            lg[r["label"]] = (int(r["race"]), r["horse"])
    placed = re.sub(r"\.csv$", "-placed.jsonl", a.orders)
    if os.path.exists(placed):
        for l in open(placed):
            d = json.loads(l)
            for r in d.get("records", []):
                if r.get("submit_result") != "Success" or r["id"] in seen or d.get("label") not in lg:
                    continue
                seen.add(r["id"])
                real.append(dict(amount=float(r["amount"]), price=float(r["current_odds"]), label=d["label"]))
    lines = [(b["race"], b["horse"], "paper", b["open"], b["stake"], k) for k, b in by.items()]
    for r in real:
        rc, hz = lg[r["label"]]
        lines.append((rc, hz, "real", r["price"], r["amount"] / a.unit, (rc, norm(hz))))
    money = lambda x: f"${x:.0f}" if abs(x - round(x)) < 0.005 else f"${x:.2f}"
    rows, tot, pl = [], 0.0, 0.0
    for rc, hz, kind, price, st, k in sorted(lines, key=lambda x: (x[0] or 0, x[1], x[2] != "real")):
        d = rep.get(rc)
        dtxt = f"{100 * d:g}c" if d is not None else ("?" if rc in scr_races else "-")
        if rc in late:
            dtxt += ("+" if d is not None else "")
        eff = 1 + (price - 1) * (1 - d) if d else price
        tot += st
        res = ""
        if k in won:
            p = st * (eff - 1) if won[k] else -st; pl += p
            res = f"<b style='color:{'#1b5e20' if won[k] else '#b71c1c'}'>{p:+.2f}u</b>"
        now = px.get(k, (None, None, True))[0]
        rows.append((f"<tr><td><a href='#r{rc}'>R{rc}</a> {html.escape(hz)}" + (" <span class='tag edge'>REAL</span>" if kind == "real" else "") +
                     f"</td><td><b>{st:.2f}u</b></td><td>{money(price)}</td><td>{dtxt}</td><td><b>{money(eff)}</b></td>"
                     f"<td>{res or (money(now) if now else 'SCR')}</td>", res))
    anyres = any(r for _, r in rows)
    rows = [h + "</tr>" for h, r in rows]   # a settled race shows its P/L in the last column instead of the price now
    nbet = len(rows)
    if rows:
        rows.append(f"<tr><td><b>Total</b></td><td><b>{tot:.2f}u</b></td><td colspan='3'></td><td>"
                    + (f"<b>{pl:+.2f}u</b>" if anyres else "") + "</td></tr>")
    body = ("<table><tr><th>Horse</th><th>Units</th><th>Got on</th><th>Ded.</th><th>Our price</th>"
            + ("<th>Now / P&amp;L</th>" if anyres else "<th>Now</th>") + "</tr>" + "".join(rows) + "</table>"
            "<div class='note'>Our price is what we got on at after TAB's deductions. ? = scratching in the race, TAB's deduction not in yet; "
            "+ = a later scratching, more to come.</div>") if rows else "<div>None.</div>"
    n_orders = sum(counts.values())
    sec = (f"{START}<style>.bets.ob td,.bets.ob th{{padding:6px 4px}}</style><div class='bets ob'><h2>Our bets at the open ({nbet})</h2><div class='tw'>{body}</div></div>{END}")  # no notes on the page (founder, 24 Oct 2026)
    page = open(a.page).read()
    page = re.sub(re.escape(START) + ".*?" + re.escape(END), "", page, flags=re.S)
    # the top bar's "Bets" button jumps to #bets; a page with no opening-price bets section has no such element, so this
    # box takes the id (2 Nov 2026, founder: "the bets tab isn't linked")
    if "id='bets'" not in page:
        sec = sec.replace("<div class='bets ob'>", "<div class='bets ob' id='bets' style='scroll-margin-top:64px'>", 1)
    i = page.find("<h2>Bets at the opening price")
    page = page[:i] + sec + page[i:] if i >= 0 else page.replace("</h1>", "</h1>" + sec, 1)
    open(a.page, "w").write(page)
    print(f"{a.page}: BetMatic section, {nbet} bets at the open, {tot:.2f}u")


if __name__ == "__main__":
    main()
