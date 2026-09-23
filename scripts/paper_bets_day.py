"""One day's paper bets as a table, one row per runner backed, every plan that backed it.

    python scripts/paper_bets_day.py --date 2026-09-23 [--track Geelong]

Read-only: the database's fk.paper_bets, no Form King calls.
"""
from __future__ import annotations

import argparse
from collections import OrderedDict

from _common import load_settings
from fk.db import Db

SHORT = {"top_pick": "Top pick", "top_pick_to_win_1": "To win 1", "value_flags": "Value",
         "value_under_8": "Value <$8", "kelly_quarter": "Kelly"}


def table(bets: list[dict]) -> str:
    """Markdown: race, horse, struck price, rated price, plans (with the stake where it is not
    one unit), and the result once settled."""
    by_runner: "OrderedDict[tuple, list[dict]]" = OrderedDict()
    for b in sorted(bets, key=lambda b: (b["track"] or "", b["race_number"] or 0, b["horse_name"] or "", b["plan"])):
        by_runner.setdefault((b["track"], b["race_number"], b["horse_name"]), []).append(b)
    lines = ["| Race | Horse | Opened | Price taken | Our price | Plans (units) | Result |", "|---|---|---|---|---|---|---|"]
    for (track, race, horse), group in by_runner.items():
        first = group[0]
        plans = ", ".join(f"{SHORT.get(b['plan'], b['plan'])} {float(b['stake']):.2f}" for b in group)
        price = f"${float(first['price']):.2f}" if first["price"] else "n/a"
        rated = f"${float(first['rated_price']):.2f}" if first["rated_price"] else "n/a"
        opened = f"${float(first['opening_price']):.2f}" if first.get("opening_price") else "n/a"
        if first.get("void"):
            result = "void, did not start (stake back)"
        elif first["settled_at"] is None:
            result = "open"
        else:
            won = sum(float(b["returned"] or 0) - float(b["stake"]) for b in group)
            fin = first["finish"] if first["finish"] is not None else "?"
            sp = f" BSP ${float(first['settle_price']):.2f}" if first["settle_price"] else ""
            ded = f", deduction {float(first['deduction']):.0%}" if first.get("deduction") else ""
            result = f"{fin}{sp}, {won:+.2f}u{ded}"
        lines.append(f"| R{race} | {horse} | {opened} | {price} | {rated} | {plans} | {result} |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="meeting date YYYY-MM-DD")
    ap.add_argument("--track", help="only this track (prefix, any case)")
    a = ap.parse_args()
    db = Db(load_settings().database_url)
    bets = [b for b in db.paper_bets() if str(b["meeting_date"]) == a.date
            and (not a.track or (b["track"] or "").lower().startswith(a.track.lower()))]
    if not bets:
        print(f"no paper bets on {a.date}" + (f" at {a.track}" if a.track else ""))
        return
    print(f"## Paper bets, {a.date}" + (f", {a.track}" if a.track else "") + "\n")
    print(table(bets))
    staked = {}
    for b in bets:
        staked[b["plan"]] = staked.get(b["plan"], 0.0) + float(b["stake"])
    models = sorted({b.get("model") or "unrecorded" for b in bets})
    print("\nPriced by: " + "; ".join(models))
    print("\nStaked by plan: " + ", ".join(f"{SHORT.get(p, p)} {s:.2f}u" for p, s in staked.items()))
    print("\nOne unit a bet except Kelly (quarter Kelly on a 100-unit bank) and To win 1 (staked to win one unit). "
          "'Price taken' is the price on the page when the race was first priced; settled bets pay at Betfair SP.")


if __name__ == "__main__":
    main()
