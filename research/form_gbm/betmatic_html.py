"""Put the BetMatic book for one meeting at the top of its market sheet (13 Oct 2026, founder: "update our artifact so
I can follow along"; the BetMatic standard in data/live_bets/TIPPING_RULES.md).

    python betmatic_html.py ORDERS.csv DAYPREFIX PAGE.html [--results RESULTS.txt]

Reads the pre-open order file (betmatic_orders.py) and the prices file, works out which orders filled at Form King's
open, and writes a "BetMatic" section into PAGE.html above the opening-price table: per horse the orders filled, the
price, the stake, the race's scratching deduction (deductions.py) and the price after it, the price now, and with
--results the result and P/L. Replaces an earlier BetMatic section, so it can be re-run every refresh.
"""
import argparse, csv, html, os, re, sys, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
from opens import parse_opens
from deductions import race_deductions
L = os.path.join(here, "../../data/live_bets")
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
START, END = "<!-- betmatic -->", "<!-- /betmatic -->"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("orders"); ap.add_argument("prefix"); ap.add_argument("page"); ap.add_argument("--results")
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
    ded = race_deductions(a.prefix)[0]
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
    rows, tot, pl = [], 0.0, 0.0
    for k, b in sorted(by.items(), key=lambda x: x[1]["race"]):
        d = ded.get(b["race"], 0.0); eff = 1 + (b["open"] - 1) * (1 - d); tot += b["stake"]
        res = ""
        if k in won:
            p = b["stake"] * (eff - 1) if won[k] else -b["stake"]; pl += p
            res = f"{'WON' if won[k] else 'lost'} {p:+.2f}u"
        rows.append(f"<tr><td><a href='#r{b['race']}'>R{b['race']}</a></td><td>{html.escape(b['horse'])}</td><td>{b['n']} of {counts[k]}</td>"
                    f"<td>${b['open']:.2f}</td><td>{b['stake']:.2f}u</td><td>{round(d * 100)}c</td><td>${eff:.2f}</td>"
                    f"<td>{'$%.2f' % b['now'] if b['now'] else 'SCR'}</td><td>{res}</td></tr>")
    body = ("<table><tr><th>Race</th><th>Horse</th><th>Orders filled</th><th>Got on at</th><th>Stake</th><th>Deduction</th>"
            "<th>After deduction</th><th>Now</th><th>Result</th></tr>" + "".join(rows) + "</table>") if rows else "<div>None.</div>"
    n_orders = sum(counts.values())
    sec = (f"{START}<h2>Filled at the open ({len(rows)})</h2><div class='tw'>{body}</div>"
           f"<div style='height:14px'></div>{END}")  # no notes on the page (founder, 24 Oct 2026)
    page = open(a.page).read()
    page = re.sub(re.escape(START) + ".*?" + re.escape(END), "", page, flags=re.S)
    i = page.find("<h2>Bets at the opening price")
    page = page[:i] + sec + page[i:] if i >= 0 else page.replace("</h1>", "</h1>" + sec, 1)
    open(a.page, "w").write(page)
    print(f"{a.page}: BetMatic section, {len(rows)} horses filled, {tot:.2f}u")


if __name__ == "__main__":
    main()
