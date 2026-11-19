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
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)   # polls every few seconds, one line each

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_best                 # noqa: E402
import topaz_iso                  # noqa: E402
import topaz_round33 as R33       # noqa: E402
import topaz_track as T           # noqa: E402
from greyhound import betwatch as B   # noqa: E402

MEL = ZoneInfo("Australia/Melbourne")
BLEND, BEST = "corrected blend", "best model"


def latest_prices(races: list) -> dict:
    """(venue, race number, normalised name) -> TAB's latest price and when, and Sportsbet's and Ladbrokes' latest."""
    out = {}
    for r in races:
        for ru in r.get("runners", []):
            b = ru.get("books") or {}
            tab = sorted(((b.get("Tab") or {}).get("flucs") or []), key=lambda f: str(f[1]))
            out[(r.get("track"), str(r.get("number")), T.norm(pd.Series([ru.get("name") or ""]))[0])] = {
                "number": ru.get("number"), "bw_race": r.get("id"),
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


def full_fields(races: list) -> set:
    """Races whose every runner not scratched has a TAB price. Only these are priced: a part-priced field would put
    the whole book on the dogs TAB has priced so far."""
    out = set()
    for r in races:
        live = [ru for ru in r.get("runners", []) if not ru.get("scratched")]
        if live and all(((ru.get("books") or {}).get("Tab") or {}).get("flucs") for ru in live):
            out.add(r.get("id"))
    return out


def detect(x: pd.DataFrame, races: list, now: datetime, day: str) -> list:
    """The bets of the races just priced, each with when it was seen and TAB's price then (its latest), and whether that
    price still cleared 1.1x: the paper bet is placed at that price, or missed."""
    stamp = now.astimezone(timezone.utc).isoformat(timespec="seconds")
    out = []
    for b in morning_bets(x, latest_prices(races)):
        p = b.get("tab_now")
        out.append({**b, "model": BLEND, "day": day, "detected_at": stamp, "tab_at_detect": p,
                    "placed": bool(p is not None and float(p) >= b["need_11"])})
    return out


def best_detect(xb: pd.DataFrame, races: list, now: datetime, day: str) -> list:
    """The best model's bets in the races just priced: the 2-point margin at TAB's first price, our fair price under
    $15, the price it needs (1 / (our chance - 2 points)), the quarter-Kelly share of the bank; placed at TAB's price
    when seen if that still needs no more than it, else missed."""
    if xb is None or xb.empty or "best_bet" not in xb:
        return []
    stamp = now.astimezone(timezone.utc).isoformat(timespec="seconds")
    lp = latest_prices(races)
    out = []
    for _, r in xb[xb.best_bet.values].iterrows():
        p = float(r.p_best)
        need = round(1 / (p - topaz_best.MARGIN), 2)
        now_p = lp.get((r.venue, str(r.race_no), T.norm(pd.Series([r.dog_name or ""]))[0]), {})
        tp = now_p.get("tab_now")
        out.append({"model": BEST, "venue": r.venue, "race_no": str(r.race_no), "start": r.start,
                    "box": str(r.card_box), "dog": r.card_dog, "fair": round(1 / p, 3), "need": need,
                    "kelly": round(float(r.best_kelly), 4), "tab_open": float(r.price), "tab_open_at": r.tab_first_t,
                    **now_p, "day": day, "detected_at": stamp, "tab_at_detect": tp,
                    "placed": bool(tp is not None and float(tp) >= need)})
    return sorted(out, key=lambda b: str(b["start"]))


def settle(rows: list, races: list) -> list:
    """Each placed paper bet settled on Betwatch's result: one unit at TAB's price when it was seen, less TAB's deduction
    for the dogs scratched after its first price. A race with no result yet stays unsettled."""
    byid = {r.get("id"): r for r in races}
    out = []
    for b in rows:
        if not b.get("placed") or b.get("settled"):
            out.append(b)
            continue
        r = byid.get(b.get("bw_race"))
        res = (r or {}).get("results")
        if not r or not res:
            out.append(b)
            continue
        first = res[0] if isinstance(res[0], list) else [res[0]]
        won = str(b.get("number")) in {str(v) for v in first}
        fr = R33.field_rows(r, times=(0,))
        ded = float(fr[0]["ded"]) if fr else 0.0
        paid = 1 + (float(b["tab_at_detect"]) - 1) * (1 - ded)
        out.append({**b, "settled": True, "won": won, "ded": ded, "paid": round(paid, 4),
                    "profit": round(paid - 1, 4) if won else -1.0})
    return out


def by_model(rows: list) -> str:
    """Each model's summary on one line ('corrected blend' for rows from before the best model)."""
    models = sorted({b.get("model", BLEND) for b in rows}, key=lambda m: (m != BEST, m))
    return "; ".join(f"{m}: " + summary([b for b in rows if b.get("model", BLEND) == m]) for m in models) or "no bets"


def summary(rows: list) -> str:
    """Counts and units only (the log is public)."""
    placed = [b for b in rows if b.get("placed")]
    st = [b for b in placed if b.get("settled")]
    units = sum(b["profit"] for b in st)
    return (f"{len(rows)} bets seen, {len(placed)} placed ({len(rows) - len(placed)} missed: TAB had cut the price "
            f"below the price it needed by then), {len(st)} settled, {sum(b['won'] for b in st)} won, {units:+.2f} units "
            f"({units / len(st):+.1%} a bet)" if st else
            f"{len(rows)} bets seen, {len(placed)} placed, none settled yet")


def feed_health(races: list) -> dict:
    """Counts only, for the public log: today's races and runners not scratched, how many of them TAB has priced, and
    how many any bookmaker has priced. A morning with no TAB price is told apart from a morning with no bet."""
    rn = [(r.get("id"), ru) for r in races for ru in r.get("runners", []) if not ru.get("scratched")]
    tab = [i for i, ru in rn if ((ru.get("books") or {}).get("Tab") or {}).get("flucs")]
    priced = sum(1 for _, ru in rn if any((b or {}).get("flucs") or ((b or {}).get("last") or [None])[0]
                                          for b in (ru.get("books") or {}).values()))
    return {"races": len(races), "runners": len(rn), "tab_runners": len(tab), "tab_races": len(set(tab)),
            "any_runners": priced}


def health_line(h: dict) -> str:
    return (f"TAB has priced {h.get('tab_races', 0)} of {h.get('races', 0)} races ({h.get('tab_runners', 0)} of "
            f"{h.get('runners', 0)} runners); any bookmaker {h.get('any_runners', 0)} runners")


def race_opened_at(r: dict) -> datetime | None:
    """When Betwatch first showed a TAB price in this race (its earliest TAB fluc), or None."""
    ts = [B._ts(f[1]) for ru in r.get("runners", []) for f in (((ru.get("books") or {}).get("Tab") or {}).get("flucs")
                                                                or []) if f and len(f) > 1]
    ts = [t for t in ts if t is not None]
    return min(ts) if ts else None


def delay_line(lags: list) -> str:
    """The delay from Betwatch's first TAB price in a race to that race's bets being ready, in seconds."""
    if not lags:
        return "No race priced, so no delay to measure"
    a = np.sort(np.asarray(lags, float))
    return (f"From Betwatch's first TAB price in a race to its bets being ready: median {np.median(a):.0f} seconds, "
            f"9 in 10 within {np.quantile(a, 0.9):.0f}, longest {a[-1]:.0f} ({len(a)} races)")


def watch(day: str, cards, bst, meta, until: datetime, every: float, fetch, clock=None, sleep=time.sleep,
          best=None, late: datetime | None = None, after_open: float = 60, fast: float | None = None,
          fast_for: float = 10, timer=time.monotonic) -> tuple:
    """Poll today's races until `until`, pricing each race the first time TAB has priced its whole field: the corrected
    blend, and the best model when `best` is (booster, meta, Betwatch history).

    TAB's open is the bet, whenever it comes (19 Nov 2026: at 8:38am Betwatch showed no price from any bookmaker on 390
    runners, against 338 of 338 by 8am the day before). So when `late` is later than `until`, the watch runs past
    `until`: to `late` until TAB has opened (priced half the day's races), else to `after_open` minutes after the poll
    that first saw it open, never past `late`. (bets, polls, races priced, the last poll's feed_health with
    'first_open', the poll time that first saw TAB open, and 'lags', 'fetch_s', 'price_s': the seconds from each
    race's first TAB price to its bets being ready, and each poll's fetching and pricing time).

    The edge goes in the first minutes after TAB's open (Test 95), so the polls run start to start, `every` seconds
    apart (19 Nov: a 45-second wait AFTER each poll's fetch and pricing made 50 to 62 seconds), and `fast` seconds
    apart for `fast_for` minutes after a poll that saw a race newly priced by TAB or newly full, while any race is
    still to price."""
    clock = clock or (lambda: datetime.now(MEL))
    seen, bets, polls = set(), [], 0
    first_open, shown, h = None, None, {}
    moved, lags, fetch_s, price_s = None, [], [], []

    def stop_at() -> datetime:
        if late is None or late <= until:
            return until
        if first_open is None:
            return late
        return min(late, max(until, first_open + timedelta(minutes=after_open)))

    while clock() < stop_at():
        t_start = timer()
        races = fetch()
        polls += 1
        now = clock()
        fetch_s.append(timer() - t_start)
        h = feed_health(races)
        if first_open is None and h["races"] and 2 * h["tab_races"] >= h["races"]:
            first_open = now                  # TAB's open: half the day's races priced (19 Nov: 3 stray runners at 6:25)
        full = full_fields(races)
        if (h["tab_races"], len(full)) != shown:
            if shown is not None or h["tab_races"]:
                moved = now                   # a race newly priced by TAB, or newly full: TAB is opening races
            shown = (h["tab_races"], len(full))
            print(f"{now:%H:%M:%S} poll {polls}: {health_line(h)}; {len(full)} fields full")
        full -= seen
        facts = T.open_field(races)
        if len(facts) and full:
            t_price = timer()
            facts = facts[facts.bw_race.isin(full)]
            x = topaz_iso.at_open(facts, cards, bst, meta) if len(facts) else pd.DataFrame()
            if len(x):
                new = detect(x, races, now, day)
                if best is not None and best[1] is not None:
                    new += best_detect(topaz_best.at_open(x, *best), races, now, day)
                bets += new
                done = set(x.bw_race.unique())
                took = timer() - t_price
                price_s.append(took)
                for r in races:
                    o = race_opened_at(r) if r.get("id") in done else None
                    if o is not None:
                        lags.append((now - o).total_seconds() + took)
                seen |= done
                print(f"{now:%H:%M:%S} poll {polls}: {len(set(x.bw_race.unique()))} race(s) priced, {len(new)} bet(s) "
                      f"({sum(b['placed'] for b in new)} still at the price); {len(seen)} races priced today")
        quick = (fast is not None and moved is not None and now < moved + timedelta(minutes=fast_for)
                 and len(seen) < h.get("races", 0))
        sleep(max(1.0, (fast if quick else every) - (timer() - t_start)))
    return bets, polls, seen, {**h, "first_open": first_open, "lags": lags, "fetch_s": fetch_s, "price_s": price_s}


def ledger_path() -> Path:
    return Path(os.environ.get("MORNING_DIR", "greyhound/cache/morning")) / "ledger.json"


def run_watch(day: str, cards, bst, meta) -> int:
    """Settle the earlier days, watch today until MORNING_UNTIL (Melbourne, default 08:20), or later when TAB opens
    late (MORNING_LATE, default 09:50; see watch), keep the ledger, seal it."""
    from greyhound import sealed
    lp = ledger_path()
    ledger = json.loads(lp.read_text()) if lp.exists() else []
    session = B._session()
    open_days = sorted({b["day"] for b in ledger if b.get("placed") and not b.get("settled") and b["day"] < day})
    for d in open_days[-7:]:
        races = [B.compact(r) for r in B.fetch_day(session, d)]
        mine = [b for b in ledger if b["day"] == d]
        rest = [b for b in ledger if b["day"] != d]
        ledger = rest + settle(mine, races)
    for d in sorted({b["day"] for b in ledger})[-14:]:
        print(f"{d}: " + by_model([b for b in ledger if b["day"] == d]))
    if ledger:
        print("All days: " + by_model(ledger))
    best = None
    bb, bm = topaz_best.load_best()
    bdir = os.environ.get("BETWATCH_DIR", "")
    if bm is None:
        print("No best model yet (best_meta.json in MODEL_DIR): the corrected blend only")
    elif not bdir or not os.path.isdir(bdir):
        print("No Betwatch history (BETWATCH_DIR): the best model is left out")
    else:
        import topaz_round65 as R65
        hist = topaz_best.runs_history(R65.tab_and_books(bdir))
        best = (bb, bm, topaz_best.mh_table(hist))     # built once, so a poll at TAB's open prices in seconds
        print(f"The best model: {bm.get('rounds', 0)} rounds, trained {bm.get('trained', '?')}; "
              f"{len(hist):,} Betwatch runs of history")
    hh, mm = (int(v) for v in os.environ.get("MORNING_UNTIL", "08:20").split(":"))
    until = datetime.now(MEL).replace(hour=hh, minute=mm, second=0, microsecond=0)
    every = float(os.environ.get("MORNING_EVERY", "30") or 30)
    fast = float(os.environ.get("MORNING_FAST", "10") or 10)
    today = []
    fh, fm = (int(v) for v in os.environ.get("MORNING_FROM", "06:45").split(":"))
    start = datetime.now(MEL).replace(hour=fh, minute=fm, second=0, microsecond=0)
    if datetime.now(MEL) < start and not any(b["day"] == day for b in ledger):
        time.sleep((start - datetime.now(MEL)).total_seconds())     # a start in standard time comes an hour early
    if datetime.now(MEL) < until and not any(b["day"] == day for b in ledger):
        print(f"\nWatching {day} until {until:%H:%M} Melbourne, every {every:.0f} seconds, and every {fast:.0f} "
              "while TAB is opening races")
        lh, lm = (int(v) for v in os.environ.get("MORNING_LATE", "09:50").split(":"))
        late = datetime.now(MEL).replace(hour=lh, minute=lm, second=0, microsecond=0)
        if late > until:
            print(f"If TAB has not opened by then, watching on to {late:%H:%M} at the latest")
        today, polls, seen, h = watch(day, cards, bst, meta, until, every,
                                      lambda: [B.compact(r) for r in B.fetch_day(session, day)], best=best, late=late,
                                      fast=fast)
        print(f"{polls} polls, {len(seen)} races priced. {day}: " + by_model(today))
        fo = h.get("first_open")
        print(f"At the last poll: {health_line(h)}. TAB open (half the races priced) first seen: "
              + (f"{fo:%H:%M}" if fo else "never") + ".")
        print(delay_line(h.get("lags", [])) + ". A poll's fetch took a median "
              f"{np.median(h['fetch_s']) if h.get('fetch_s') else 0:.1f} seconds; pricing the races it found full, a "
              f"median {np.median(h['price_s']) if h.get('price_s') else 0:.1f}.")
        if not h.get("tab_runners"):
            print("NO TAB PRICE: Betwatch showed none for today's races all morning, so nothing could be priced. The "
                  "feed, or TAB, was late; this is not a day without a bet.")
        ledger += today
    lp.parent.mkdir(parents=True, exist_ok=True)
    lp.write_text(json.dumps(ledger, default=str))
    lines, sha = sealed.seal(json.dumps({"day": day, "today": today, "ledger": ledger}, default=str).encode())
    print(f"sealed, sha256 {sha}")
    print("\n".join(lines))
    return 0


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
    if os.environ.get("MORNING_MODE", "").strip() == "watch":
        return run_watch(day, cards, bst, meta)
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
