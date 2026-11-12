"""Every runner's price at each minute after its race's market opened, for every resulted Victorian race with timed
flucs (12 Nov 2026, founder: "test all the minutes from July then?"). DB and history files only, no credits.
    python scripts/fluc_minutes.py 2025-07-01
The race's open is its first fluc on any runner (a race needs 3+ runners with flucs, as open_times.py). For each minute
m in MINS the price is the runner's last fluc at or before open + m minutes (its own first fluc if it had none by
then is left blank: it was not yet priced); after the jump the last price stands. CSV between CSV-BEGIN and CSV-END."""
import os, sys
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
MEL = ZoneInfo("Australia/Melbourne")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import load_settings
from fk import history as H
from fk import fields as F
from fk.db import Db

MINS = list(range(0, 11)) + [12, 15, 20, 25, 30, 40, 50, 60, 75, 90, 120, 180, 240, 360, 480, 720, 1080, 1440, 2880]
since = sys.argv[1] if len(sys.argv) > 1 else "2025-07-01"
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


CLOCK = ("09:00", "12:00")   # clock prices on race day, Melbourne (founder, 12 Nov: "Are there any type of bets that we win 9am")
print("CSV-BEGIN"); print("race_id,horse_id,name,open,jump," + ",".join(f"m{m}" for m in MINS) + "," + ",".join("c" + c.replace(":", "") for c in CLOCK))
n = 0
for r in rows:
    ents = []
    for e in r["entries"]:
        fl = sorted((t, float(p)) for t, p in ((ms(f.get("time")), f.get("price")) for f in ((e.get("odds") or {}).get("flucs") or [])) if t and p)
        if fl: ents.append((e, fl))
    if len(ents) < 3: continue
    t0 = min(fl[0][0] for _, fl in ents); n += 1
    for e, fl in ents:
        cells = []
        for m in MINS:
            p = [x for t, x in fl if t <= t0 + m * 60e3]
            cells.append(f"{p[-1]:g}" if p else "")
        d = datetime.fromisoformat(str(r["date"])[:10])
        for c in CLOCK:
            hh, mi = map(int, c.split(":")); cut = datetime(d.year, d.month, d.day, hh, mi, tzinfo=MEL).timestamp() * 1000
            p = [x for t, x in fl if t <= cut]
            cells.append(f"{p[-1]:g}" if p else "")
        nm = str(e.get("name") or (e.get("horse") or {}).get("name") or "").replace(",", " ")
        print(f"{r['race_id']},{F.horse_id(e)},{nm},{fl[0][1]:g},{fl[-1][1]:g}," + ",".join(cells))
print("CSV-END"); print(f"{n} races with timed flucs since {since}", file=sys.stderr)
