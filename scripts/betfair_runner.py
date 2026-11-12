"""Betfair game-day runner: the paper lay book and favourite-back book, fired at Betfair SP (8 Nov 2026; founder: "We are
going live Friday with this all", "$50 a lay works").

Before each jump (default 90 s) it reads Betfair's projected SP for the race and applies the rules exactly as the meeting
pages state them (data/live_bets/TIPPING_RULES.md):
  LAY  a runner on the day's lay sheet (DAYPREFIX-GTAG-lays.csv, rows not excluded) when its projected SP is inside its
       window: $8-$12 at 1.6x our price, or $15-$40 at 1.5x. Order: LIMIT_ON_CLOSE LAY, limit = the window's top, liability
       = unit x (projected SP - 1), so the backer's stake lands at about one unit whatever the final SP.
  BACK a runner on the day's back sheet (DAYPREFIX-GTAG-backs.csv) only if it is the projected favourite and its projected
       SP is $4 to its cap. Order: LIMIT_ON_CLOSE BACK, size = the back unit, limit $4 (never matched under $4).
Caps: liability per race and per day; an order that would breach either is logged and skipped, never resized.

Every decision goes to a CSV log (one row per candidate looked at, with the projected SP and why it was or was not bet).
  --mode paper  (default) decides and logs, places nothing
  --mode live   places the orders; only ever run from the "betfair" GitHub environment, whose approval is the founder's send

Betfair blocks API logins from the United States, where GitHub's own runners are, so the workflow runs on a self-hosted
runner in Australia. The login and API addresses are settings (BETFAIR_LOGIN_URL, BETFAIR_API_URL) because they have not
been exercised yet: the first paper run with the real key is the check that they are right.
Secrets (environment only, never in the repo): BETFAIR_APP_KEY, BETFAIR_USERNAME, BETFAIR_PASSWORD.
LIVE LAYS ARE OFF (founder, 13 Nov 2026: "Stop the live lays, track the ours/1.6 rule"): LIVE_LAYS below is False, so a
live run never places a lay; the lay rules stay on paper in research/form_gbm/track_rules.py.

    python scripts/betfair_runner.py --date 2026-11-13 --manifest data/live_bets/2026-11-13-betfair-manifest.txt
    python scripts/betfair_runner.py --date 2026-11-13 --manifest M --mock tests/betfair_mock.json   (offline test)
The manifest lists the day's meetings, one per line: DAYPREFIX GTAG (the tag whose lay and back sheets are the day's).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

L = Path(__file__).resolve().parents[1] / "data" / "live_bets"
LIVE_LAYS = False   # founder, 13 Nov 2026: "Stop the live lays". Only the founder's word turns this back on.
norm =lambda s: re.sub(r"[^a-z0-9]", "", re.sub(r"^\s*\d+\.\s*", "", str(s)).lower())
venue_key = lambda s: re.sub(r"[^a-z]", "", re.sub(r"(hillside|lakeside|synthetic|poly|heath)", "", str(s).lower()))


class Betfair:
    """The four API-NG calls the runner needs, over JSON-RPC."""

    def __init__(self, app_key: str, user: str, password: str, login_url: str, api_url: str):
        import requests
        self.s, self.api_url, self.app_key = requests.Session(), api_url, app_key
        r = self.s.post(login_url, data={"username": user, "password": password},
                        headers={"X-Application": app_key, "Accept": "application/json",
                                 "Content-Type": "application/x-www-form-urlencoded"}, timeout=30)
        j = r.json()
        if j.get("status") != "SUCCESS":
            raise SystemExit(f"Betfair login failed: {j.get('status')} {j.get('error')}")
        self.token = j["token"]

    def call(self, method: str, params: dict):
        body = {"jsonrpc": "2.0", "method": f"SportsAPING/v1.0/{method}", "params": params, "id": 1}
        r = self.s.post(self.api_url, data=json.dumps(body), timeout=30,
                        headers={"X-Application": self.app_key, "X-Authentication": self.token, "Content-Type": "application/json"})
        j = r.json()
        if "error" in j:
            raise RuntimeError(f"{method}: {j['error']}")
        return j["result"]

    def markets(self, day: str):
        start = datetime.fromisoformat(day).replace(tzinfo=timezone(timedelta(hours=11)))   # Melbourne summer time
        return self.call("listMarketCatalogue", {
            "filter": {"eventTypeIds": ["7"], "marketCountries": ["AU"], "marketTypeCodes": ["WIN"],
                       "marketStartTime": {"from": start.isoformat(), "to": (start + timedelta(days=1)).isoformat()}},
            "marketProjection": ["EVENT", "MARKET_START_TIME", "RUNNER_DESCRIPTION"], "maxResults": 1000})

    def book(self, market_id: str):
        return self.call("listMarketBook", {"marketIds": [market_id], "priceProjection": {"priceData": ["SP_PROJECTED"]}})[0]

    def place(self, market_id: str, instructions: list, ref: str):
        return self.call("placeOrders", {"marketId": market_id, "instructions": instructions, "customerRef": ref[:32]})


class Mock:
    """Offline stand-in: {"markets": [listMarketCatalogue rows], "books": {marketId: listMarketBook row}}."""

    def __init__(self, path: str):
        self.d = json.load(open(path))

    def markets(self, day):
        return self.d["markets"]

    def book(self, market_id):
        return self.d["books"][market_id]

    def place(self, market_id, instructions, ref):
        return {"status": "SUCCESS", "instructionReports": [{"status": "SUCCESS", "betId": f"MOCK-{market_id}-{i}"} for i, _ in enumerate(instructions)]}


def load_sheets(manifest: str):
    """{(venue key, race): {"lays": [...], "backs": [...]}} from each meeting's lay and back sheets."""
    out = {}
    for line in open(manifest):
        parts = line.split("#")[0].split()
        if len(parts) < 2:
            continue
        prefix, tag = parts[:2]
        vk = venue_key(prefix[11:])
        for r in csv.DictReader(open(L / f"{prefix}-{tag}-lays.csv")):
            if "excluded" in (r.get("note") or ""):
                continue
            out.setdefault((vk, int(r["race"])), {"lays": [], "backs": []})["lays"].append(
                dict(horse=r["horse"], ours=float(r["ours"]), lo=float(r["lay_if_bsp_at_least"]), hi=float(r["lay_if_bsp_at_most"]),
                     band=(r.get("band") or "15-40").strip()))
        for r in csv.DictReader(open(L / f"{prefix}-{tag}-backs.csv")):
            out.setdefault((vk, int(r["race"])), {"lays": [], "backs": []})["backs"].append(
                dict(horse=r["horse"], ours=float(r["ours"]), lo=float(r["back_if_favourite_bsp_at_least"]),
                     hi=float(r["back_if_favourite_bsp_at_most"])))
    return out


def decide(sheet: dict, names: dict, book: dict, lay_unit: float, back_unit: float):
    """The orders the rules ask for in one race, and a log line for every candidate. names: selectionId -> runner name."""
    proj = {}
    for rn in book.get("runners", []):
        if rn.get("status") != "ACTIVE":
            continue
        p = ((rn.get("sp") or {}).get("nearPrice"))
        if isinstance(p, (int, float)) and p > 1:
            proj[rn["selectionId"]] = float(p)
    by_name = {norm(names[s]): s for s in proj if s in names}
    fav = min(proj, key=proj.get) if proj else None
    orders, log = [], []
    for c in sheet.get("lays", []):
        sid = by_name.get(norm(c["horse"])); p = proj.get(sid)
        if sid is None or p is None:
            log.append((c["horse"], "LAY", None, c["lo"], c["hi"], 0.0, "not on Betfair or no projected SP")); continue
        if not (c["lo"] <= p <= c["hi"]):
            log.append((c["horse"], "LAY", p, c["lo"], c["hi"], 0.0, "projected SP outside its window")); continue
        liab = round(lay_unit * (p - 1), 2)
        orders.append(dict(selectionId=sid, side="LAY", orderType="LIMIT_ON_CLOSE", handicap=0,
                           limitOnCloseOrder={"liability": liab, "price": c["hi"]}, _horse=(c["horse"], "LAY", c["lo"]), _p=p, _liab=liab, _lo=c["lo"]))
        log.append((c["horse"], "LAY", p, c["lo"], c["hi"], liab, f"lay ${c['band']}"))
    for c in sheet.get("backs", []):
        sid = by_name.get(norm(c["horse"])); p = proj.get(sid)
        if sid is None or p is None:
            continue   # every runner can be a back candidate; only the favourite matters, so silence for the rest
        if sid != fav or not (c["lo"] <= p <= c["hi"]):
            if sid == fav:
                log.append((c["horse"], "BACK", p, c["lo"], c["hi"], 0.0, "favourite outside $4-cap"))
            continue
        orders.append(dict(selectionId=sid, side="BACK", orderType="LIMIT_ON_CLOSE", handicap=0,
                           limitOnCloseOrder={"liability": back_unit, "price": c["lo"]}, _horse=(c["horse"], "BACK", c["lo"]), _p=p, _liab=back_unit, _lo=c["lo"]))
        log.append((c["horse"], "BACK", p, c["lo"], c["hi"], back_unit, "back the favourite"))
    return orders, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--mode", choices=["paper", "live"], default="paper")
    ap.add_argument("--lay-unit", type=float, default=50.0)    # founder, 8 Nov 2026: "$50 a lay works"
    ap.add_argument("--back-unit", type=float, default=50.0)
    ap.add_argument("--race-cap", type=float, default=3000.0, help="most liability in one race (backtest at $50: 90% of races with a lay need under $3,100)")
    ap.add_argument("--day-cap", type=float, default=40000.0, help="most liability placed in the day, all races added up (backtest at $50: busiest day $32,000)")
    ap.add_argument("--lead", type=int, default=90, help="seconds before the scheduled jump to act")
    ap.add_argument("--mock")
    ap.add_argument("--no-wait", action="store_true", help="act on every race straight away (tests)")
    a = ap.parse_args()
    if a.mode == "live" and a.mock:
        raise SystemExit("live with a mock makes no sense")
    bf = Mock(a.mock) if a.mock else Betfair(os.environ["BETFAIR_APP_KEY"], os.environ["BETFAIR_USERNAME"], os.environ["BETFAIR_PASSWORD"],
                                             os.environ.get("BETFAIR_LOGIN_URL", "https://identitysso.betfair.com.au/api/login"),
                                             os.environ.get("BETFAIR_API_URL", "https://api.betfair.com/exchange/betting/json-rpc/v1"))
    sheets = load_sheets(a.manifest)
    venues = {vk for vk, _ in sheets}
    todo = []
    for m in bf.markets(a.date):
        vk = venue_key((m.get("event") or {}).get("venue") or (m.get("event") or {}).get("name", ""))
        rm = re.match(r"R(\d+)\b", m.get("marketName", ""))
        if vk in venues and rm and (vk, int(rm.group(1))) in sheets:
            todo.append((m["marketStartTime"], m["marketId"], vk, int(rm.group(1)), {r["selectionId"]: r["runnerName"] for r in m.get("runners", [])}))
    todo.sort()
    print(f"{a.date} {a.mode}: {len(todo)} races with a lay or back candidate across {len(venues)} meetings")
    logf = L / f"{a.date}-betfair-{a.mode}-log.csv"
    new = not logf.exists()
    out = csv.writer(open(logf, "a", newline=""))
    if new:
        out.writerow(["time_utc", "venue", "race", "market", "horse", "side", "projected_sp", "window_lo", "window_hi", "liability", "decision", "bet_id"])
    day_liab = 0.0
    for start, mid, vk, race, names in todo:
        t0 = datetime.fromisoformat(start.replace("Z", "+00:00")) - timedelta(seconds=a.lead)
        if not a.no_wait:
            while (wait := (t0 - datetime.now(timezone.utc)).total_seconds()) > 0:
                time.sleep(min(wait, 60))
        book = bf.book(mid)
        if book.get("status") != "OPEN" or book.get("inplay"):
            print(f"R{race} {vk}: market {book.get('status')}, skipped"); continue
        orders, log = decide(sheets[(vk, race)], names, book, a.lay_unit, a.back_unit)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        placed, race_liab = {}, 0.0
        keep = []
        for o in orders:
            # LIVE LAYS STOPPED (founder, 13 Nov 2026: "Stop the live lays"): on the months that never chose them every lay rule
            # lost (night/bsp_rules_oos.py), so a live run places backs only and logs each lay it would have made.
            if o["side"] == "LAY" and not LIVE_LAYS:
                placed[o["_horse"]] = "not placed: live lays stopped (13 Nov)"; continue
            if race_liab + o["_liab"] > a.race_cap or day_liab + o["_liab"] > a.day_cap:
                placed[o["_horse"]] = "skipped: over the race or day cap"; continue
            race_liab += o["_liab"]; day_liab += o["_liab"]; keep.append(o)
        if keep and a.mode == "live":
            res = bf.place(mid, [{k: v for k, v in o.items() if not k.startswith("_")} for o in keep], f"fk{a.date}{race}")
            for o, rep in zip(keep, res.get("instructionReports", [])):
                placed[o["_horse"]] = f"{rep.get('status')} {rep.get('betId', '')} {rep.get('errorCode', '')}".strip()
        for o in keep:
            placed.setdefault(o["_horse"], "paper: would place")
        for h, side, p, lo, hi, liab, why in log:
            st = placed.get((h, side, lo), "")
            out.writerow([now, vk, race, mid, h, side, p, lo, hi, liab, why, st])
            if liab:
                print(f"R{race} {vk:<12} {side:<4} {h:<22} projected ${p:.2f} (window ${lo:g}-${hi:g}) liability ${liab:,.2f}  {st}")
    print(f"day done: liability placed ${day_liab:,.2f} (cap ${a.day_cap:,.0f}); log {logf}")


if __name__ == "__main__":
    main()
