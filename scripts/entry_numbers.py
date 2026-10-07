"""Saddlecloth number, emergency flag and scratching for every entry of a meeting (which emergencies
gain a start). DB only, no credits.  python scripts/entry_numbers.py kyneton-20261008"""
import os, sys
import psycopg
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for rn, raw in c.execute("""select r.race_number, e.raw from fk.entries e join fk.races r using (race_id)
                                where r.meeting_id = %s order by r.race_number""", (sys.argv[1],)).fetchall():
        name = raw.get("name") or (raw.get("horse") or {}).get("name") or raw.get("horseName")
        print(f"{rn}|{raw.get('number')}|{name}|{bool(raw.get('emergency'))}|{bool(raw.get('scratched'))}")
