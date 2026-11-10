"""When did each race's market open? (11 Nov 2026, night research: the opens we miss cost more than anything in the
model, and the 12:17pm pricing run was set by when riders are declared, not by when TAB opens.)
For every resulted VIC race with timed flucs since a date: the Melbourne clock time of the first price on any runner,
how many runners were priced within 10 minutes of it (a real opening market, not one early quote), the median runner's
first price time, the jump (last fluc) and the hours between. DB and history files only, no credits.
CSV between CSV-BEGIN and CSV-END.
    python scripts/open_times.py 2026-09-01"""
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import load_settings
from fk import history as H
from fk.db import Db
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
MEL = ZoneInfo("Australia/Melbourne")
since = sys.argv[1] if len(sys.argv) > 1 else "2026-09-01"
ROOT = Path(__file__).resolve().parent.parent
db = Db(load_settings().database_url)
rows = [r for r in db.resulted_races("VIC") if str(r["date"])[:10] >= since]
held = {r["race_id"] for r in rows}
rows += [r for r in H.resulted_races(ROOT / "history", "VIC", skip=held) if str(r["date"])[:10] >= since]
def ms(v):
    if v is None: return None
    if isinstance(v, (int, float)): return float(v)
    try: return datetime.fromisoformat(str(v).replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp() * 1000 if "T" in str(v) else float(v)
    except Exception: return None
loc = lambda t: datetime.fromtimestamp(t / 1000, MEL).strftime("%Y-%m-%d %H:%M")
print("CSV-BEGIN"); print("race_id,date,track,runners_priced,open_mel,within10,median_first_mel,jump_mel,hours_open_to_jump")
n = 0
for r in rows:
    firsts, last = [], 0
    for e in r["entries"]:
        fl = sorted(t for t in (ms(f.get("time")) for f in ((e.get("odds") or {}).get("flucs") or []) if f.get("price")) if t)
        if fl: firsts.append(fl[0]); last = max(last, fl[-1])
    if len(firsts) < 3: continue
    firsts.sort(); t0 = firsts[0]; n += 1
    print(f"{r['race_id']},{str(r['date'])[:10]},{str(r.get('track') or '').replace(',', ' ')},{len(firsts)},{loc(t0)},{sum(1 for t in firsts if t <= t0 + 600e3)},"
          f"{loc(firsts[len(firsts) // 2])},{loc(last)},{(last - t0) / 3600e3:.1f}")
print("CSV-END"); print(f"{n} races with timed flucs since {since}", file=sys.stderr)
