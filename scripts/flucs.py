"""Price history for a stored meeting (18 Oct 2026, founder: how many bookmakers open after TAB and how far off TAB's
opening price they are). Per runner: every stored fixed-odds fluctuation (time, price), Form King's average opening
price (avgOpen, the corporate bookmakers' open, "typically 15-20 minutes after the TAB market"), the best price and
who held it at the last snapshot, plus any extra odds snapshots stored for the meeting. DB only, no credits.

    python scripts/flucs.py caulfield-20261014"""
import json, os, sys
from datetime import datetime, timezone, timedelta
import psycopg
MEL = timezone(timedelta(hours=11))
ts = lambda ms: datetime.fromtimestamp(ms / 1000, MEL).strftime("%a %H:%M:%S") if isinstance(ms, (int, float)) else str(ms)
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    tabs = [r[0] for r in c.execute("select table_schema||'.'||table_name from information_schema.tables where table_schema='fk' and table_name ilike '%odds%'")]
    print("odds tables:", tabs)
    for mid in sys.argv[1:]:
        rows = c.execute("""select r.race_number, e.raw from fk.entries e join fk.races r using (race_id)
                            where r.meeting_id = %s order by r.race_number""", (mid,)).fetchall()
        print(f"## {mid}: {len(rows)} entries")
        shown = False
        for rn, raw in rows:
            if not isinstance(raw, dict): continue
            name = raw.get("name") or (raw.get("horse") or {}).get("name") or raw.get("horseName")
            o = raw.get("odds") or {}
            if not shown and o:
                print("odds keys:", sorted(o.keys())); shown = True
            fl = o.get("flucs") or raw.get("flucs") or []
            seq = " ".join(f"{ts(f.get('time'))}=${f.get('price')}" for f in fl)
            print(f"R{rn} {name!s:22s} avgOpen {o.get('avgOpen')} bestNow {o.get('bestNow')} avgNow {o.get('avgNow')} "
                  f"best@ {o.get('bestBookies')} last {ts(o.get('timestamp'))} | flucs: {seq}")
        for t in tabs:
            try:
                n = c.execute(f"select count(*) from {t} where meeting_id = %s", (mid,)).fetchone()[0]
                print(f"{t}: {n} rows for {mid}")
            except Exception as e:
                c.rollback(); print(f"{t}: {str(e)[:80]}")
