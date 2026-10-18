"""Which BetMatic orders would have filled at the open: a paper test of a pre-open order file (betmatic_orders.py).

    python betmatic_fills.py ORDERS.csv DAYPREFIX [--results RESULTS.txt]

An order fills when Form King's opening price (fk_open in DAYPREFIX-prices.txt) is at or over its minimum odds, at the
open. With --results (meeting_results.py output) the fills are settled: winnings less the race's scratching deduction
(deductions.py, measured from the saved price files), $100 a unit.
"""
import argparse, csv, os, re, sys
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
from opens import parse_opens
L = os.path.join(here, "../../data/live_bets")
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("orders"); ap.add_argument("prefix"); ap.add_argument("--results")
    a = ap.parse_args()
    opens = {}
    for l in open(f"{L}/{a.prefix}-prices.txt"):
        pa = [x.strip() for x in l.split("#")[0].split(",")]
        if len(pa) >= 3 and pa[0].isdigit() and not pa[2].upper().startswith("SCR"):
            fk, tab = parse_opens(", ".join(pa[3:]))
            opens[(int(pa[0]), norm(pa[1]))] = fk or tab
    won, ded = {}, {}
    if a.results:
        for l in open(a.results):
            m = re.match(r"R(\d+) (.+?)\s+finish (\S+)", l)
            if m:
                won[(int(m[1]), norm(m[2]))] = m[3] == "1"
        from deductions import race_deductions
        ded = race_deductions(a.prefix)[0]
    fills, staked, pl, missing = [], 0.0, 0.0, set()
    for o in csv.DictReader(open(a.orders)):
        k = (int(o["race"]), norm(o["horse"])); op = opens.get(k)
        if op is None:
            missing.add(o["race"]); continue
        if op >= float(o["min_odds"]):
            st = float(o["stake_units"]); staked += st
            res = ""
            if k in won:
                d = ded.get(int(o["race"]), 0.0)
                p = st * (op - 1) * (1 - d) if won[k] else -st; pl += p; res = f"{'WON' if won[k] else 'lost'} {p:+.2f}u"
            fills.append((o["race"], o["horse"], o["order"], o["min_odds"], op, st, res))
    for f in fills:
        print(f"R{f[0]} {f[1]:20s} order {f[2]:7s} min ${f[3]:>6s} opened ${f[4]:<6} {f[5]:.2f}u {f[6]}")
    print(f"{len(fills)} orders filled, {staked:.2f}u" + (f", P/L {pl:+.2f}u" if won else "")
          + (f"; no open yet in races {sorted(missing, key=int)}" if missing else ""))


if __name__ == "__main__":
    main()
