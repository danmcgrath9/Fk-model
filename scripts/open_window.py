"""Price at the open and 2/5/10/20/60 minutes after it, for every runner of a stored meeting (any status, so it works
before the race). The open is the race's first fluc across all runners. DB only, no credits (14 Oct 2026: what a
member who gets the tip a few minutes after our bets would get).
    python scripts/open_window.py caulfield-20261017"""
import os, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import psycopg
MEL = ZoneInfo("Australia/Melbourne"); MINS = (2, 5, 10, 20, 60)
def ms(v):
    if isinstance(v, (int, float)): return float(v)
    try: return datetime.fromisoformat(str(v).replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp() * 1000
    except Exception: return None
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for mid in sys.argv[1:]:
        races = {}
        for rn, raw in c.execute("""select r.race_number, e.raw from fk.entries e join fk.races r using (race_id)
                                    where r.meeting_id = %s order by r.race_number""", (mid,)).fetchall():
            fl = sorted((t, float(p)) for t, p in ((ms(f.get("time")), f.get("price")) for f in ((raw.get("odds") or {}).get("flucs") or [])) if t and p)
            name = raw.get("name") or (raw.get("horse") or {}).get("name")
            races.setdefault(rn, []).append((name, fl))
        print(f"## {mid}\nrace|horse|open_time|open|" + "|".join(f"m{m}" for m in MINS) + "|latest")
        for rn, ents in sorted(races.items()):
            t0 = min((fl[0][0] for _, fl in ents if fl), default=None)
            if t0 is None: continue
            for name, fl in ents:
                if not fl: continue
                upto = lambda cut: next((p for t, p in reversed(fl) if t <= cut), "")
                print(f"{rn}|{name}|{datetime.fromtimestamp(t0/1000, MEL).strftime('%a %H:%M')}|{fl[0][1]}|"
                      + "|".join(str(upto(t0 + m * 60e3)) for m in MINS) + f"|{fl[-1][1]}")
