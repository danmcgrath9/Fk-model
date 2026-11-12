"""Every runner's market price at a clock time on race day, from Form King's stored flucs (12 Nov 2026, founder: "Is
there a way we could get 9am prices for our bets since live"). DB only, no credits.
    python scripts/fluc_at.py 09:00 MEETING_ID [MEETING_ID ...]
For each runner: the first fluc (the open) with its Melbourne time, the last fluc at or before HH:MM Melbourne on the
meeting's own date (blank if the market had not opened by then), and the last stored fluc (the jump, or the last pull).
The flucs come from the newest stored odds snapshot, else the entry's own odds, as fluc_meeting.py reads them.
CSV between CSV-BEGIN and CSV-END."""
import os, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import psycopg
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fk import fields as F
MEL = ZoneInfo("Australia/Melbourne")
def ms(v):
    if v is None: return None
    if isinstance(v, (int, float)): return float(v)
    try: return datetime.fromisoformat(str(v).replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp() * 1000
    except Exception: return None
hh, mm = (int(x) for x in sys.argv[1].split(":"))
loc = lambda t: datetime.fromtimestamp(t / 1000, MEL).strftime("%Y-%m-%d %H:%M")
print("CSV-BEGIN"); print("meeting_id,race,race_id,name,open,open_mel,at_price,at_mel,last,last_mel,flucs")
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for mid in sys.argv[2:]:
        day = c.execute("select meeting_date from fk.meetings where meeting_id = %s", (mid,)).fetchone()
        if not day:
            print(f"# {mid}: not in the database", file=sys.stderr); continue
        cut = datetime(day[0].year, day[0].month, day[0].day, hh, mm, tzinfo=MEL).timestamp() * 1000
        snap = {}
        for rid_, hid_, raw_ in c.execute("""select distinct on (s.race_id, s.horse_id) s.race_id, s.horse_id, s.raw
                                              from fk.odds_snapshots s join fk.races r using (race_id)
                                              where r.meeting_id = %s and s.kind = 'current'
                                              order by s.race_id, s.horse_id, s.fetched_at desc""", (mid,)).fetchall():
            snap[(rid_, hid_)] = raw_ or {}
        for rn, rid, raw in c.execute("""select r.race_number, r.race_id, e.raw from fk.entries e join fk.races r using (race_id)
                                         where r.meeting_id = %s order by r.race_number""", (mid,)).fetchall():
            o = snap.get((rid, F.horse_id(raw))) or raw.get("odds") or {}
            fl = sorted((t, float(p)) for t, p in ((ms(f.get("time")), f.get("price")) for f in (o.get("flucs") or [])) if t and p)
            nm = str(raw.get("name") or (raw.get("horse") or {}).get("name") or "").replace(",", " ")
            if not fl:
                print(f"{mid},{rn},{rid},{nm},,,,,,,0"); continue
            at = [x for x in fl if x[0] <= cut]
            a = at[-1] if at else None
            print(f"{mid},{rn},{rid},{nm},{fl[0][1]},{loc(fl[0][0])},{a[1] if a else ''},{loc(a[0]) if a else ''},"
                  f"{fl[-1][1]},{loc(fl[-1][0])},{len(fl)}")
print("CSV-END")
