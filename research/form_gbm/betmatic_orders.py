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
SHADE, TIERS = 0.95, (1.0, 1.25, 1.5)
UNIT_DOLLARS = 50   # founder, 18 Oct 2026: $50 a unit until he says otherwise (the send workflow's unit input is what BetMatic gets)
# Short opens (founder, 16 Oct 2026: "do it for Moe and moving forward"; t_short_edge.py): when the TAB opens a runner
# under $4 the edge is 1.15, not 1.2. On the holdout the extra bets this lets in still beat the open like our normal ones
# (77% shortened after the open, open 1.23x BSP, against 83% and 1.31x for the live under-$4 bets); 1.10 and below fell
# to coin-flip. Built as two ladders per runner: the 1.2 ladder with every step under $4 lifted to $4.00 (fires only on
# an open of $4 or more), and a 1.15 ladder capped at $3.99 (fires only on an open under $4), so each open price meets
# exactly one rule and the stakes are the backtest's.
SHORT_OPEN, SHORT_EDGE = 4.0, 1.15   # 14 Oct: 3 steps sized at the next step: same holdout profit as 8 (+801u), at most 3 bets a horse (t_monthly.py)


def tiers(min_odds, cap, chance_at, only_ride, field, mult_at=None):
    """[(price, extra stake, total stake)]: each step adds what the stake rule gives at the NEXT step's price over the
    steps before it, so a horse opening anywhere in a step is staked as if at the top of it (14 Oct 2026,
    t_betmatic_tiers.py: 8 steps sized this way made 18% more on the holdout than 3 steps sized at their own price,
    at the same ROI). The last step is sized at its own price.
    mult_at(t): the firm/drift multiplier at a step's own price (drift_forecast.py, 18 Oct 2026); the step's total is
    the stake rule's total times it, capped at the stake rule's maximum."""
    ts = [round(min_odds * m, 2) for m in TIERS if min_odds * m < cap]
    out, prev = [], 0.0
    for k, t in enumerate(ts):
        tp = ts[k + 1] if k + 1 < len(ts) else t
        s = stake_rule.stake(chance_at(tp), tp, only_ride, field)
        if mult_at is not None:
            s = round(min(stake_rule.MAX_UNITS, s * mult_at(t)), 2)
        if s - prev >= 0.01:
            out.append((t, round(s - prev, 2), s)); prev = s
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix"); ap.add_argument("gtag"); ap.add_argument("out")
    ap.add_argument("--times", default=""); ap.add_argument("--after-open", action="store_true")
    ap.add_argument("--v6", help="price file to use instead of DAYPREFIX-GTAG-v6.json (e.g. the version priced before the market)")
    ap.add_argument("--drift", metavar="DAY_NPZ", help="stake by the firm/drift forecast (drift_forecast.py): the day's "
                                      "final-field npz the model file was priced from; the forecast model is read from --drift-dir")
    ap.add_argument("--drift-dir", default=os.environ.get("FK_MODEL_DIR", "."), help="directory holding drift_model.txt and drift_meta.json")
    ap.add_argument("--numbers", help="entry_numbers.py output (race|number|name|emergency|scratched): adds the saddlecloth "
                                      "number BetMatic bets on (default DAYPREFIX-entry-numbers.txt if it exists)")
    a = ap.parse_args()
    B = f"{L}/{a.prefix}-{a.gtag}"
    times = dict(x.split("=", 1) for x in a.times.split(",") if "=" in x)
    v = json.load(open(a.v6 or f"{B}-v6.json"))
    date, venue = a.prefix[:10], a.prefix[11:].replace("-", " ").title()
    import re
    nm = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
    nums_fn = a.numbers or (f"{L}/{a.prefix}-entry-numbers.txt" if os.path.exists(f"{L}/{a.prefix}-entry-numbers.txt") else None)
    numbers, out_ = {}, set()
    if nums_fn:
        for l in open(nums_fn):
            pa = l.strip().split("|")
            if len(pa) == 5 and pa[0].isdigit() and pa[1].isdigit():
                numbers[(int(pa[0]), nm(pa[2]))] = pa[1]
                if pa[3] == "True" or pa[4] == "True":
                    out_.add((int(pa[0]), nm(pa[2])))
    for pf in (f"{L}/{a.prefix}-prices-fields.txt", f"{L}/{a.prefix}-prices.txt"):   # SCR in a fields/prices file = out
        if os.path.exists(pf):
            for l in open(pf):
                pa = [x.strip() for x in l.split("#")[0].split(",")]
                if len(pa) >= 3 and pa[0].isdigit() and pa[2].upper().startswith("SCR"):
                    out_.add((int(pa[0]), nm(pa[1])))
    if not out_ and not nums_fn:
        print("WARNING: no entry-numbers or fields file, so emergencies and scratchings cannot be checked. Build orders "
              "only on a model file priced on the final field.")
    # FINAL FIELD ONLY (14 Oct 2026, t_overlap.py): the 5-9 Oct files were priced with emergencies and scratched horses
    # still in, so the runners who ran held only 81-90% of the probability, every price came out ~15% too long, and the
    # forward test staked half what the same races support. Emergencies and scratched runners are dropped here and each
    # race's model probability is re-spread over the runners left, so an order is never priced against a horse that will
    # not run. A race whose runners held under 97% before the re-spread is named: the model file was made before the
    # final field and should be re-made.
    dropped = [r for r in v if (int(r["race"]), nm(r["horse"])) in out_]
    v = [r for r in v if (int(r["race"]), nm(r["horse"])) not in out_]
    tot = {}
    for r in v:
        tot[int(r["race"])] = tot.get(int(r["race"]), 0.0) + r.get("p_model", r["p"])
    low = {rc: t for rc, t in tot.items() if abs(t - 1) > 0.03}
    if dropped:
        print(f"final field: dropped {len(dropped)} emergencies/scratched runners from the model file")
    if low:
        print("WARNING: model probability of the final field, by race (re-spread to 1.00 for these orders; re-make the "
              "model file on the final field): " + ", ".join(f"R{rc} {t:.2f}" for rc, t in sorted(low.items())))
    v = [dict(r, p_model=r.get("p_model", r["p"]) / tot[int(r["race"])]) for r in v]
    field = {}
    for r in v:
        field[int(r["race"])] = field.get(int(r["race"]), 0) + 1
    rows = []
    FC, XR = None, {}
    if a.drift:   # firm/drift stakes (founder, 18 Oct 2026: drop the forecast-to-drift third, x2 on the forecast-to-firm third)
        import numpy as np, drift_forecast
        FC = drift_forecast.Forecast(a.drift_dir); U = np.load(a.drift, allow_pickle=True)
        uc = {str(c): j for j, c in enumerate(U["cols"])}; miss = [c for c in FC.cols if c not in uc]
        if miss:
            sys.exit(f"STOP: the day file lacks {len(miss)} columns the drift model needs ({', '.join(miss[:5])}...)")
        sel = [uc[c] for c in FC.cols]
        for i in range(len(U["name"])):
            XR[(int(U["race_number"][U["race_idx"][i]]), nm(str(U["name"][i])))] = np.asarray(U["X"][i, sel], np.float32)
        print(f"firm/drift stakes: drift third x{drift_forecast.DRIFT_MULT:g}, firm third x{drift_forecast.FIRM_MULT:g} "
              f"(forecast thresholds {FC.t1:.3f} / {FC.t2:.3f})")
    nodrift = []

    def add(r, ours, min_odds, cap, chance_at, note, band=None):
        """band: None for one ladder; "open4+" lifts every step under SHORT_OPEN to it; "under4" keeps only the steps
        under SHORT_OPEN and caps them there. Steps are sized on the full ladder first, so the stakes match the backtest."""
        rc = int(r["race"])   # max_odds: the 3x-our-price (or EARLY $8) ceiling; an open above it is not a bet (14 Oct 2026)
        mult_at = None
        if FC is not None:
            xr = XR.get((rc, nm(r["horse"])))
            if xr is None:
                sys.exit(f"STOP: R{rc} {r['horse']} is not in the day file given to --drift")
            mult_at = lambda t, xr=xr, pm=r["p_model"], f=field[rc]: FC.mult(xr, pm, t, f)[0]
            ms = [mult_at(round(min_odds * mm, 2)) for mm in TIERS if min_odds * mm < cap]
            lab_ = {0.0: "drift", 1.0: "middle", 2.0: "firm"}
            fc_note = "forecast " + "/".join(lab_.get(x, f"x{x:g}") for x in ms) + " by step"
            note = (note + "; " if note else "") + fc_note
        ts = tiers(min_odds, cap, chance_at, r.get("only_ride", False), field[rc], mult_at)
        if FC is not None and not ts:
            nodrift.append(f"R{rc} {r['horse']}")
        hi = cap
        if band == "open4+":
            ts = [(max(t, SHORT_OPEN), extra, total) for t, extra, total in ts]
        elif band == "under4":
            ts = [x for x in ts if x[0] < SHORT_OPEN]; hi = min(cap, SHORT_OPEN - 0.01)
        for k, (t, extra, total) in enumerate(ts, 1):
            rows.append(dict(date=date, venue=venue, race=rc, jump=times.get(str(rc), ""), number=numbers.get((rc, nm(r["horse"])), ""), horse=r["horse"], bet="WIN",
                             min_odds=f"{t:.2f}", max_odds=f"{hi:.2f}", stake_units=f"{extra:.2f}", stake_dollars=f"{extra * UNIT_DOLLARS:.0f}",
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
            min_short = round(SHADE * (SHORT_EDGE / pm ** 0.82) ** (1 / 0.78), 2)
            cap = min(3 * ours, 8.0 if blk.startswith("EARLY") else 1e9)
            ch = lambda t, pm=pm: pm ** 0.82 * t ** -0.22; note = "EARLY: $8 or shorter only" if blk else ""
            if min_odds < cap and SHORT_OPEN < cap:
                add(r, ours, min_odds, cap, ch, note, "open4+")
            if min_short < min(cap, SHORT_OPEN):
                add(r, ours, min_short, cap, ch, (note + "; " if note else "") + "opens under $4: edge 1.15", "under4")
    rows.sort(key=lambda x: (x["race"], x["horse"], float(x["min_odds"])))
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["date"]); w.writeheader(); w.writerows(rows)
    print(f"{a.out}: {len(rows)} orders on {len({(x['race'], x['horse']) for x in rows})} runners")
    if FC is not None and nodrift:
        print(f"forecast to drift at every step, no order (ladder dropped): {', '.join(sorted(set(nodrift)))}")


if __name__ == "__main__":
    main()
