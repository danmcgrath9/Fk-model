"""Each horse's stored runs with Form King's ratings, read from fk.past_events (every field we pull and every fk-horse
lookup writes there; fk.horses.raw is only the last Get Horse Form snapshot). DB only, no credits.

    python scripts/horse_ratings.py --file data/nominations/X.txt [--runs 8]
    python scripts/horse_ratings.py "Cavill Avenue" Caddington

Rating = Form King's weight-for-age rating for the run (wfaRat, else weightForAgeRating); at weights beside it."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fk import fields as F  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("names", nargs="*")
ap.add_argument("--file")
ap.add_argument("--runs", type=int, default=8)
a = ap.parse_args()
names = list(a.names) + ([ln.strip() for ln in Path(a.file).read_text().splitlines() if ln.strip()] if a.file else [])
out = []
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for n in names:
        hs = c.execute("select horse_id, name from fk.horses where lower(name) = lower(%s)", (n,)).fetchall()
        runs = []
        for hid, _ in hs:
            for d, raw in c.execute("select event_date::date, raw from fk.past_events where horse_id = %s order by event_date desc", (hid,)):
                if raw.get("trial"):
                    continue
                r = F.run_ratings(raw)
                runs.append({"date": str(d), "track": r["track"], "dist": r["distance"], "fin": r["finish"], "of": r["runners"],
                             "margin": F.past_event_margin(raw), "sp": raw.get("startingPrice"),
                             "wfa": r["wfaRat"] or r["wfa"], "atWeights": r["atWeights"], "raceRating": r["raceRating"]})
        runs = sorted(runs, key=lambda x: x["date"], reverse=True)[: a.runs]
        out.append({"horse": n, "runs": runs})
        print(f"\n{n}" + ("" if hs else ": not held"))
        for x in runs:
            print(f"  {x['date']} {x['track'] or '?':18} {x['dist']}m {x['fin']}/{x['of']} {x['margin']}L ${x['sp']}  "
                  f"WFA {x['wfa']}  at weights {x['atWeights']}  race {x['raceRating']}")
print("\nJSON " + json.dumps(out, default=str))
