"""Scheduled jump times for stored meetings, Melbourne time. DB only, no credits.
python scripts/race_times.py ballarat-20261009 cranbourne-20261009"""
import os, sys
from zoneinfo import ZoneInfo
import psycopg
mel = ZoneInfo("Australia/Melbourne")
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for mid in sys.argv[1:]:
        print(f"## {mid}")
        for n, at, raw in c.execute("select race_number, scheduled_at, raw->>'startTime' from fk.races where meeting_id=%s order by race_number", (mid,)).fetchall():
            print(f"R{n} {at.astimezone(mel).strftime('%H:%M') if at else '?'} raw={raw}")
