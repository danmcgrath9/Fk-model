"""First call on Betwatch's current API with the trial key (13 Nov 2026; trial to 20 Nov): one past Victorian thoroughbred
day through the betwatch Python SDK (get_races, date_from/date_to, flucs), to see what a race, a runner and a
bookmaker's flucs look like, and whether TAB's flucs reach back to the timed-price gap (Nov 2025 - Aug 2026).
Key from BETWATCH_API_KEY, never printed.    python scripts/betwatch_hist_test.py [YYYY-MM-DD] (default 2026-03-14)"""
import json, os, subprocess, sys, inspect

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "betwatch", "backoff", "gql[all]", "pydantic"], check=False)
import betwatch
KEY = os.environ["BETWATCH_API_KEY"].strip()
day = sys.argv[1] if len(sys.argv) > 1 else "2026-03-14"
print("betwatch version:", getattr(betwatch, "__version__", "?"))
print("module members:", [m for m in dir(betwatch) if not m.startswith("_")][:60])
client = betwatch.connect(api_key=KEY) if hasattr(betwatch, "connect") else betwatch.BetwatchClient(api_key=KEY)
print("client methods:", [m for m in dir(client) if not m.startswith("_")])
from betwatch.types import RaceProjection, RacesFilter
print("get_races_between_dates:", inspect.signature(client.get_races_between_dates))
print("RacesFilter fields:", list(getattr(RacesFilter, "model_fields", getattr(RacesFilter, "__dataclass_fields__", {})).keys()) or inspect.signature(RacesFilter))
print("RaceProjection fields:", list(getattr(RaceProjection, "model_fields", getattr(RaceProjection, "__dataclass_fields__", {})).keys()) or inspect.signature(RaceProjection))
proj = RaceProjection(markets=True, flucs=True, betfair=True)
flt = RacesFilter(locations=["VIC"], types=["Thoroughbred"], limit=100)
races = client.get_races_between_dates(day, day, projection=proj, filter=flt)
print(f"{len(races)} VIC thoroughbred races on {day}")
enc = lambda o: getattr(o, "__dict__", None) or (o.isoformat() if hasattr(o, "isoformat") else str(o))
r = races[0]
d = json.loads(json.dumps(r, default=enc))
print("race keys:", list(d.keys()))
print(json.dumps({k: v for k, v in d.items() if k != "runners"}, default=str)[:1500])
run = (d.get("runners") or [{}])[0]
print("runner keys:", list(run.keys()))
for bm in (run.get("bookmaker_markets") or run.get("bookmakerMarkets") or [])[:40]:
    b = json.dumps(bm, default=str)
    if "tab" in b.lower()[:200]:
        print("TAB market:", b[:2500])
print("first market:", json.dumps((run.get("bookmaker_markets") or [None])[0], default=str)[:2000])
