"""Price-related fields stored on a meeting's entries (raw Form King JSON), to see whether a
meeting summary carried prices our parser missed. DB only, no credits.

    python scripts/entry_odds_keys.py bendigo-20261004 [flemington-20261003]
"""
from __future__ import annotations

import json
import os
import re
import sys

import psycopg


def walk(d, pre=""):
    if isinstance(d, dict):
        for k, v in d.items():
            yield from walk(v, f"{pre}{k}.")
    elif isinstance(d, list):
        for i, v in enumerate(d[:3]):
            yield from walk(v, f"{pre}{i}.")
    else:
        yield pre[:-1], d


with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for mid in sys.argv[1:]:
        rows = c.execute("""select e.raw, e.fetched_at from fk.entries e join fk.races r using (race_id)
                            where r.meeting_id = %s order by r.race_number limit 2""", (mid,)).fetchall()
        for raw, at in rows:
            print(f"## {mid} entry fetched {at}")
            for k, v in walk(raw):
                if re.search(r"odd|price|fluc|market|sp$|bsp|scratch|tote|fixed", k, re.I) and "pastEvents" not in k:
                    print(f"- {k}: {json.dumps(v)[:80]}")
