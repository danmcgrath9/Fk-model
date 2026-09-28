"""Where is the form price sharper than the opening market? Read-only, no Form King calls.

    python scripts/sharpness_by_segment.py [--state VIC] [--history history]

The form price (form + the horse's past prices, fitted to winners, the config/form_price.json
recipe) is fitted on the older 70% of racing. On the newer 30% it never saw, every race is
put in a segment and, per segment, the form price and Form King's opening average are each
scored for closeness to Betfair SP (KL, lower is closer) and for being right about the
winner (log loss). Where the form price is closer to BSP than the open, the open is the
softer price there. The 20c value rule at the opening price is shown per segment as well.

Segments: metro or country track; Saturday or not; field size; distance; the class standard
(Form King's LWS); and the opening favourite's price.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fk import backtest as B  # noqa: E402
from fit_form_only import CANDIDATES, TARGETS, TRAIN_SHARE, fit_np, split_by_date  # noqa: E402
from form_value_trial import bets_for, summary  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MODEL = "form_kitchen_sink_memory"
RIDGE = 30.0


def fav_price(race) -> float | None:
    opens = [float(r.raw["open"]) for r in race.runners if r.raw.get("open")]
    return min(opens) if opens else None


def segments(race) -> dict[str, str]:
    n = len(race.runners)
    d = float(getattr(race, "distance_m", None) or 0)
    try:
        lws = float(race.lws) if getattr(race, "lws", None) is not None else None
    except (TypeError, ValueError):
        lws = None
    fav = fav_price(race)
    return {
        "track": "metro" if (race.track or "").lower().startswith(B.METRO_TRACKS) else "country",
        "day": "Saturday" if date.fromisoformat(str(race.date)[:10]).weekday() == 5 else "midweek/Sunday",
        "field": "8 or fewer" if n <= 8 else ("9 to 12" if n <= 12 else "13+"),
        "distance": "sprint (to 1200)" if d <= 1200 else ("mile-ish (1201-1700)" if d <= 1700 else "staying (1701+)"),
        "class (LWS)": "no LWS" if lws is None else ("low (under 80)" if lws < 80 else ("mid (80-89)" if lws < 90 else "high (90+)")),
        "favourite": "no price" if fav is None else ("$2.50 or under" if fav <= 2.5 else ("$2.51 to $4" if fav <= 4 else "over $4")),
    }


def kl_of(probs_fn, races) -> float:
    return B.score(probs_fn(races), races).kl_to_bsp


def ll_of(probs_fn, races) -> float:
    return B.score(probs_fn(races), races).log_loss


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--history", default=str(ROOT / "history"))
    a = ap.parse_args()
    from backtest import load_races
    races, _ = load_races(a.state, Path(a.history))
    races = [r for r in races if B.bsp_chances(r.runners) and B.winner_chances(r.runners)]
    train, test = split_by_date(races, TRAIN_SHARE)
    beta = fit_np(train, CANDIDATES[MODEL], RIDGE, target=TARGETS["winners"])
    form = lambda rs: [B.predict(beta, r.runners) for r in rs]  # noqa: E731
    mkt = B.market_probs
    print(f"Form price ({MODEL}, fitted to winners, ridge {RIDGE:g}) on {len(train)} races; judged on the {len(test)} newer "
          f"races ({test[0].date} to {test[-1].date}).\n")
    print("KL to BSP: lower is closer to Betfair SP. 'Edge' is the open's KL less the form price's: POSITIVE means the form "
          "price is the sharper of the two in that segment. Log loss: lower is more right about the winner.\n")
    tagged = [(segments(r), r) for r in test]
    for key in ("track", "day", "field", "distance", "class (LWS)", "favourite"):
        print(f"### by {key}\n")
        print("| segment | races | form KL | open KL | edge | form log loss | open log loss | 20c value at open: bets | winners | return at open | at BSP |")
        print("|---|---|---|---|---|---|---|---|---|---|---|")
        groups: dict[str, list] = {}
        for seg, r in tagged:
            groups.setdefault(seg[key], []).append(r)
        for name, rs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            if len(rs) < 40:
                print(f"| {name} | {len(rs)} | too few | | | | | | | | |")
                continue
            fk, mk = kl_of(form, rs), kl_of(mkt, rs)
            fl, ml = ll_of(form, rs), ll_of(mkt, rs)
            cells = summary(bets_for(rs, beta, 0.2, True)).strip("|").split("|")
            bets, wins, at_open, at_bsp = [c.strip() for c in cells[:4]]
            print(f"| {name} | {len(rs)} | {fk:.4f} | {mk:.4f} | {mk - fk:+.4f} | {fl:.4f} | {ml:.4f} | {bets} | {wins} | {at_open} | {at_bsp} |")
        print()


if __name__ == "__main__":
    main()
