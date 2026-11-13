"""What the card would have taken, live (14 Nov 2026, founder: "There's a key that pulls the live races on GitHub, can
you track what we would of taken the model live").

Every night gh topaz nightly prices tomorrow's Victorian card and keeps it (race, dog, our chance, GRV's pre-race price)
in this repository's Actions cache (topaz_price_upcoming.save_card). The morning after the races, gh topaz track brings
the day's results (Topaz) and every bookmaker's price history (Betwatch: TAB's first price, when it came, and who was
scratched after it) up to date, and settles three ways of betting the card as if each had been bet at TAB's first price:

  1. the card as sent: the bets the card listed (Test 27's rule on GRV's pre-race price, ours blended with GRV's book),
     every one taken at TAB's first price, at the card's units
  2. the same bets, only where TAB's first price was still at least 1.3x the card's blended price
  3. the rule at TAB's open (Tests 51 and 54): our chance over the field at TAB's first price, blended with TAB's own
     book there, held at 0.54 ours / 0.67 TAB; a bet when TAB's first price is at least 1.3x the blended price, the
     blended price $2 to $15, Kelly units

Settling: TAB's first price less TAB's deduction for the dogs scratched after it (topaz_round33.field_rows, the same
deduction the backtests used). A bet on a dog scratched after the bet is a refund; a dog scratched before TAB opened was
never in the market, so a card bet on it is void. A race is priced at the open only when every dog in TAB's field then
is on the card. The best first price of three (TAB, Sportsbet, Ladbrokes) and Betfair's BSP (once Betfair publishes
the month) ride along for comparison: BSP under the price paid is a bet that beat the closing market.

    python research/greyhound/topaz_track.py RUNS_DIR LABEL
        RUNS_DIR: the Topaz pulls (runs_VIC_YYYY-MM.json.gz, for the results). CARDS_DIR: the cached cards
        (card_YYYY-MM-DD.csv.gz). BETWATCH_DIR. BETFAIR_DIR (optional). TRACK_FROM: the first card day to settle
        (default every card). FACTS_FROM, FACTS_TO: also seal each day's market facts in that span that has no cached
        card (the nights before the cards were cached), to settle cards held elsewhere with --local.
    python research/greyhound/topaz_track.py --local FACTS.json CARD.json [CARD.json ...]
        the same settlement on unsealed facts and unsealed nightly cards; prints every bet. Private copies only.

The log is public, so it carries counts and units only: the bets themselves (dogs, prices) are sealed
(greyhound/sealed.py), as the card is. Nothing is bet.
"""
import gzip
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gbm_v0                     # noqa: E402
import topaz_round9 as R9         # noqa: E402
import topaz_round33 as R33       # noqa: E402
import topaz_v1 as V1             # noqa: E402

HELD = (0.54, 0.67)               # Test 51's weights at TAB's first price (Dec 2023 to Jun 2024), held in Test 54
RATIO, BAND = 1.3, (2, 15)
CARD_BLEND = (0.51, 0.66)         # the card's own blend with GRV's pre-race price (Test 27), when a card lacks it
VARIANTS = {"card": "1. the card as sent, at TAB's first price",
            "card_still": "2. the card's bets still 1.3x at TAB's first price",
            "open": "3. the rule at TAB's open, blend held 0.54 / 0.67"}
CARD_COLS = ["day", "race_key", "venue", "race_no", "start", "box", "dog_name", "p_model", "grv_price", "w_ours",
             "w_grv"]
FACT_COLS = ["date", "bw_race", "venue", "race_no", "start", "dog_name", "price", "p_book", "ran", "s_later",
             "n_later", "ded", "tab_first_t", "sportsbet_first", "ladbrokes_first", "won", "bsp"]


def norm(s) -> np.ndarray:
    return gbm_v0.norm_name(pd.Series(s, dtype=object).fillna("")).values


# ---- the cards ----------------------------------------------------------------------------------------------------

def cards_from_dir(d: str) -> pd.DataFrame:
    fs = sorted(Path(d).glob("card_*.csv.gz")) if d and os.path.isdir(d) else []
    if not fs:
        return pd.DataFrame(columns=CARD_COLS)
    return pd.concat([pd.read_csv(f, dtype={"race_no": str, "box": str}) for f in fs], ignore_index=True)


def cards_from_payload(p: dict) -> pd.DataFrame:
    """A nightly card payload (topaz_price_upcoming.card_payload, unsealed) as card rows."""
    w = p.get("blend") or CARD_BLEND
    rows = []
    for r in p.get("races", []):
        for x in r["r"]:
            rows.append({"day": p["day"], "race_key": f"{p['day']}|{r['t']}|{r['n']}", "venue": r["t"],
                         "race_no": str(r["n"]), "start": r.get("s", ""), "box": str(x[0]), "dog_name": x[1],
                         "p_model": float(x[2]), "grv_price": float(x[3]), "w_ours": w[0], "w_grv": w[1]})
    return pd.DataFrame(rows, columns=CARD_COLS)


def card_rule(cards: pd.DataFrame) -> pd.DataFrame:
    """The card's own bets, exactly as topaz_price_upcoming.rule_bets makes them: ours blended with GRV's pre-race book
    (its margin taken out), a bet when GRV's price is at least 1.3x the blended price, the blended price $2 to $15,
    Kelly units. One row per bet: the card row, p_blend, units."""
    c = cards[cards.grv_price > 1].copy()
    if c.empty:
        return c.assign(p_blend=[], units=[])
    c["race_id"] = c.race_key
    c["p_grv"] = (1 / c.grv_price) / (1 / c.grv_price).groupby(c.race_key).transform("sum")
    score = c.w_ours.values * np.log(c.p_model.clip(1e-12).values) + c.w_grv.values * np.log(c.p_grv.clip(1e-12).values)
    c["p_blend"] = V1.race_softmax(score, c.race_key.values)
    m, _, u = R9.horse_bets(c, c.p_blend.values, c.p_grv.values, c.grv_price.values.astype(float), 0.0, RATIO, BAND)
    return c[m].assign(units=u[m]).drop(columns="race_id")


# ---- the market and the results -----------------------------------------------------------------------------------

def betwatch_races(bdir: str, days) -> list:
    days = set(days)
    out = []
    for mo in sorted({d[:7] for d in days}):
        for f in Path(bdir).glob(f"betwatch_VIC_G_{mo}.json.gz"):
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                out.extend(r for r in json.load(fh).get("races", []) if r.get("date") in days)
    return out


def open_field(races: list) -> pd.DataFrame:
    """Each race as it stood at TAB's first price (topaz_round33.field_rows at 0 minutes), with the race's venue and
    number, each runner's raw name, when TAB's first price came, and Sportsbet's and Ladbrokes' first prices."""
    rows = []
    for r in races:
        extra = {}
        for ru in r.get("runners", []):
            b = ru.get("books") or {}
            tab = sorted(((b.get("Tab") or {}).get("flucs") or []), key=lambda f: str(f[1]))
            extra[ru.get("name")] = {"tab_first_t": tab[0][1] if tab else None,
                                     **{f"{k.lower()}_first": (((b.get(k) or {}).get("flucs") or [[np.nan]])[0][0])
                                        for k in ("Sportsbet", "Ladbrokes")}}
        for x in R33.field_rows(r, times=(0,)):
            name = x.pop("dog_raw")
            rows.append({**x, "dog_name": name, "venue": r.get("track"), "race_no": str(r.get("number")),
                         "start": r.get("start"), **extra.get(name, {})})
    f = pd.DataFrame(rows)
    return f.drop(columns="k") if not f.empty else f


def topaz_results(runs_dir: str, days) -> pd.DataFrame:
    """(date, normalised dog) -> won, scratched. A race with a winner settles every dog in it (a dog that fell or did
    not finish lost); a race with no winner yet leaves its dogs unsettled. A name twice in one day is left out."""
    days = set(days)
    rows = []
    for mo in sorted({d[:7] for d in days}):
        for f in Path(runs_dir).glob(f"runs_VIC_{mo}.json.gz"):
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                for r in json.load(fh):
                    d = str(r.get("meetingDate") or "")[:10]
                    if d in days:
                        rows.append((d, r.get("raceId"), r.get("dogName"), pd.to_numeric(r.get("place"), errors="coerce"),
                                     bool(r.get("scratched"))))
    t = pd.DataFrame(rows, columns=["date", "race", "dog", "place", "scratched"])
    t["_dn"] = norm(t.dog)
    has_winner = (t.place == 1).groupby(t.race).transform("any")
    t["won"] = (t.place == 1).astype(float).where(has_winner | t.scratched)
    return t.drop_duplicates(["date", "_dn"], keep=False)[["date", "_dn", "won", "scratched"]]


def betwatch_days(bdir: str) -> set:
    """The days the Betwatch month files hold (a day is pulled once it is over)."""
    out = set()
    for f in Path(bdir).glob("betwatch_VIC_G_*.json.gz"):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            out |= set(json.load(fh).get("days", []))
    return out


def betfair_bsp(bf_dir: str, days) -> pd.DataFrame:
    if not bf_dir or not os.path.isdir(bf_dir):
        return pd.DataFrame(columns=["date", "_dn", "bsp"])
    try:
        bf = gbm_v0.load(bf_dir)
    except Exception:                                    # no file for these months yet
        return pd.DataFrame(columns=["date", "_dn", "bsp"])
    bf = bf[(bf.STATE_CODE == "VIC") & (bf.WIN_BSP > 1)]
    bf = bf.assign(date=bf.date.dt.strftime("%Y-%m-%d"), _dn=bf.dog, bsp=bf.WIN_BSP)
    bf = bf[bf.date.isin(set(days))]
    return bf[["date", "_dn", "bsp"]].drop_duplicates(["date", "_dn"], keep=False)


def market_facts(runs_dir: str, bdir: str, bf_dir: str, days) -> pd.DataFrame:
    """Every runner in TAB's field at its first price on these days, with the result and BSP."""
    f = open_field(betwatch_races(bdir, days))
    if f.empty:
        return pd.DataFrame(columns=FACT_COLS)
    f["_dn"] = norm(f.dog_name)
    f = f.merge(topaz_results(runs_dir, days), on=["date", "_dn"], how="left")
    f = f.merge(betfair_bsp(bf_dir, days), on=["date", "_dn"], how="left")
    f.loc[~f.ran.astype(bool), "won"] = 0.0          # scratched after the open: a refund, whatever Topaz says
    return f[FACT_COLS]


# ---- settling -----------------------------------------------------------------------------------------------------

def paid_at(price: float, ded) -> float:
    """The price paid after TAB's deduction (cents in the dollar off the winnings)."""
    return 1 + (price - 1) * (1 - (0.0 if ded is None or pd.isna(ded) else float(ded)))


def settle(price, ded, won, ran, units) -> tuple:
    """(price paid, status, units won) for one bet at `price`."""
    if not np.isfinite(price) or price <= 1:
        return np.nan, "void: not in TAB's market at its open", 0.0
    paid = paid_at(price, ded)
    if not ran:
        return paid, "refund: scratched after the bet", 0.0
    if pd.isna(won):
        return paid, "unsettled: no result yet", 0.0
    return paid, ("won" if won == 1 else "lost"), (units * (paid - 1) if won == 1 else -units)


def best_first(f: pd.DataFrame) -> np.ndarray:
    cols = ["price", "sportsbet_first", "ladbrokes_first"]
    b = f[cols].apply(pd.to_numeric, errors="coerce")
    return b.where(b > 1).max(axis=1).where(b.price > 1).values


def ledger(cards: pd.DataFrame, facts: pd.DataFrame) -> tuple:
    """(one row per bet of each variant, coverage counts). Cards and facts join on (day, normalised dog name)."""
    cards = cards.assign(_dn=norm(cards.dog_name))
    facts = facts.assign(_dn=norm(facts.dog_name), best=best_first(facts)) if len(facts) else facts.assign(_dn=[], best=[])
    fx = facts.drop_duplicates(["date", "_dn"], keep=False).set_index(["date", "_dn"])
    rows = []

    def add(variant, c, p_blend, units, f):
        units = round(float(units), 2)                   # the stake as the card shows it
        price = float(f.price) if f is not None else np.nan
        paid, status, won_u = settle(price, None if f is None else f.ded, None if f is None else f.won,
                                     True if f is None else bool(f.ran), units)
        bsp = np.nan if f is None else f.bsp
        rows.append({"variant": variant, "day": c.day, "venue": c.venue, "race_no": c.race_no, "box": c.box,
                     "dog_name": c.dog_name, "p_model": round(float(c.p_model), 4), "p_blend": round(float(p_blend), 4),
                     "grv_price": c.grv_price, "tab_first": price,
                     "tab_first_t": None if f is None else f.tab_first_t,
                     "ded": None if f is None else f.ded, "paid": paid,
                     "best_first": np.nan if f is None else f.best, "bsp": bsp, "units": units,
                     "status": status, "units_won": won_u,
                     "units_won_best": ({"won": units * (paid_at(f.best, f.ded) - 1), "lost": -units}.get(status, 0.0)
                                        if f is not None else 0.0)})

    for _, c in card_rule(cards).iterrows():
        f = fx.loc[(c.day, c._dn)] if (c.day, c._dn) in fx.index else None
        add("card", c, c.p_blend, c.units, f)
        if f is not None and np.isfinite(f.price) and f.price >= RATIO / max(c.p_blend, 1e-9):
            add("card_still", c, c.p_blend, c.units, f)

    cov = {"races": int(cards.race_key.nunique()), "in_market": 0, "priced": 0}
    if len(facts):
        x = facts.merge(cards[["day", "_dn", "race_key", "venue", "race_no", "box", "dog_name", "p_model",
                               "grv_price"]].rename(columns={"day": "date", "dog_name": "card_dog", "venue": "card_venue",
                                                             "race_no": "card_race_no"}),
                        on=["date", "_dn"], how="left")
        x = x[x.date.isin(set(cards.day))]
        cov["in_market"] = int(x.bw_race.nunique())
        g = x.groupby("bw_race")
        whole = g.p_model.transform(lambda s: s.notna().all()) & (g.race_key.transform("nunique") == 1)
        x = x[whole.values & (x.price > 1).values].copy()
        cov["priced"] = int(x.bw_race.nunique())
        if len(x):
            x["race_id"] = x.bw_race
            x["p_open"] = x.p_model / x.groupby("bw_race").p_model.transform("sum")
            x["pb"] = V1.blend(["p_open", "p_book"], x, np.asarray(HELD))[1]
            m, _, u = R9.horse_bets(x, x.pb.values, x.p_book.values, x.price.values.astype(float), 0.0, RATIO, BAND)
            for (_, r), units in zip(x[m].iterrows(), u[m]):
                c = pd.Series({"day": r.date, "venue": r.card_venue, "race_no": r.card_race_no, "box": r.box,
                               "dog_name": r.card_dog, "p_model": r.p_model, "grv_price": r.grv_price})
                add("open", c, r.pb, units, r)
    return pd.DataFrame(rows), cov


# ---- the report ---------------------------------------------------------------------------------------------------

def report(led: pd.DataFrame, cov: dict, days: list) -> None:
    """Counts and units only."""
    print(f"Cards settled: {len(days)} days ({days[0] if days else ''} to {days[-1] if days else ''}); "
          f"{cov['races']:,} card races, {cov['in_market']:,} of them found in TAB's market, "
          f"{cov['priced']:,} with every dog in TAB's field at its open on the card.\n")
    print("| way of betting | bets | void (not in TAB's market) | refunded | unsettled | settled | winners | expected "
          "at the price taken | A/E | units staked | units won | Kelly ROI | flat ROI | units won at the best first "
          "price of three | bets with a BSP | BSP under the price paid |\n|" + "---|" * 16)
    for v, name in VARIANTS.items():
        g = led[led.variant == v] if len(led) else led
        if g.empty:
            print(f"| {name} | 0 |" + " |" * 15)
            continue
        s = g[g.status.isin(["won", "lost"])]
        won = (s.status == "won").values
        exp = (1 / s.tab_first).sum()
        flat = np.where(won, s.paid - 1, -1.0).mean() if len(s) else np.nan
        b = s[s.bsp > 1]
        print(f"| {name} | {len(g)} | {g.status.str.startswith('void').sum()} | {g.status.str.startswith('refund').sum()} "
              f"| {g.status.str.startswith('unsettled').sum()} | {len(s)} | {int(won.sum())} | {exp:.2f} | "
              f"{won.sum() / exp if exp else np.nan:.2f} | {s.units.sum():.2f} | {s.units_won.sum():+.2f} | "
              f"{s.units_won.sum() / s.units.sum() if s.units.sum() else np.nan:+.1%} | "
              f"{'' if np.isnan(flat) else f'{flat:+.1%}'} | {s.units_won_best.sum():+.2f} | {len(b)} | "
              f"{(b.bsp < b.paid).sum()} |")
    if len(led):
        print("\n| day | card bets | settled | winners | units won | 1.3x still at TAB's open | rule at TAB's open: bets "
              "| settled | winners | units won |\n|---|---|---|---|---|---|---|---|---|---|")
        for d in days:
            a, s2, o = (led[(led.variant == v) & (led.day == d)] for v in ("card", "card_still", "open"))
            sa, so = a[a.status.isin(["won", "lost"])], o[o.status.isin(["won", "lost"])]
            print(f"| {d} | {len(a)} | {len(sa)} | {(sa.status == 'won').sum()} | {sa.units_won.sum():+.2f} | {len(s2)} | "
                  f"{len(o)} | {len(so)} | {(so.status == 'won').sum()} | {so.units_won.sum():+.2f} |")


def main(d, label):
    from greyhound.sealed import seal
    from zoneinfo import ZoneInfo
    print(f"# {label}: what the card would have taken at TAB's open\n")
    bdir, bf_dir = os.environ.get("BETWATCH_DIR", ""), os.environ.get("BETFAIR_DIR", "")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to settle")
        return 1
    today = pd.Timestamp.now(tz=ZoneInfo("Australia/Melbourne")).strftime("%Y-%m-%d")
    cards = cards_from_dir(os.environ.get("CARDS_DIR", ""))
    cards = cards[(cards.day < today) & (cards.day >= os.environ.get("TRACK_FROM", "0000"))]
    held = betwatch_days(bdir)
    waiting = sorted(set(cards.day) - held)
    if waiting:
        print(f"Cards waiting for Betwatch to hold their day: {', '.join(waiting)}\n")
    cards = cards[cards.day.isin(held)]
    days = sorted(cards.day.unique())
    facts = market_facts(d, bdir, bf_dir, days) if days else pd.DataFrame(columns=FACT_COLS)
    led, cov = ledger(cards, facts) if days else (pd.DataFrame(), {"races": 0, "in_market": 0, "priced": 0})
    report(led, cov, days)
    payload = {"ledger": json.loads(led.to_json(orient="records")) if len(led) else []}
    a, b = os.environ.get("FACTS_FROM", "").strip(), os.environ.get("FACTS_TO", "").strip() or today
    if a:
        extra = [x.strftime("%Y-%m-%d") for x in pd.date_range(a, b) if x.strftime("%Y-%m-%d") < today]
        extra = [x for x in extra if x not in set(days) and x in held]
        ef = market_facts(d, bdir, bf_dir, extra) if extra else pd.DataFrame(columns=FACT_COLS)
        payload["facts"] = json.loads(ef.to_json(orient="records"))
        print(f"\nMarket facts sealed for {len(extra)} days without a cached card: {ef.bw_race.nunique() if len(ef) else 0:,} "
              f"races, {len(ef):,} runners in TAB's field at its open, {int((ef.won.notna() & ef.ran.astype(bool)).sum()) if len(ef) else 0:,} "
              "that ran with a result")
    plain = json.dumps(payload, separators=(",", ":")).encode()
    lines, sha = seal(plain)
    print(f"\nThe bets are sealed (dogs and prices: GRV's and Betwatch's data stay private): {len(plain):,} bytes, "
          f"sha256 {sha}")
    print("\n".join(lines))
    return 0


def local(facts_path: str, card_paths: list) -> int:
    """Settle unsealed nightly cards against unsealed market facts; prints every bet (private copies only)."""
    p = json.load(open(facts_path))
    facts = pd.DataFrame(p.get("facts", p) if isinstance(p, dict) else p, columns=FACT_COLS)
    cards = pd.concat([cards_from_payload(json.load(open(c))) for c in card_paths], ignore_index=True)
    cards = cards[cards.day.isin(set(facts.date))]
    led, cov = ledger(cards, facts)
    report(led, cov, sorted(cards.day.unique()))
    if len(led):
        cols = ["variant", "day", "venue", "race_no", "box", "dog_name", "p_blend", "grv_price", "tab_first", "ded",
                "paid", "best_first", "bsp", "units", "status", "units_won"]
        print("\n" + led[cols].to_string(index=False))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--local":
        sys.exit(local(sys.argv[2], sys.argv[3:]))
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz live track"))
