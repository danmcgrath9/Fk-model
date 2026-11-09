"""Career prizemoney and age for a list of horses, from the newest stored field entry (fk.entries.raw totalPrizeMoney,
as at that race) plus any run since. DB only, no credits. For a ballot tie-break (Racing Victoria: equal ballot rating
-> oldest out first, then lowest aggregate prizemoney out first; 9 Nov 2026).
    python scripts/horse_prizemoney.py --file data/nominations/X.txt"""
import argparse, json, os
from pathlib import Path
import psycopg

ap = argparse.ArgumentParser(); ap.add_argument("names", nargs="*"); ap.add_argument("--file")
a = ap.parse_args()
names = list(a.names) + ([l.strip() for l in Path(a.file).read_text().splitlines() if l.strip()] if a.file else [])
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for n in names:
        row = c.execute("""select r.race_id, r.raw->>'date', e.raw from fk.entries e join fk.races r using (race_id)
                           join fk.horses h using (horse_id) where lower(h.name) = lower(%s)
                           order by r.race_id desc limit 1""", (n,)).fetchone()
        if not row:
            print(f"{n}: no stored entry"); continue
        rid, d, raw = row
        prize_keys = {k: v for k, v in raw.items() if "prize" in k.lower() or k.lower() in ("age", "wins", "starts", "places")}
        h = raw.get("horse") or {}
        print(f"{n}: entry {rid} {d}  " + json.dumps(prize_keys, default=str) + "  age " + str(h.get("age")))
        pe = c.execute("""select p.event_date::date, p.raw from fk.past_events p join fk.horses h using (horse_id)
                          where lower(h.name) = lower(%s) order by p.event_date desc limit 3""", (n,)).fetchall()
        for dd, pr in pe:
            pk = {k: v for k, v in pr.items() if "prize" in k.lower() or k in ("position", "finish", "finishPosition")}
            print(f"    run {dd} " + json.dumps(pk, default=str)[:300])
