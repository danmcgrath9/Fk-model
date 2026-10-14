"""When does the opening price go? (13 Oct 2026, founder: "when is the best time to place a bet, when is the last
available"). For every runner in resulted VIC races with timed flucs: how long before the jump the market opened, and
the price standing at fixed times AFTER the open (20 min, 1, 2, 4, 8, 12, 24 h) and BEFORE the jump (12, 6, 3, 1, 0.5 h),
plus the last price. The jump is taken as the last fluc. Reads the database and history files only, no credits.
    python scripts/fluc_timing.py 2026-09-01"""
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
AFTER = (0.33, 1, 2, 4, 8, 12, 24); BEFORE = (12, 6, 3, 1, 0.5)
MINS = (2, 5, 10, 20)   # 14 Oct 2026: the price standing 2/5/10/20 minutes after the open (a follower's price)
print("CSV-BEGIN")
print("race_id,horse_id,n,open_h_before_jump,open," + ",".join(f"a{h}" for h in AFTER) + "," + ",".join(f"b{h}" for h in BEFORE) + ",last,finish,bsp,am930,jump_mel,scratched," + ",".join(f"m{m}" for m in MINS) + ",nflucs_10m")
n_r = 0
for r in rows:
    ents = []
    for e in r["entries"]:
        o = e.get("odds") or {}
        fl = sorted((t, float(p)) for t, p in ((ms(f.get("time")), f.get("price")) for f in (o.get("flucs") or [])) if t and p)
        if fl: ents.append((e, fl))
    if not ents: continue
    n_r += 1
    end = max(fl[-1][0] for _, fl in ents)   # the race's last fluc, for every runner
    for e, fl in ents:
        t0 = fl[0][0]
        def upto(cut):
            c = [p for t, p in fl if t <= cut]; return c[-1] if c else ""
        a = [upto(t0 + h * 3600e3) if t0 + h * 3600e3 < end else "" for h in AFTER]
        b = [upto(end - h * 3600e3) if end - h * 3600e3 >= t0 else "" for h in BEFORE]
        # 14 Oct 2026: the price standing at 9:30am Melbourne on race day (the race-morning top-up check), the jump time
        # in Melbourne, and whether the runner was scratched (so a replay can rebuild the field before the scratchings)
        day = str(r["date"])[:10]
        t930 = datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 9, 30, tzinfo=MEL).timestamp() * 1000
        am930 = upto(t930) if t0 <= t930 < end else ""
        jump = datetime.fromtimestamp(end / 1000, MEL).strftime("%H:%M")
        scr = "1" if F.entry_scratched(e) else ""
        mm = [upto(t0 + m * 60e3) if t0 + m * 60e3 < end else "" for m in MINS]
        n10 = sum(1 for t, p in fl if t <= t0 + 10 * 60e3)
        print(f"{r['race_id']},{F.horse_id(e)},{len(fl)},{(end - t0) / 3600e3:.2f},{fl[0][1]}," + ",".join(map(str, a)) + "," + ",".join(map(str, b)) + f",{fl[-1][1]},{(F.result_finish_position(F.entry_result(e) or {}) or '')},{(F.result_betfair_sp(F.entry_result(e) or {}) or '')},{am930},{jump},{scr}," + ",".join(map(str, mm)) + f",{n10}")
print("CSV-END"); print(f"{n_r} races with timed flucs since {since}", file=sys.stderr)
