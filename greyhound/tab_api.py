"""TAB's own racing information service, for the OPENING price of every runner (5 Nov 2026, founder's screenshots of
the TAB app at 7:47am: each runner carries "Open 1.95 > Today 1.95 > -28m 1.55 > -28m 1.50 > Fixed 1.45", so TAB
keeps the open and the price moves, and its app reads them from an API).

    python -m greyhound.tab_api probe  [--date YYYY-MM-DD] [--jurisdiction VIC]   # field NAMES of a runner's prices,
                                                                                   # then open / current per runner
    python -m greyhound.tab_api record --out DIR [--date YYYY-MM-DD]               # one CSV of the day's VIC greyhound
                                                                                   # opens, every runner

The base URL and the first path are the public tab-info-service that TAB's own website calls
(api.beta.tab.com.au/v1/tab-info-service/racing/dates/{date}/meetings?jurisdiction=VIC); every path after that is
taken from the `_links` the answers carry, never typed from memory. Which fields hold the open is what the probe
prints, as names; the code reads `returnWinOpen`, `returnWinOpenDaily`, `flucs` and `returnWin` IF they exist and
leaves a column empty otherwise. No bet, no login, read-only. Egress: blocked from the cloud session, open from a
GitHub runner.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

BASE = "https://api.beta.tab.com.au/v1/tab-info-service"
BASES = (BASE, "https://api.tab.com.au/v1/tab-info-service")
# an honest client identity: if TAB chooses not to serve a script, the probe reports that and we stop
HEADERS = {"accept": "application/json", "user-agent": "fk-model greyhound opens recorder (github.com/danmcgrath9/Fk-model)"}
SYDNEY = timezone(timedelta(hours=11))
OPEN_FIELDS = ("returnWinOpen", "returnWinOpenDaily", "returnWin", "returnPlace", "bettingStatus")


class TabClient:
    def __init__(self, session=None, timeout: float = 30.0, base: str = BASE):
        self.s = session or requests.Session()
        self.timeout = timeout
        self.base = base
        self.calls = 0

    def get(self, url: str, params: dict | None = None):
        self.calls += 1
        r = self.s.get(url, params=params, timeout=self.timeout, headers=HEADERS)
        short = url.split("/racing/")[-1]
        if r.status_code != 200:
            raise RuntimeError(f"TAB {short}: HTTP {r.status_code}, {_describe(r)}")
        try:
            return r.json()
        except ValueError:
            raise RuntimeError(f"TAB {short}: HTTP 200 but not JSON, {_describe(r)}") from None

    def meetings(self, day: str, jurisdiction: str = "VIC") -> list[dict]:
        ans = self.get(f"{self.base}/racing/dates/{day}/meetings", params={"jurisdiction": jurisdiction})
        return [m for m in (ans.get("meetings") or []) if isinstance(m, dict)]

    def race(self, race_link: str, jurisdiction: str = "VIC") -> dict:
        url = race_link if race_link.startswith("http") else f"{self.base}{race_link}"
        return self.get(url, params={"jurisdiction": jurisdiction} if "jurisdiction=" not in url else None)


def _describe(r) -> str:
    """What came back instead of the JSON: the content type and the first words of the body (an error page, never a
    price), so a refusal can be read from the log and respected."""
    ctype = str(getattr(r, "headers", {}).get("content-type", "") or "")
    text = str(getattr(r, "text", "") or "")
    body = " ".join(text.split())[:160]
    return f"content-type {ctype or 'none'}, body starts: {body!r}"


def greyhound_meetings(meetings: list[dict], location: str = "VIC") -> list[dict]:
    """TAB codes greyhound meetings raceType "G"; `location` is the state the track is in."""
    return [m for m in meetings if str(m.get("raceType") or "").upper() == "G"
            and (not location or str(m.get("location") or "").upper() == location.upper())]


def race_links(meeting: dict) -> list[tuple[int, str]]:
    out = []
    for r in meeting.get("races") or []:
        if not isinstance(r, dict):
            continue
        link = ((r.get("_links") or {}).get("self")) if isinstance(r.get("_links"), dict) else None
        if link and r.get("raceNumber") is not None:
            out.append((int(r["raceNumber"]), str(link)))
    return out


def runner_rows(day: str, meeting: dict, race_number: int, race: dict) -> list[dict]:
    """One row per runner: the open, the daily open, the current fixed price, the fluc count and times."""
    rows = []
    for u in race.get("runners") or []:
        if not isinstance(u, dict):
            continue
        fo = u.get("fixedOdds") if isinstance(u.get("fixedOdds"), dict) else {}
        flucs = [f for f in (fo.get("flucs") or []) if isinstance(f, dict)]
        rows.append({
            "date": day, "venue": meeting.get("meetingName"), "race": race_number,
            "start": race.get("raceStartTime"), "runner": u.get("runnerNumber"), "name": u.get("runnerName"),
            "status": fo.get("bettingStatus"), "open": fo.get("returnWinOpen"), "open_daily": fo.get("returnWinOpenDaily"),
            "current": fo.get("returnWin"), "flucs": len(flucs),
            "first_fluc_at": flucs[0].get("returnWinTime") if flucs else "",
            "last_fluc_at": flucs[-1].get("returnWinTime") if flucs else "",
            "scratched": u.get("scratched") if "scratched" in u else (str(fo.get("bettingStatus") or "").lower() == "scratched"),
        })
    return rows


ROW_FIELDS = ["date", "venue", "race", "start", "runner", "name", "status", "open", "open_daily", "current", "flucs",
              "first_fluc_at", "last_fluc_at", "scratched"]


def collect(client: TabClient, day: str, jurisdiction: str = "VIC", location: str = "VIC", max_races: int = 0):
    """Every VIC greyhound runner's prices for the day, plus the field names seen (for the probe)."""
    rows, seen_fixed, seen_runner, seen_race = [], set(), set(), set()
    for m in greyhound_meetings(client.meetings(day, jurisdiction), location):
        for n, link in race_links(m):
            if max_races and len(seen_race) >= max_races:
                break
            race = client.race(link, jurisdiction)
            seen_race.add((m.get("meetingName"), n))
            for u in race.get("runners") or []:
                if isinstance(u, dict):
                    seen_runner.update(u.keys())
                    if isinstance(u.get("fixedOdds"), dict):
                        seen_fixed.update(u["fixedOdds"].keys())
            rows += runner_rows(day, m, n, race)
    return rows, sorted(seen_fixed), sorted(seen_runner), len(seen_race)


def probe(client: TabClient, day: str, jurisdiction: str) -> int:
    meetings, last = None, None
    for base in BASES:
        client.base = base
        try:
            meetings = client.meetings(day, jurisdiction)
            print(f"{base}: answered")
            break
        except (RuntimeError, requests.RequestException) as e:
            print(f"{base}: {e}")
            last = e
    if meetings is None:
        raise RuntimeError(f"no host answered a plain client; last: {last}")
    dogs = greyhound_meetings(meetings, "VIC")
    print(f"{day}: {len(meetings)} meetings from TAB for jurisdiction {jurisdiction}; "
          f"{len(dogs)} Victorian greyhound meetings: {', '.join(str(m.get('meetingName')) for m in dogs)}")
    if meetings:
        print(f"  meeting fields: {', '.join(sorted(meetings[0].keys()))}")
    rows, fixed, runner, n_races = collect(client, day, jurisdiction, "VIC", max_races=3)
    print(f"  runner fields: {', '.join(runner)}")
    print(f"  fixedOdds fields: {', '.join(fixed)}")
    print(f"  {n_races} races read, {len(rows)} runners; open filled on {sum(1 for r in rows if r['open'])}, "
          f"daily open on {sum(1 for r in rows if r['open_daily'])}, current on {sum(1 for r in rows if r['current'])}, "
          f"with flucs on {sum(1 for r in rows if r['flucs'])}")
    print("| venue | race | runner | status | open | daily open | current | flucs | first fluc | last fluc |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows[:24]:
        print(f"| {r['venue']} | {r['race']} | {r['runner']} | {r['status']} | {r['open']} | {r['open_daily']} | "
              f"{r['current']} | {r['flucs']} | {r['first_fluc_at']} | {r['last_fluc_at']} |")
    return 0 if rows else 1


def record(client: TabClient, day: str, jurisdiction: str, out: Path) -> int:
    rows, fixed, _, n_races = collect(client, day, jurisdiction, "VIC")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"tab-opens-{day}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ROW_FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"{day}: {n_races} races, {len(rows)} runners, open filled on {sum(1 for r in rows if r['open'])} -> {path}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name in ("probe", "record"):
        p = sp.add_parser(name)
        p.add_argument("--date", default=datetime.now(SYDNEY).strftime("%Y-%m-%d"))
        p.add_argument("--jurisdiction", default="VIC")
        if name == "record":
            p.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    client = TabClient()
    try:
        return probe(client, a.date, a.jurisdiction) if a.cmd == "probe" else record(client, a.date, a.jurisdiction, a.out)
    except (RuntimeError, requests.RequestException, json.JSONDecodeError) as e:
        print(f"TAB refused or failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
