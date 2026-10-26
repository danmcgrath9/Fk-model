"""Prices AFTER the market opens, for every runner in resulted VIC races from a date (26 Oct 2026, founder: "how
profitable are we after the market opens if all accounts are available"). From Form King's corporate-average flucs:
the open, the price standing 15 min, 1, 3, 6 and 12 h after the open, at 9:30am Melbourne on race day, 1 h before the
jump (the last fluc) and the last price; plus the final best/average ratio (bestNow / avgNow), the only per-account
figure the data holds. Reads the database and history files, no credits. CSV between CSV-BEGIN and CSV-END.
    python scripts/fluc_after_open.py 2026-06-03"""
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import load_settings
from fk import fields as F
from fk import history as H
from fk.db import Db
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
MEL = ZoneInfo("Australia/Melbourne")
since = sys.argv[1] if len(sys.argv) > 1 else "2026-06-03"
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
print("CSV-BEGIN"); print("race_id,horse_id,open_ms,end_ms,open,a15m,a1h,a3h,a6h,a12h,am930,b1h,last,best_over_avg")
for r in rows:
    for e in r["entries"]:
        o = e.get("odds") or {}
        fl = sorted((t, float(p)) for t, p in ((ms(f.get("time")), f.get("price")) for f in (o.get("flucs") or [])) if t and p)
        if not fl: continue
        t0, end = fl[0][0], fl[-1][0]
        def upto(cut):
            c = [p for t, p in fl if t <= cut]; return c[-1] if c else ""
        d = datetime.fromtimestamp(end / 1000, MEL)
        am = datetime(d.year, d.month, d.day, 9, 30, tzinfo=MEL).timestamp() * 1000
        bo = (float(o["bestNow"]) / float(o["avgNow"])) if o.get("bestNow") and o.get("avgNow") else ""
        a = [upto(t0 + h * 3600e3) if t0 + h * 3600e3 < end else "" for h in (0.25, 1, 3, 6, 12)]
        print(f"{r['race_id']},{F.horse_id(e)},{int(t0)},{int(end)},{fl[0][1]},{','.join(str(x) for x in a)},"
              f"{upto(am) if t0 <= am < end else ''},{upto(end - 3600e3)},{fl[-1][1]},{bo}")
print("CSV-END")
