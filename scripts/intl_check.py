"""Imported / overseas-form runners on stored meetings: Form King's firstStarter flag, career starts (careerForm),
the past runs we hold, their tracks, and any country/state key on those runs. DB only, no credits.

    python scripts/intl_check.py caulfield-20261017 [more meeting ids]
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys

import psycopg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fk import fields as F  # noqa: E402


def starts(e):
    cf = e.get("careerForm") or ""
    m = re.match(r"\s*(\d+)\s*:", str(cf))
    return int(m.group(1)) if m else None


with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for mid in sys.argv[1:]:
        rows = c.execute("""select r.race_number, e.raw from fk.entries e join fk.races r using (race_id)
                            where r.meeting_id = %s order by r.race_number""", (mid,)).fetchall()
        print(f"## {mid}: {len(rows)} entries")
        print("| R | Horse | FK firstStarter | career starts | runs held (non-trial) | tracks of runs held | country/state keys |")
        print("|---|---|---|---|---|---|---|")
        sample = None
        for rn, e in rows:
            if F.entry_scratched(e):
                continue
            name = e.get("name") or e.get("horseName") or (e.get("horse") or {}).get("name") or "?"
            pe = F.entry_past_events(e)
            real = [p for p in pe if not (p.get("isTrial") or p.get("trial") or p.get("raceType") == "TRIAL")]
            tracks = collections.Counter(str(F.past_event_track(p)) for p in real)
            ckeys = sorted({k for p in pe for k in p if re.search(r"country|state|nation|overseas|international", k, re.I)})
            vals = sorted({str(p.get(k)) for p in pe for k in ckeys})[:6]
            st = starts(e)
            flag = (st or 0) > len(real)
            if flag and sample is None and pe:
                sample = (name, pe[0])
            if flag or e.get("firstStarter"):
                print(f"| {rn} | {name} | {e.get('firstStarter')} | {st} | {len(real)} | {dict(tracks.most_common(4))} | {ckeys} {vals} |")
        if sample:
            print(f"\nsample past-run keys for {sample[0]}: {sorted(sample[1].keys())}")
            print(json.dumps({k: sample[1].get(k) for k in sorted(sample[1]) if not isinstance(sample[1][k], (dict, list))})[:1500])
