"""The corrected blend at TAB's open, the morning TAB opens (18 Nov 2026, founder: "the GRV price is horrific, how
aren't we matching against TAB opening price")

The nightly card is made the evening before, when TAB has no price yet (TAB opens Victorian greyhounds at a median
7:25am, Test 92), so its rule reads GRV's evening price, which TAB's market does not agree with (the live tracker). The
corrected blend (Tests 80 and 81) is built to be matched against TAB's first price, and until now it has only been
matched after the races, by the tracker (variants 4 and 5). This prices it the same way on the morning itself:

  1. today's Victorian greyhound races from Betwatch, as they stand: TAB's field at its first price (the tracker's
     open_field), and each runner's latest TAB, Sportsbet and Ladbrokes prices
  2. last night's kept card_iso (CARDS_DIR) and the saved correction (MODEL_DIR), through topaz_iso.at_open: ours
     with Isolynx over TAB's field at its first price, blended at 0.54 / 0.67 and corrected
  3. the rule: the corrected price $2 to $15 and TAB's first price at least 1.1x it (and, marked, 1.2x); one unit flat,
     paper only

The bets, with TAB's first price and when, and TAB's price now, are SEALED to the card key (Betwatch's data and the
card's inputs are never shown in this public log); the log prints counts only.

    python research/greyhound/topaz_morning.py LABEL     (MORNING_DAY=YYYY-MM-DD, default today in Melbourne;
                                                          CARDS_DIR, MODEL_DIR, BETWATCH_API_KEY)
"""
import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_iso                  # noqa: E402
import topaz_track as T           # noqa: E402
from greyhound import betwatch as B   # noqa: E402

MEL = ZoneInfo("Australia/Melbourne")


def latest_prices(races: list) -> dict:
    """(venue, race number, normalised name) -> TAB's latest price and when, and Sportsbet's and Ladbrokes' latest."""
    out = {}
    for r in races:
        for ru in r.get("runners", []):
            b = ru.get("books") or {}
            tab = sorted(((b.get("Tab") or {}).get("flucs") or []), key=lambda f: str(f[1]))
            out[(r.get("track"), str(r.get("number")), T.norm(pd.Series([ru.get("name") or ""]))[0])] = {
                "tab_now": tab[-1][0] if tab else None, "tab_now_at": tab[-1][1] if tab else None,
                "sportsbet_now": ((b.get("Sportsbet") or {}).get("last") or [None])[0],
                "ladbrokes_now": ((b.get("Ladbrokes") or {}).get("last") or [None])[0]}
    return out


def morning_bets(x: pd.DataFrame, now: dict) -> list:
    """The rule's bets at 1.1x, each with the 1.2x mark, the price needed at each, and TAB's first and latest price."""
    if x.empty:
        return []
    m11 = topaz_iso.bets(x, 1.1)
    m12 = topaz_iso.bets(x, 1.2)
    out = []
    for i in np.where(m11)[0]:
        r = x.iloc[i]
        fair = 1 / float(r.p_corr)
        lp = now.get((r.venue, str(r.race_no), T.norm(pd.Series([r.dog_name or ""]))[0]), {})
        out.append({"venue": r.venue, "race_no": str(r.race_no), "start": r.start, "box": str(r.card_box),
                    "dog": r.card_dog, "fair": round(fair, 3), "need_11": round(1.1 * fair, 2),
                    "need_12": round(1.2 * fair, 2), "at_12": bool(m12[i]), "tab_open": float(r.price),
                    "tab_open_at": r.tab_first_t, **lp})
    return sorted(out, key=lambda b: str(b["start"]))


def main(label):
    day = os.environ.get("MORNING_DAY", "").strip() or datetime.now(MEL).strftime("%Y-%m-%d")
    print(f"# {label}: the corrected blend at TAB's open, {day}\n")
    iso = T.load_iso(os.environ.get("CARDS_DIR", ""))
    if iso is None:
        return 1
    cards, bst, meta = iso
    cards = cards[cards.day.astype(str) == day] if len(cards) else cards
    if cards.empty:
        print(f"No kept card_iso for {day} (CARDS_DIR): nothing to price")
        return 1
    races = [B.compact(r) for r in B.fetch_day(B._session(), day)]
    facts = T.open_field(races)
    x = topaz_iso.at_open(facts, cards, bst, meta) if len(facts) else pd.DataFrame()
    bets = morning_bets(x, latest_prices(races))
    print(f"Card races: {cards.race_key.nunique():,}. TAB's market: {len(races):,} races, "
          f"{int(facts.bw_race.nunique()) if len(facts) else 0:,} with a first price. Priced on the corrected blend: "
          f"{int(x.bw_race.nunique()) if len(x) else 0:,} races. Bets at 1.1x: {len(bets)}, of them at 1.2x: "
          f"{sum(b['at_12'] for b in bets)}.")
    from greyhound import sealed
    lines, sha = sealed.seal(json.dumps({"day": day, "bets": bets}, default=str).encode())
    print(f"sealed, sha256 {sha}")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "topaz morning"))
