"""Betwatch price history for Victorian greyhounds (founder, 13 Nov 2026: "We have betwatch").

Betwatch (Jamie Watts, founder, email of 13 Nov 2026):
  - history back to November 2022, every bookmaker's price changes ("flucs") with timestamps up to the jump, TAB
    included
  - the first price is the first one Betwatch picked up that day: usually close to the open, but it can miss a sharp
    early move, so it is not a guaranteed opening price
  - GraphQL rate limits are dynamic, so big pulls need pacing
  - using the data for our own models, not shared or resold, is fine

    python -m greyhound.betwatch probe
        counts only, for five sample days from Nov 2022 to now: what the API holds and when TAB's first price lands
    python -m greyhound.betwatch pull --from 2022-11 --to 2026-11 --dir greyhound/cache/betwatch [--max-minutes N]
        a month file at a time (betwatch_VIC_G_YYYY-MM.json.gz), resumable; a month is redone only if not complete

Nothing here prints a price, a dog or a time: the Actions log is public. The data lives in this repository's Actions
cache. Key: BETWATCH_API_KEY (an Actions secret), sent as the X-Api-Key header with an honest client name.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import statistics
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

URL = "https://api.betwatch.com/query"
AGENT = "fk-model greyhound research (python-requests)"
FLUC_BOOKIES = ("Tab", "Sportsbet", "Ladbrokes")
PAGE = 50
PAUSE = 1.0          # seconds between calls, so a long pull stays well inside Betwatch's dynamic limits
QUERY = """
query GetRaces($limit: Int, $offset: Int, $types: [RaceType!], $locations: [String!], $dateFrom: String!, $dateTo: String!) {
  races(limit: $limit, offset: $offset, types: $types, locations: $locations, dateFrom: $dateFrom, dateTo: $dateTo) {
    id name number status startTime actualStartTime results distance classConditions trackCondition
    meeting { id location track type date }
    runners {
      id name number barrier scratchedTime emergency
      bookmakerMarkets(bookmakers: [""], bookmakersWithFlucs: %s) {
        bookmaker fixedWin { price lastUpdated flucs { price lastUpdated } }
      }
    }
  }
}
""" % json.dumps(list(FLUC_BOOKIES))


class BetwatchError(RuntimeError):
    pass


def _post(session: requests.Session, variables: dict, tries: int = 6) -> list:
    """One page of races; retries a 429, a 5xx or a dropped connection with backoff, and stops loudly on anything
    else (an empty page from an error must never be filed as a day with no races)."""
    wait = 5.0
    for attempt in range(tries):
        try:
            r = session.post(URL, json={"query": QUERY, "variables": variables}, timeout=120)
        except requests.RequestException as e:
            err = f"connection: {type(e).__name__}"
        else:
            if r.status_code == 200:
                body = r.json()
                if body.get("errors"):
                    msgs = "; ".join(str(e.get("message", ""))[:160] for e in body["errors"])
                    if "rate" in msgs.lower() or "too many" in msgs.lower():
                        err = f"rate limited: {msgs}"
                    else:
                        raise BetwatchError(f"GraphQL error: {msgs}")
                else:
                    return (body.get("data") or {}).get("races") or []
            elif r.status_code in (401, 403):
                raise BetwatchError(f"HTTP {r.status_code}: the key was refused (BETWATCH_API_KEY)")
            elif r.status_code == 429 or r.status_code >= 500:
                err = f"HTTP {r.status_code}"
            else:
                raise BetwatchError(f"HTTP {r.status_code}: {r.text[:200]}")
        if attempt < tries - 1:
            print(f"  retry {attempt + 1} after {err}, waiting {wait:.0f}s")
            time.sleep(wait)
            wait = min(wait * 2, 300)
    raise BetwatchError(f"gave up after {tries} tries: {err}")


def fetch_day(session: requests.Session, day: str) -> list[dict]:
    """Every Victorian greyhound race on `day` (YYYY-MM-DD), paged."""
    races, offset = [], 0
    while True:
        page = _post(session, {"limit": PAGE, "offset": offset, "types": ["Greyhound"], "locations": ["VIC"],
                               "dateFrom": day, "dateTo": day})
        races.extend(page)
        if len(page) < PAGE:
            return races
        offset += PAGE
        time.sleep(PAUSE)


def _ts(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def compact(race: dict) -> dict:
    """The race in the shape we keep: race fields, and per runner each bookmaker's flucs as [price, time] pairs in
    time order (TAB, Sportsbet, Ladbrokes) or its last price only (the rest)."""
    m = race.get("meeting") or {}
    out = {"id": race.get("id"), "date": m.get("date"), "track": m.get("track"), "location": m.get("location"),
           "number": race.get("number"), "name": race.get("name"), "status": race.get("status"),
           "start": race.get("startTime"), "actual_start": race.get("actualStartTime"),
           "distance": race.get("distance"), "results": race.get("results"), "runners": []}
    for ru in race.get("runners") or []:
        books = {}
        for bm in ru.get("bookmakerMarkets") or []:
            fw = bm.get("fixedWin") or {}
            fl = sorted(([f.get("price"), f.get("lastUpdated")] for f in (fw.get("flucs") or [])
                         if f.get("price") and f.get("lastUpdated")), key=lambda x: x[1])
            books[bm.get("bookmaker")] = {"last": [fw.get("price"), fw.get("lastUpdated")], "flucs": fl}
        out["runners"].append({"id": ru.get("id"), "number": ru.get("number"), "barrier": ru.get("barrier"),
                               "name": ru.get("name"), "scratched": ru.get("scratchedTime"),
                               "emergency": ru.get("emergency"), "books": books})
    return out


def first_price(runner: dict, bookie: str = "Tab"):
    """(price, time) of the bookmaker's first recorded fluc, or None."""
    fl = ((runner.get("books") or {}).get(bookie) or {}).get("flucs") or []
    return (fl[0][0], fl[0][1]) if fl else None


def day_counts(races: list[dict]) -> dict:
    """Counts only: races, runners, TAB coverage, flucs a runner, and when TAB's first price came against the jump."""
    rows = [compact(r) for r in races]
    runners = [ru for r in rows for ru in r["runners"] if not ru.get("scratched")]
    tab = [ru for ru in runners if first_price(ru)]
    lead, nfl = [], []
    for r in rows:
        st = _ts(r["start"])
        for ru in r["runners"]:
            fp = first_price(ru)
            if ru.get("scratched") or not fp:
                continue
            nfl.append(len(ru["books"]["Tab"]["flucs"]))
            t = _ts(fp[1])
            if st and t:
                lead.append((st - t).total_seconds() / 3600)
    books = {}
    for ru in runners:
        for b, v in ru["books"].items():
            if v["flucs"] or v["last"][0]:
                books[b] = books.get(b, 0) + 1
    q = (lambda xs, p: sorted(xs)[min(len(xs) - 1, int(p * len(xs)))]) if lead else None
    return {"races": len(rows), "tracks": len({r["track"] for r in rows}), "runners": len(runners),
            "with_tab_flucs": len(tab),
            "tab_flucs_median": statistics.median(nfl) if nfl else None,
            "hours_first_tab_before_jump": None if not lead else
            {"p10": round(q(lead, 0.1), 1), "median": round(q(lead, 0.5), 1), "p90": round(q(lead, 0.9), 1)},
            "first_tab_after_jump": sum(1 for x in lead if x < 0),
            "bookmakers_on_10pct_of_runners": sorted(b for b, n in books.items() if n >= 0.1 * max(len(runners), 1))}


def months(a: str, b: str) -> list[str]:
    y, m = map(int, a.split("-"))
    y2, m2 = map(int, b.split("-"))
    out = []
    while (y, m) <= (y2, m2):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def month_days(month: str, today: date) -> list[str]:
    y, m = map(int, month.split("-"))
    d = date(y, m, 1)
    out = []
    while d.month == m and d < today:
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _session() -> requests.Session:
    key = os.environ.get("BETWATCH_API_KEY", "").strip()
    if not key:
        raise SystemExit("BETWATCH_API_KEY is not set (add it as an Actions secret)")
    s = requests.Session()
    s.headers.update({"X-Api-Key": key, "User-Agent": AGENT, "Content-Type": "application/json"})
    return s


def probe(days: list[str]) -> int:
    s = _session()
    print("# Betwatch probe: Victorian greyhounds, counts only\n")
    print("| day | races | tracks | runners | with TAB flucs | TAB flucs a runner (median) | hours from TAB's first "
          "price to the jump (p10 / median / p90) | first TAB price after the jump | bookmakers on 10%+ of runners |\n"
          "|---|---|---|---|---|---|---|---|---|")
    keys_shown = False
    for d in days:
        try:
            races = fetch_day(s, d)
        except BetwatchError as e:
            print(f"| {d} | refused: {str(e)[:150]} | | | | | | | |")
            continue
        c = day_counts(races)
        h = c["hours_first_tab_before_jump"]
        hs = "" if not h else f"{h['p10']} / {h['median']} / {h['p90']}"
        print(f"| {d} | {c['races']} | {c['tracks']} | {c['runners']} | {c['with_tab_flucs']} | {c['tab_flucs_median']} | "
              f"{hs} | {c['first_tab_after_jump']} | "
              f"{', '.join(c['bookmakers_on_10pct_of_runners'])} |")
        if races and not keys_shown:
            ru = (races[0].get("runners") or [{}])[0]
            print(f"\nfield names: race {sorted(races[0])}; runner {sorted(ru)}; market "
                  f"{sorted((ru.get('bookmakerMarkets') or [{}])[0])}\n")
            keys_shown = True
        time.sleep(PAUSE)
    return 0


def pull(a: str, b: str, out_dir: Path, max_minutes: float) -> int:
    s = _session()
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    today = datetime.now(ZoneInfo("Australia/Melbourne")).date()
    print(f"# Betwatch pull {a} to {b}: Victorian greyhounds, counts only\n")
    print("| month | days | races | runners | with TAB flucs | status |\n|---|---|---|---|---|---|")
    for mo in months(a, b):
        f = out_dir / f"betwatch_VIC_G_{mo}.json.gz"
        days = month_days(mo, today)
        prior = {}
        if f.exists():
            prior = json.load(gzip.open(f, "rt", encoding="utf-8"))
            if prior.get("complete") and set(prior.get("days", [])) >= set(days):
                continue
        done, races = set(prior.get("days", [])), list(prior.get("races", []))
        status = "complete"
        for d in days:
            if d in done:
                continue
            if (time.monotonic() - t0) / 60 > max_minutes:
                status = "partial: time budget"
                break
            try:
                races.extend(compact(r) for r in fetch_day(s, d))
            except BetwatchError as e:
                status = f"partial: {str(e)[:120]}"
                break
            done.add(d)
            time.sleep(PAUSE)
        with gzip.open(f, "wt", encoding="utf-8") as fh:
            json.dump({"month": mo, "days": sorted(done), "complete": status == "complete", "races": races}, fh)
        runners = [ru for r in races for ru in r["runners"] if not ru.get("scratched")]
        print(f"| {mo} | {len(done)} of {len(days)} | {len(races):,} | {len(runners):,} | "
              f"{sum(1 for ru in runners if first_price(ru)):,} | {status} |")
        if status != "complete":
            break
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["probe", "pull"])
    p.add_argument("--days", default="2022-11-15,2023-11-14,2024-11-12,2025-11-11,2026-11-10")
    p.add_argument("--from", dest="a", default="2022-11")
    p.add_argument("--to", dest="b", default=datetime.now().strftime("%Y-%m"))
    p.add_argument("--dir", default="greyhound/cache/betwatch")
    p.add_argument("--max-minutes", type=float, default=300)
    a = p.parse_args(argv)
    if a.mode == "probe":
        return probe(a.days.split(","))
    return pull(a.a, a.b, Path(a.dir), a.max_minutes)


if __name__ == "__main__":
    sys.exit(main())
