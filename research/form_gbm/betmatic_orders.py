"""BetMatic order file for a meeting (13 Oct 2026; tested in t_betmatic.py).

    python betmatic_orders.py DAYPREFIX GTAG OUT.csv [--times "1=3:00pm,2=3:30pm,..."] [--after-open]

BEFORE THE MARKET (default): every runner the live rules could bet, priced on our model alone, gets a minimum odds
    min odds = 0.95 x (1.2 / p_model^0.82)^(1/0.78)
(the blend with the open, worked backwards, shaded 5%: t_betmatic.py found 5% recovers most of the bets the unshaded
formula misses without letting weak ones in) and a stake in up to eight price steps (the minimum x1 to x2), so the stake grows with the
price the market opens at: each step its own order carrying the extra stake the live stake rule (stake_rule.py)
gives at the next step's price, with our chance at that open taken from the same blend.
Filters: our price $1.60-$15, no first starters, no first-up/bounce blocks, EARLY-only runners only at $8 or shorter,
and nothing at 3x our price or more. The race-level first-starter rule (no bets in a race where a first starter opens
$6 or shorter) needs the market, so it cannot be in a pre-open order: check it when the market is up.

AFTER THE OPEN (--after-open): only the bets that were value at the opening price on the sheet's exact blend
(DAYPREFIX-GTAG-open-bets.csv, from open_book.py), with the sheet's take-at as the minimum and the same tiers. A horse
that was not value at the open never gets an order, so drift-made value cannot fire one.
"""
import argparse, csv, json, os, sys
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import stake_rule
L = os.path.join(here, "../../data/live_bets")
SHADE, TIERS = 0.95, (1.0, 1.25, 1.5)   # 14 Oct: 3 steps sized at the next step: same holdout profit as 8 (+801u), at most 3 bets a horse (t_monthly.py)


def tiers(min_odds, cap, chance_at, only_ride, field):
    """[(price, extra stake, total stake)]: each step adds what the stake rule gives at the NEXT step's price over the
    steps before it, so a horse opening anywhere in a step is staked as if at the top of it (14 Oct 2026,
    t_betmatic_tiers.py: 8 steps sized this way made 18% more on the holdout than 3 steps sized at their own price,
    at the same ROI). The last step is sized at its own price."""
    ts = [round(min_odds * m, 2) for m in TIERS if min_odds * m < cap]
    out, prev = [], 0.0
    for k, t in enumerate(ts):
        tp = ts[k + 1] if k + 1 < len(ts) else t
        s = stake_rule.stake(chance_at(tp), tp, only_ride, field)
        if s - prev >= 0.01:
            out.append((t, round(s - prev, 2), s)); prev = s
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix"); ap.add_argument("gtag"); ap.add_argument("out")
    ap.add_argument("--times", default=""); ap.add_argument("--after-open", action="store_true")
    ap.add_argument("--v6", help="price file to use instead of DAYPREFIX-GTAG-v6.json (e.g. the version priced before the market)")
    ap.add_argument("--numbers", help="entry_numbers.py output (race|number|name|emergency|scratched): adds the saddlecloth "
                                      "number BetMatic bets on (default DAYPREFIX-entry-numbers.txt if it exists)")
    a = ap.parse_args()
    B = f"{L}/{a.prefix}-{a.gtag}"
    times = dict(x.split("=", 1) for x in a.times.split(",") if "=" in x)
    v = json.load(open(a.v6 or f"{B}-v6.json"))
    field = {}
    for r in v:
        field[int(r["race"])] = field.get(int(r["race"]), 0) + 1
    date, venue = a.prefix[:10], a.prefix[11:].replace("-", " ").title()
    import re
    nm = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
    nums_fn = a.numbers or (f"{L}/{a.prefix}-entry-numbers.txt" if os.path.exists(f"{L}/{a.prefix}-entry-numbers.txt") else None)
    numbers = {}
    if nums_fn:
        for l in open(nums_fn):
            pa = l.strip().split("|")
            if len(pa) == 5 and pa[0].isdigit() and pa[1].isdigit():
                numbers[(int(pa[0]), nm(pa[2]))] = pa[1]
    rows = []

    def add(r, ours, min_odds, cap, chance_at, note):
        rc = int(r["race"])   # max_odds: the 3x-our-price (or EARLY $8) ceiling; an open above it is not a bet (14 Oct 2026)
        ts = tiers(min_odds, cap, chance_at, r.get("only_ride", False), field[rc])
        for k, (t, extra, total) in enumerate(ts, 1):
            rows.append(dict(date=date, venue=venue, race=rc, jump=times.get(str(rc), ""), number=numbers.get((rc, nm(r["horse"])), ""), horse=r["horse"], bet="WIN",
                             min_odds=f"{t:.2f}", max_odds=f"{cap:.2f}", stake_units=f"{extra:.2f}", stake_dollars=f"{extra * 100:.0f}",
                             order=f"{k} of {len(ts)}", total_if_all_fire=f"{total:.2f}u", our_price=f"{ours:.2f}", note=note))

    if a.after_open:
        by = {(int(r["race"]), r["horse"]): r for r in v}
        seen = set()
        for b in csv.DictReader(open(f"{B}-open-bets.csv")):
            k = (int(b["race"]), b["horse"])
            if b["plan"] == "top_pick" or k in seen or k not in by:
                continue
            seen.add(k); ours = float(b["model_price"]); pb = 1 / ours
            add(by[k], ours, round(1.2 * ours + 0.004, 2), 3 * ours, lambda t, pb=pb: pb, f"value at the open (${b['fk_open'] or b['open']})")
    else:
        fs = set(json.load(open(f"{B}-first-starters.json")))
        fu = json.load(open(f"{B}-first-up-blocks.json"))
        for r in v:
            k = f"{int(r['race'])}|{r['horse']}"; pm = r["p_model"]; ours = 1 / pm; blk = fu.get(k, "")
            if k in fs or (blk and not blk.startswith("EARLY")) or not 1.6 <= ours <= 15:
                continue
            min_odds = round(SHADE * (1.2 / pm ** 0.82) ** (1 / 0.78), 2)
            cap = min(3 * ours, 8.0 if blk.startswith("EARLY") else 1e9)
            if min_odds >= cap:
                continue
            add(r, ours, min_odds, cap, lambda t, pm=pm: pm ** 0.82 * t ** -0.22, "EARLY: $8 or shorter only" if blk else "")
    rows.sort(key=lambda x: (x["race"], x["horse"], float(x["min_odds"])))
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["date"]); w.writeheader(); w.writerows(rows)
    print(f"{a.out}: {len(rows)} orders on {len({(x['race'], x['horse']) for x in rows})} runners")


if __name__ == "__main__":
    main()
