"""The price path of every runner in resulted VIC races from a date, from Form King's flucs (each a price and a time):
the first price (the open), the price standing 24h, 12h, 3h and 1h before the last fluc (the jump, in effect), and the
last price. Reads the database and the history files only, no credits. Prints CSV between CSV-BEGIN and CSV-END.
    python scripts/fluc_path.py 2026-05-06"""
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import load_settings
from fk import fields as F
from fk import history as H
from fk.db import Db
from datetime import datetime, timezone
since = sys.argv[1] if len(sys.argv) > 1 else "2026-05-06"
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
print("CSV-BEGIN"); print("race_id,horse_id,n,open,p24,p12,p3,p1,last")
n_r = 0
for r in rows:
    n_r += 1
    for e in r["entries"]:
        o = e.get("odds") or {}; fl = [(ms(f.get("time")), f.get("price")) for f in (o.get("flucs") or [])]
        fl = sorted((t, float(p)) for t, p in fl if t and p)
        if not fl: continue
        end = fl[-1][0]
        def at(h):
            cut = end - h * 3600e3; c = [p for t, p in fl if t <= cut]
            return c[-1] if c else ""
        print(f"{r['race_id']},{F.horse_id(e)},{len(fl)},{fl[0][1]},{at(24)},{at(12)},{at(3)},{at(1)},{fl[-1][1]}")
print("CSV-END"); print(f"{n_r} races", file=sys.stderr)
