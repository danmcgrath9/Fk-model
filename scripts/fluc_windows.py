"""Price at the open and 15/30/45/60 min after it, with BSP and the finish, for every runner in resulted VIC races in a
date range (26 Oct 2026, founder: "How often do we beat bsp this week with betting 15 / 30 / 45 / 60 minutes after?").
Form King corporate-average flucs. Reads the database and history files, no credits. CSV between CSV-BEGIN and CSV-END.
    python scripts/fluc_windows.py 2026-10-20 2026-10-26"""
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import load_settings
from fk import fields as F
from fk import history as H
from fk.db import Db
from datetime import datetime, timezone
since = sys.argv[1] if len(sys.argv) > 1 else "2026-10-20"
until = sys.argv[2] if len(sys.argv) > 2 else "2099-01-01"
ROOT = Path(__file__).resolve().parent.parent
db = Db(load_settings().database_url)
rows = [r for r in db.resulted_races("VIC") if since <= str(r["date"])[:10] <= until]
held = {r["race_id"] for r in rows}
rows += [r for r in H.resulted_races(ROOT / "history", "VIC", skip=held) if since <= str(r["date"])[:10] <= until]
def ms(v):
    if v is None: return None
    if isinstance(v, (int, float)): return float(v)
    try: return datetime.fromisoformat(str(v).replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp() * 1000 if "T" in str(v) else float(v)
    except Exception: return None
MINS = (15, 30, 45, 60)
print("CSV-BEGIN"); print("race_id,horse_id,horse,finish,bsp,open," + ",".join(f"m{m}" for m in MINS) + ",last")
for r in rows:
    for e in r["entries"]:
        o = e.get("odds") or {}; hr = e.get("horseResult") or {}
        fl = sorted((t, float(p)) for t, p in ((ms(f.get("time")), f.get("price")) for f in (o.get("flucs") or [])) if t and p)
        if not fl: continue
        t0, end = fl[0][0], fl[-1][0]
        def upto(cut):
            c = [p for t, p in fl if t <= cut]; return c[-1] if c else ""
        a = [upto(t0 + m * 60e3) if t0 + m * 60e3 < end else "" for m in MINS]
        nm = str(e.get("horseName") or e.get("name") or "").replace(",", " ")
        print(f"{r['race_id']},{F.horse_id(e)},{nm},{hr.get('finishPosition') or ''},{hr.get('betfairStartingPrice') or ''},"
              f"{fl[0][1]},{','.join(str(x) for x in a)},{fl[-1][1]}")
print("CSV-END")
