"""Record the bets each plan takes at the prices the user could actually get.

    python scripts/record_bets.py data/live_bets/2026-09-30-ballarat-model.json prices.txt data/live_bets/2026-09-30-ballarat-bets.csv

prices.txt: one runner per line, "race, horse, price" (e.g. "6, High Falls, 9.50"). A runner the
model priced but the prices file leaves out is taken as scratched, and each race's chances are
rescaled over the runners that remain.
Plans, each at the user's price:
  top_pick     the model's top pick, 1 unit
  value_20c    chance x price > 1.20, 1 unit
  kelly_q_5c   chance x price > 1.05, quarter Kelly on a 100-unit bank, capped at 5 units
Guards on the value plans: model price under $50, and the price under three times the model price.
"""
import csv
import json
import sys


def main() -> None:
    model_path, prices_path, out = sys.argv[1:4]
    rows = json.load(open(model_path))
    prices = {}
    for line in open(prices_path):
        parts = [x.strip() for x in line.split(",")]
        if len(parts) >= 3 and parts[0].isdigit():
            prices[(int(parts[0]), parts[1].lower())] = float(parts[2].replace("$", ""))
    bets = []
    for rn in sorted({r["race"] for r in rows}):
        rs = [r for r in rows if r["race"] == rn and (rn, r["horse"].lower()) in prices]
        if not rs:
            continue
        tot = sum(r["p"] for r in rs)
        for r in rs:
            r["pp"] = r["p"] / tot
        top = max(rs, key=lambda r: r["pp"])
        for r in rs:
            price = prices[(rn, r["horse"].lower())]
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
                                 model_price=round(fair, 2), value=round(ev, 3), stake=round(stake, 2), result="", returned=""))
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(bets[0].keys()))
        w.writeheader()
        w.writerows(bets)
    for b in bets:
        print(f"R{b['race']} {b['horse']:22s} {b['plan']:11s} {b['stake']:4.2f}u at ${b['price']:.2f} (model ${b['model_price']:.2f}, value {b['value']:+.0%})")
    missing = [r["horse"] for r in rows if (r["race"], r["horse"].lower()) not in prices]
    print(f"{len(bets)} bets; not in the prices (treated as scratched): {', '.join(missing) or 'none'}")


if __name__ == "__main__":
    main()
