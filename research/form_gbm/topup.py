"""Race-morning top-ups (14 Oct 2026, founder: "track this from now on, re price at 9:30am after scratchings and assess if
a top up works on a small sample"). Paper only: the backtest (t_topup.py) found the top-up slice loses, so this is a
live tracking sample, not a rule.

    python topup.py DAYPREFIX GTAG [--orders ORDERS.csv] [--out OUT.csv]

Needs the race-morning prices file (DAYPREFIX-prices.txt, taken after scratchings) and the sheet re-priced on that
final field (DAYPREFIX-GTAG-v6.json: our chance blended with every starter's open). For every runner that is value at
its OPENING price on the final field (open >= 1.2 / our chance, ours $1.60-$15, open under 3x ours), the full sheet stake
at the race-morning price is worked out, IF that price is still at or over take-at. The top-up is that stake less what
the BetMatic orders already got at the open (betmatic_orders.py file; 0 for a horse they missed). Written to
DAYPREFIX-topups.csv for settling with the results (no deduction: struck after the scratchings).
"""
import argparse, csv, json, os, re, sys
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import stake_rule
from opens import parse_opens
L = os.path.join(here, "../../data/live_bets")
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("prefix"); ap.add_argument("gtag"); ap.add_argument("--orders"); ap.add_argument("--out")
    a = ap.parse_args()
    orders = a.orders or f"{L}/{a.prefix}-betmatic-preopen.csv"; out = a.out or f"{L}/{a.prefix}-topups.csv"
    px = {}
    for l in open(f"{L}/{a.prefix}-prices.txt"):
        pa = [x.strip() for x in l.split("#")[0].split(",")]
        if len(pa) >= 3 and pa[0].isdigit() and not pa[2].upper().startswith("SCR"):
            fk, tab = parse_opens(", ".join(pa[3:])); px[(int(pa[0]), norm(pa[1]))] = (float(pa[2]), fk or tab)
    got = {}
    if os.path.exists(orders):
        for o in csv.DictReader(open(orders)):
            k = (int(o["race"]), norm(o["horse"]))
            if k in px and px[k][1] and px[k][1] >= float(o["min_odds"]):
                got[k] = got.get(k, 0.0) + float(o["stake_units"])
    v = json.load(open(f"{L}/{a.prefix}-{a.gtag}-v6.json"))
    field = {}
    for r in v: field[int(r["race"])] = field.get(int(r["race"]), 0) + 1
    B = f"{L}/{a.prefix}-{a.gtag}"
    fs = set(json.load(open(f"{B}-first-starters.json"))) if os.path.exists(f"{B}-first-starters.json") else set()
    fu = json.load(open(f"{B}-first-up-blocks.json")) if os.path.exists(f"{B}-first-up-blocks.json") else {}
    rows = []
    for r in v:
        k = (int(r["race"]), norm(r["horse"])); hk = f"{int(r['race'])}|{r['horse']}"
        if k not in px or not px[k][1]: continue
        if hk in fs or (fu.get(hk) and not fu[hk].startswith("EARLY")): continue   # the sheet's own blocks
        now, op = px[k]; ours = 1 / r["p"]; take = 1.2 * ours
        if not (1.6 <= ours <= 15 and op >= take and op < 3 * ours): continue
        s0 = got.get(k, 0.0)
        full = stake_rule.stake(r["p"], now, r.get("only_ride", False), field[k[0]]) if now >= take else 0.0
        top = round(max(0.0, full - s0), 2)
        rows.append(dict(race=k[0], horse=r["horse"], open=op, ours_now=round(ours, 2), take_at=round(take, 2), price_now=now,
                         betmatic_stake=round(s0, 2), full_stake_now=full, topup=top,
                         note="top up" if top > 0 else ("under take-at now" if now < take else "already at full stake")))
    rows.sort(key=lambda x: x["race"])
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["race"]); w.writeheader(); w.writerows(rows)
    n = sum(1 for x in rows if x["topup"] > 0)
    print(f"{out}: {len(rows)} value-at-open runners on the final field, {n} top-ups, {sum(x['topup'] for x in rows):.2f}u")
    for x in rows:
        print(f"R{x['race']} {x['horse']:20s} open ${x['open']} ours now ${x['ours_now']} take ${x['take_at']} now ${x['price_now']} "
              f"BetMatic {x['betmatic_stake']}u full {x['full_stake_now']}u -> {x['note']} {x['topup'] if x['topup'] else ''}")


if __name__ == "__main__":
    main()
