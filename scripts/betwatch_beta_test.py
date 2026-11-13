"""First calls on the Betwatch beta API with the founder's key (13 Nov 2026): the limits and prices docs, the sources
list, today's Victorian thoroughbred meetings, and one race's win prices with history, to see what a price row and its
fluctuations look like. Key from BETWATCH_BETA_API_KEY, never printed.
    python scripts/betwatch_beta_test.py [VENUE-WORD] [RACE-NUMBER]   (default pakenham 4)"""
import json, os, re, sys, urllib.parse, urllib.request, urllib.error
import datetime as dt
from zoneinfo import ZoneInfo

KEY = os.environ["BETWATCH_BETA_API_KEY"].strip()
BASE = "https://api-beta.betwatch.com/v2"
UA = {"User-Agent": "fk-model/1.0"}
venue_word = (sys.argv[1] if len(sys.argv) > 1 else "pakenham").lower()
race_no = int(sys.argv[2]) if len(sys.argv) > 2 else 4


def doc(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def api(path, **q):
    url = BASE + path + ("?" + urllib.parse.urlencode({k: v for k, v in q.items() if v is not None}, doseq=True) if q else "")
    req = urllib.request.Request(url, headers={**UA, "X-API-Key": KEY, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            lim = {k: v for k, v in r.headers.items() if "ratelimit" in k.lower() or "quota" in k.lower() or "units" in k.lower()}
            return r.status, json.loads(r.read() or b"null"), lim
    except urllib.error.HTTPError as e:
        return e.code, e.read(800).decode("utf-8", "replace").replace(KEY, "<KEY>"), {}


def show(x, n=1500):
    return json.dumps(x, indent=1)[:n] if not isinstance(x, str) else x[:n]



st, src, lim = api("/sources", limit=100)
print("==== /sources", st, lim)
items = src.get("items", []) if isinstance(src, dict) else []
print("source ids:", ", ".join(f"{x['id']}({x['kind']})" for x in items))

mel = ZoneInfo("Australia/Melbourne"); today = dt.datetime.now(mel).date()
st, ev, lim = api("/events", sport="thoroughbred", country="AU", startFrom=f"{today}T00:00:00+11:00", startTo=f"{today}T23:59:00+11:00", limit=100)
print("\n==== /events today", st, lim)
evs = ev.get("items", []) if isinstance(ev, dict) else []
if not evs: print(show(ev, 1500))
print("first event:", show(evs[0], 1500) if evs else None)
pick = next((e for e in evs if venue_word in json.dumps(e).lower() and str(e.get("number", e.get("raceNumber", ""))) == str(race_no)), None)
print("\npicked:", show(pick, 800))
if pick:
    st, od, lim = api("/odds", event=pick["id"], key="win", include="history", limit=200)
    print("\n==== /odds win with history", st, lim)
    rows = od.get("items", []) if isinstance(od, dict) else []
    print(f"{len(rows)} price rows; sources: {sorted({str(r.get('source', {}).get('id') if isinstance(r.get('source'), dict) else r.get('source')) for r in rows})[:40]}")
    print(show(rows[:2], 3500))
