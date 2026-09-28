"""Record the bets each plan takes at the prices the user could actually get.

    python scripts/record_bets.py data/live_bets/2026-09-30-ballarat-model.json prices.txt data/live_bets/2026-09-30-ballarat-bets.csv

prices.txt: one runner per line, "race, horse, price[, price now]" (e.g. "6, High Falls, 9.50, 8.00"):
the price is the one the user could take (the opening price); the optional second is the price at
the time, kept for the record. "race, horse, SCR" marks a scratching: each race's chances are rescaled
over the runners that remain. A runner simply missing from the file stays in the race, unbet.
Plans, each at the user's price:
  top_pick     the model's top pick, 1 unit
  value_20c    chance x price > 1.20, 1 unit
  kelly_q_5c   chance x price > 1.05, quarter Kelly on a 100-unit bank, capped at 5 units
Guards on the value plans: model price under $50, and the price under three times the model price.
"""
import csv
import json
import re
import sys


def norm(name: str) -> str:
    """Horse names compared without punctuation or case: Lollie's Galore = Lollies Galore."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def main() -> None:
    model_path, prices_path, out = sys.argv[1:4]
    rows = json.load(open(model_path))
    prices, now, scr = {}, {}, set()
    for line in open(prices_path):
        parts = [x.strip() for x in line.split(",")]
        if len(parts) >= 3 and parts[0].isdigit():
            key = (int(parts[0]), norm(parts[1]))
            if parts[2].upper() == "SCR":
                scr.add(key)
                continue
            prices[key] = float(parts[2].replace("$", ""))
            if len(parts) >= 4 and parts[3]:
                now[key] = float(parts[3].replace("$", ""))
    bets = []
    for rn in sorted({r["race"] for r in rows}):
        field = [r for r in rows if r["race"] == rn and (rn, norm(r["horse"])) not in scr]
        if not any((rn, norm(r["horse"])) in prices for r in field):
            continue
        tot = sum(r["p"] for r in field)
        for r in field:
            r["pp"] = r["p"] / tot
        top = max(field, key=lambda r: r["pp"])
        for r in [r for r in field if (rn, norm(r["horse"])) in prices]:
            price = prices[(rn, norm(r["horse"]))]
            fair = 1 / r["pp"]
            ev = r["pp"] * price - 1
            ok = fair < 50 and price < 3 * fair
            plans = []
            if r is top:
                plans.append(("top_pick", 1.0))
            if ok and ev > 0.20:
                plans.append(("value_20c", 1.0))
            if ok and ev > 0.05:
                plans.append(("kelly_q_5c", min(5.0, 25 * ev / (price - 1))))
            for plan, stake in plans:
                bets.append(dict(race=rn, race_id=r["race_id"], horse=r["horse"], plan=plan, price=price,
                                 price_now=now.get((rn, norm(r["horse"])), ""),
                                 model_price=round(fair, 2), value=round(ev, 3), stake=round(stake, 2), result="", returned=""))
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(bets[0].keys()))
        w.writeheader()
        w.writerows(bets)
    for b in bets:
        print(f"R{b['race']} {b['horse']:22s} {b['plan']:11s} {b['stake']:4.2f}u at ${b['price']:.2f} (model ${b['model_price']:.2f}, value {b['value']:+.0%})")
    missing = [r["horse"] for r in rows if (r["race"], norm(r["horse"])) not in prices and (r["race"], norm(r["horse"])) not in scr
               and any(k[0] == r["race"] for k in prices)]
    print(f"{len(bets)} bets; no price given (left in the race, unbet): {', '.join(missing) or 'none'}; scratched: {len(scr)}")


if __name__ == "__main__":
    main()
