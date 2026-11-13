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
gr = getattr(client, "get_races")
print("get_races signature:", inspect.signature(gr))
try:
    from betwatch.types import RaceProjection, RacesFilter, MeetingType
    proj = RaceProjection(markets=True, flucs=True)
    flt = RacesFilter(meeting_types=[MeetingType.THOROUGHBRED], locations=["VIC"])
    races = client.get_races(day, day, proj, flt)
except Exception as ex:
    print("typed call failed:", type(ex).__name__, str(ex).replace(KEY, "<KEY>")[:400])
    races = client.get_races(day, day)
print(f"{len(races)} races on {day}")
r = races[0]
d = r.model_dump() if hasattr(r, "model_dump") else (r.dict() if hasattr(r, "dict") else r.__dict__)
txt = json.dumps(d, default=str)
print("race keys:", list(d.keys()))
print(txt[:4000].replace(KEY, "<KEY>"))
