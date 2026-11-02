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
price after it, "not reported" for a race holding a scratching with no figure, and with --ours V6.json our price now
from a re-price on the current field. Settlement (--results) is unchanged: at the price taken.
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
    ap.add_argument("--ours", help="v6 json re-priced on the current field: our price now")
    ap.add_argument("--since", help="an earlier prices file: a race with a scratching since it says so beside its deduction")
    ap.add_argument("--unit", type=float, default=37.5, help="dollars a unit, to show real bets in units")
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
    ours = {}
    if a.ours:
        v = json.load(open(a.ours)); tot_ = collections.Counter()
        for r in v: tot_[int(r["race"])] += r["p"]
        ours = {(int(r["race"]), norm(r["horse"])): tot_[int(r["race"])] / r["p"] for r in v if r["p"] > 0}
    # real bets: every placement BetMatic reports for the day (one row per bet, de-duplicated by its id)
    real, seen = [], set()
    for f in sorted(glob.glob(f"{L}/{a.prefix}*-placed.jsonl")):
        for l in open(f):
            d = json.loads(l)
            for r in d.get("records", []):
                if r.get("submit_result") != "Success" or r["id"] in seen:
                    continue
                seen.add(r["id"])
                m = re.search(r"-r(\d+)-", d.get("label", "")); rc = int(m[1]) if m else None
                real.append(dict(race=rc, amount=float(r["amount"]), price=float(r["current_odds"]), label=d.get("label", "")))
    lg = {}   # label -> horse, from the ledgers
    for f in glob.glob(f"{L}/{a.prefix}*-ledger.csv"):
        for r in csv.DictReader(open(f)):
            lg[r["label"]] = (int(r["race"]), r["horse"])
    lines = [(b["race"], b["horse"], "paper, at the open", b["open"], b["stake"], f"{b['stake']:.2f}u", k) for k, b in by.items()]
    for r in real:
        rc, hz = lg.get(r["label"], (r["race"], "?"))
        u = r["amount"] / a.unit
        lines.append((rc, hz, "REAL", r["price"], u, f"${r['amount']:,.0f} ({u:.2f}u)", (rc, norm(hz))))
    rows, tot, pl = [], 0.0, 0.0
    for rc, hz, kind, price, st, st_txt, k in sorted(lines, key=lambda x: (x[0] or 0, x[1], x[2] != "REAL")):
        d = rep.get(rc)
        dtxt = f"{100 * d:g}c" if d is not None else ("not reported" if rc in scr_races else "none")
        if rc in late:
            dtxt += (" + a late scratching, not reported" if d is not None else ", late scratching")
        eff = 1 + (price - 1) * (1 - d) if d else price
        if kind != "REAL": tot += st
        res = ""
        if k in won:
            p = st * (price - 1) if won[k] else -st; pl += p
            res = f"{'WON' if won[k] else 'lost'} {p:+.2f}u"
        now = px.get(k, (None, None, True))[0]; on = ours.get(k)
        rows.append(f"<tr><td><a href='#r{rc}'>R{rc}</a></td><td>{html.escape(hz)}</td><td>{kind}</td>"
                    f"<td>${price:.2f}</td><td>{st_txt}</td><td>{dtxt}</td><td>${eff:.2f}</td>"
                    f"<td>{'$%.2f' % on if on else '-'}</td><td>{'$%.2f' % now if now else 'SCR'}</td><td>{res}</td></tr>")
    body = ("<table><tr><th>Race</th><th>Horse</th><th>Bet</th><th>Got on at</th><th>Stake</th><th>Deduction</th>"
            "<th>After deduction</th><th>Our price now</th><th>Price now</th><th>Result</th></tr>" + "".join(rows) + "</table>") if rows else "<div>None.</div>"
    n_orders = sum(counts.values())
    sec = (f"{START}<h2>Our bets ({len(rows)})</h2><div class='tw'>{body}</div>"
           f"<div style='height:14px'></div>{END}")  # no notes on the page (founder, 24 Oct 2026)
    page = open(a.page).read()
    page = re.sub(re.escape(START) + ".*?" + re.escape(END), "", page, flags=re.S)
    i = page.find("<h2>Bets at the opening price")
    page = page[:i] + sec + page[i:] if i >= 0 else page.replace("</h1>", "</h1>" + sec, 1)
    open(a.page, "w").write(page)
    print(f"{a.page}: BetMatic section, {len(rows)} horses filled, {tot:.2f}u")


if __name__ == "__main__":
    main()
