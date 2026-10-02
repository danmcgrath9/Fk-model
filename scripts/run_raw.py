"""Print the raw stored Form King past event for one horse on one date, every field, plus the
same race's other runners we hold (their sectional time and finish). Reads the database only;
no Form King calls, no credits.

    python scripts/run_raw.py "Cavill Avenue" 2026-09-30
"""
from __future__ import annotations

import json
import os
import sys

import psycopg


def flat(d, pre=""):
    for k, v in (d or {}).items():
        if isinstance(v, dict):
            yield from flat(v, f"{pre}{k}.")
        elif isinstance(v, list):
            yield f"{pre}{k}", json.dumps(v)[:400]
        else:
            yield f"{pre}{k}", v


def main() -> None:
    name, date = sys.argv[1], sys.argv[2]
    with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
        h = c.execute("select horse_id from fk.horses where lower(name)=lower(%s) limit 1", (name,)).fetchone()
        if not h:
            sys.exit(f"no horse {name!r}")
        rows = c.execute("select past_event_id, raw from fk.past_events where horse_id=%s and event_date::date=%s::date",
                         (h[0], date)).fetchall()
        if not rows:
            sys.exit("no stored run on that date")
        pid, raw = rows[0]
        print(f"## {name} {date} ({pid})\n")
        for k, v in flat(raw):
            if k.startswith("benchmark.sections") or v in (None, "", "[]", "{}"):
                continue
            print(f"- {k}: {v}")
        rid = pid.split(":", 1)[1]
        print(f"\n## Other runners we hold from race {rid}\n")
        others = c.execute("""select h.name, p.finish_position, p.margin, p.raw->>'sectionalTimeInMillis', p.raw->>'sectionalDistance',
                                     p.raw->'benchmark'->>'finishingSpeed', p.raw->'benchmark'->>'dataStage'
                              from fk.past_events p join fk.horses h using (horse_id)
                              where p.past_event_id like %s order by p.finish_position""", (f"%:{rid}",)).fetchall()
        for o in others:
            print(f"- {o[0]}: finish {o[1]} margin {o[2]} sectional {o[3]}ms over {o[4]}m finishing speed {o[5]} stage {o[6]}")


if __name__ == "__main__":
    main()
