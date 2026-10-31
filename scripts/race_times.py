"""Jump times for the races of given meetings (31 Oct 2026, founder: "a list of bets in order of time"). Reads only.
    python scripts/race_times.py YYYY-MM-DD TRACK [TRACK ...]"""
import os, sys, psycopg
day, tracks = sys.argv[1], sys.argv[2:]
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for t in tracks:
        rows = c.execute("""select r.race_number, r.raw from fk.races r join fk.meetings m on m.meeting_id = r.meeting_id
                            where m.meeting_date = %s and m.track ilike %s order by r.race_number""", (day, t + "%")).fetchall()
        print(f"## {t} {day}: {len(rows)} races")
        for n, raw in rows:
            raw = raw or {}
            keys = {k: v for k, v in raw.items() if any(s in k.lower() for s in ("time", "start", "jump", "scheduled"))}
            print(n, keys)
