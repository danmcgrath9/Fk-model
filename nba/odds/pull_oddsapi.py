"""The Odds API: historical player-prop prices, every book, through the day, for backtesting.

Built and tested BEFORE a key exists, so the paid month is spent pulling, not debugging.
Endpoints (the-odds-api.com/liveapi/guides/v4, checked 21 Oct 2026):
  GET /v4/historical/sports/{sport}/events?date=...           1 credit (0 if no events)
  GET /v4/historical/sports/{sport}/events/{id}/odds?date=...  10 x markets RETURNED x regions;
      an empty answer costs nothing. Props from 2023-05-03, snapshots every 5 minutes; the
      reply is the closest snapshot at or before `date`.
Every reply carries x-requests-last / x-requests-remaining; both are logged per call.

Modes (python nba/odds/pull_oddsapi.py <mode> ...), all driven by nba/odds/request.json:
  probe            a few calls (~200 credits): which books and regions carry NBA props at
                   two hours and a day out, and which AFL prop market keys return data
  pull YYYY-MM     every game in that month: a ladder of snapshots before tip-off, plus a
                   short search for the opening snapshot (empty probes are free)
  estimate         no calls: the credit bill for the request, worst case

Money rules: a hard cap per job (max_credits), never below `floor` credits left on the
account, and anything already saved is never bought twice. The key comes from the
ODDS_API_KEY secret and is never printed (URLs are logged without it).
"""
from __future__ import annotations

import csv
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = "https://api.the-odds-api.com/v4"
FIELDS = ["event_id", "commence", "home", "away", "requested", "snapshot", "book", "market",
          "player", "side", "point", "price", "last_update"]


def iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


class OutOfBudget(Exception):
    pass


class Client:
    """Thin HTTP client with the money rules. `fetch` is swappable for tests."""

    def __init__(self, key: str, max_credits: int, floor: int, ledger: Path, fetch=None, pause=0.3):
        self.key, self.max, self.floor, self.ledger = key, max_credits, floor, ledger
        self.spent, self.remaining, self.pause = 0, None, pause
        self.fetch = fetch or self._fetch

    def _fetch(self, url: str):
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r), {k.lower(): v for k, v in r.headers.items()}

    def get(self, path: str, worst_cost: int, **params):
        if self.spent + worst_cost > self.max:
            raise OutOfBudget(f"run cap: spent {self.spent}, next call could cost {worst_cost}")
        if self.remaining is not None and self.remaining - worst_cost < self.floor:
            raise OutOfBudget(f"account floor: {self.remaining} left")
        q = urllib.parse.urlencode({**params, "apiKey": self.key})
        shown = f"{path}?{urllib.parse.urlencode(params)}"
        for attempt in range(4):
            try:
                body, headers = self.fetch(f"{BASE}{path}?{q}")
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 3:            # rate limited: back off
                    time.sleep(2 ** (attempt + 1))
                    continue
                if e.code in (401, 403):
                    raise SystemExit(f"Odds API refused the key (HTTP {e.code}). Nothing more is called.")
                raise
        last = int(headers.get("x-requests-last", 0) or 0)
        rem = headers.get("x-requests-remaining")
        self.remaining = int(float(rem)) if rem not in (None, "") else self.remaining
        self.spent += last
        new = not self.ledger.exists()
        with self.ledger.open("a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["utc", "call", "credits_last", "credits_remaining"])
            w.writerow([iso(datetime.now(timezone.utc)), shown, last, self.remaining])
        time.sleep(self.pause)
        return body


def events_on(client: Client, sport: str, day: str, day_start_utc_hour: int) -> list[dict]:
    """Games starting in one local game day (US: 12:00Z to 12:00Z next day covers every
    tip-off from noon Eastern to the late West Coast games)."""
    start = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(hours=day_start_utc_hour)
    body = client.get(f"/historical/sports/{sport}/events", worst_cost=1, date=iso(start + timedelta(hours=3)),
                      commenceTimeFrom=iso(start), commenceTimeTo=iso(start + timedelta(hours=24)))
    return body.get("data", []) if isinstance(body, dict) else []


def odds_rows(body: dict, requested: str) -> list[dict]:
    d = body.get("data") or {}
    rows = []
    for bk in d.get("bookmakers", []):
        for mk in bk.get("markets", []):
            for o in mk.get("outcomes", []):
                rows.append({"event_id": d.get("id"), "commence": d.get("commence_time"),
                             "home": d.get("home_team"), "away": d.get("away_team"),
                             "requested": requested, "snapshot": body.get("timestamp"),
                             "book": bk.get("key"), "market": mk.get("key"),
                             "player": o.get("description", ""), "side": o.get("name"),
                             "point": o.get("point"), "price": o.get("price"),
                             "last_update": mk.get("last_update") or bk.get("last_update")})
    return rows


def snapshot(client: Client, sport: str, event_id: str, when: datetime, regions: list[str], markets: list[str]):
    body = client.get(f"/historical/sports/{sport}/events/{event_id}/odds",
                      worst_cost=10 * len(regions) * len(markets), date=iso(when),
                      regions=",".join(regions), markets=",".join(markets), oddsFormat="decimal")
    return odds_rows(body, iso(when)) if isinstance(body, dict) else []


def pull_event(client, sport, ev, req) -> list[dict]:
    """Ladder of snapshots before tip-off; then narrow the gap between the last empty and
    the first priced rung to find the opening snapshot (empty probes are free)."""
    commence = parse_iso(ev["commence_time"])
    rows, first_hit, last_empty = [], None, None
    for mins in sorted(req["ladder_minutes_before"], reverse=True):
        t = commence - timedelta(minutes=mins)
        got = snapshot(client, sport, ev["id"], t, req["regions"], req["markets"])
        if got:
            rows += got
            first_hit = first_hit or t
        elif first_hit is None:
            last_empty = t
    if req.get("open_search_steps") and first_hit and last_empty:
        lo, hi = last_empty, first_hit
        for _ in range(req["open_search_steps"]):
            if hi - lo <= timedelta(minutes=10):
                break
            mid = lo + (hi - lo) / 2
            got = snapshot(client, sport, ev["id"], mid, req["regions"], req["markets"])
            if got:
                rows += got
                hi = mid
            else:
                lo = mid
    return rows


def write_rows(path: Path, rows: list[dict]) -> None:
    new = not path.exists()
    with gzip.open(path, "at", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerows(rows)


def game_days(req: dict, month: str) -> list[str]:
    if req.get("game_days_file"):
        days = json.loads((HERE.parent / req["game_days_file"]).read_text())["days"]
        return sorted(d for v in days.values() for d in v if d.startswith(month))
    y, m = map(int, month.split("-"))
    d, out = datetime(y, m, 1), []
    while d.month == m:
        out.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)
    return out


def pull_month(client: Client, req: dict, month: str) -> None:
    sport = req["sport"]
    out = HERE / "raw" / sport
    out.mkdir(parents=True, exist_ok=True)
    data, done_path = out / f"{month}.csv.gz", out / f"{month}_done.json"
    done = set(json.loads(done_path.read_text())) if done_path.exists() else set()
    for day in game_days(req, month):
        for ev in events_on(client, sport, day, req.get("day_start_utc_hour", 12)):
            if ev["id"] in done:
                continue
            rows = pull_event(client, sport, ev, req)
            write_rows(data, rows)
            done.add(ev["id"])
            done_path.write_text(json.dumps(sorted(done)))
            print(f"{day} {ev['away_team']} @ {ev['home_team']}: {len(rows)} prices "
                  f"(run spent {client.spent}, account left {client.remaining})")
    (out / f"{month}_complete").write_text(f"spent {client.spent}\n")   # the workflow skips finished months


def probe(client: Client, req: dict) -> dict:
    report = {}
    p = req["probe"]
    nba = events_on(client, "basketball_nba", p["nba_day"], 12)[:1]
    for ev in nba:
        c = parse_iso(ev["commence_time"])
        for label, mins in [("2h before", 120), ("24h before", 1440)]:
            rows = snapshot(client, "basketball_nba", ev["id"], c - timedelta(minutes=mins), ["us", "au"],
                            req["markets"])
            books = {}
            for r in rows:
                books.setdefault(r["book"], set()).add(r["market"])
            report[f"NBA {ev['away_team']} @ {ev['home_team']} {label}"] = {
                b: sorted(m) for b, m in sorted(books.items())}
    afl = events_on(client, "aussierules_afl", p["afl_day"], p.get("afl_day_start_utc_hour", 0))[:1]
    for ev in afl:
        c = parse_iso(ev["commence_time"])
        found = {}
        for mk in p["afl_candidate_markets"]:
            rows = snapshot(client, "aussierules_afl", ev["id"], c - timedelta(minutes=120), ["au"], [mk])
            found[mk] = sorted({r["book"] for r in rows})
        report[f"AFL {ev['away_team']} @ {ev['home_team']} 2h before"] = found
    report["credits spent"] = client.spent
    report["credits left on account"] = client.remaining
    return report


def estimate(req: dict) -> None:
    """Worst case: every rung and every open-search step returns every market."""
    games = int(sum(len(game_days(req, m)) for m in req["months"]) * req.get("games_per_day", 8))
    calls = len(req["ladder_minutes_before"]) + req.get("open_search_steps", 0)
    per_call = 10 * len(req["regions"]) * len(req["markets"])
    days = sum(len(game_days(req, m)) for m in req["months"])
    print(f"{len(req['months'])} months, ~{games:,} games, {calls} snapshots each, up to {per_call} credits a "
          f"snapshot: worst case {games * calls * per_call + days:,} credits. Empty early snapshots are free, "
          f"so the real bill is lower.")


def main(argv: list[str]) -> int:
    req = json.loads((HERE / "request.json").read_text())
    mode = argv[0] if argv else req.get("mode", "estimate")
    if mode == "estimate":
        estimate(req)
        return 0
    key = os.environ.get("ODDS_API_KEY", "")
    if not key:
        print("SKIPPED: ODDS_API_KEY is not set (save it as a secret in the 'Odds API' environment). "
              "Nothing called, nothing spent.")
        return 0
    # one ledger per job, so parallel month jobs never edit the same file
    ledger = HERE / "probe_ledger.csv" if mode == "probe" else HERE / "raw" / req["sport"] / f"{argv[1]}_ledger.csv"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    client = Client(key, int(req["max_credits"]), int(req.get("floor", 1000)), ledger)
    try:
        if mode == "probe":
            rep = probe(client, req)
            (HERE / "probe.json").write_text(json.dumps(rep, indent=1))
            print(json.dumps(rep, indent=1))
        elif mode == "pull":
            pull_month(client, req, argv[1])
    except OutOfBudget as e:
        print(f"STOPPED, budget: {e}")
    print(f"Credits spent this run: {client.spent}; left on the account: {client.remaining}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
