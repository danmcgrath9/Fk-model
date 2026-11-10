"""Track bias table for the model (10 Nov 2026, founder: "have a go for every track and see if it makes our model
better"). Every stored past run (fk.past_events, each horse's run once, trials out) before --before, counted by track,
distance band, where the horse settled (1, 2-3, 4-6, 7+) and its barrier group (1-3, 4-6, 7-9, 10+): runs, winners
and the winners the bookmaker SP expected (sum of 1/SP). DB only, no credits. CSV between CSV-BEGIN and CSV-END.
    python scripts/track_bias_table.py --before 2025-07-01
The cutoff keeps the table out of the races the model is trained and tested on: the dataset starts 1 Jul 2025."""
from __future__ import annotations

import argparse
import collections
import os
import re
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fk import fields as F  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--before", default="2025-07-01")
ap.add_argument("--since", default="2015-01-01")
ap.add_argument("--rows", action="store_true", help="one line per run (date,track,band,settle,barrier,win,1/SP) instead of the table, "
                "so the model can count only runs before each race's own date")
a = ap.parse_args()


def band(d):
    return "-1100" if d <= 1100 else "1101-1300" if d <= 1300 else "1301-1600" if d <= 1600 else "1601-2000" if d <= 2000 else "2001-"


def sgroup(s):
    return "1" if s == 1 else "2-3" if s <= 3 else "4-6" if s <= 6 else "7+"


def bgroup(b):
    return "1-3" if b <= 3 else "4-6" if b <= 6 else "7-9" if b <= 9 else "10+"


cells = collections.defaultdict(lambda: [0, 0, 0.0])
ROWS = []   # (track, band, kind, group) -> runs, wins, expected
seen, n_runs = set(), 0
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    cur = c.cursor(name="tb")   # server-side cursor: the table is large
    cur.itersize = 5000
    cur.execute("select horse_id, event_date::date, raw from fk.past_events where event_date >= %s and event_date < %s",
                (a.since, a.before))
    for hid, d, raw in cur:
        r = F.run_ratings(raw)
        if r.get("trial"): continue
        trk = re.sub(r"[^a-z]", "", (r.get("track") or "").lower())
        try:
            dist, fin = float(r.get("distance")), int(r.get("finish"))
            sp = float(raw.get("startingPrice"))
        except (TypeError, ValueError):
            continue
        if not trk or not (sp > 1) or sp == float('inf') or (hid, str(d)) in seen: continue   # a blank SP is NaN, and NaN <= 1 is False
        seen.add((hid, str(d))); n_runs += 1
        bd, w = band(dist), int(fin == 1)
        if a.rows:
            pos = r.get("positions") or []
            try: sg = sgroup(int(float(pos[0]))) if int(float(pos[0])) >= 1 else ""
            except (TypeError, ValueError, IndexError): sg = ""
            try: bg = bgroup(int(float(raw.get("barrier")))) if int(float(raw.get("barrier"))) >= 1 else ""
            except (TypeError, ValueError): bg = ""
            ROWS.append(f"{d},{trk},{bd},{sg},{bg},{w},{1/sp:.4f}")
            continue
        keys = [(trk, bd, "all", "all")]
        pos = r.get("positions") or []
        try:
            s = int(float(pos[0]))
            if s >= 1: keys.append((trk, bd, "settle", sgroup(s)))
        except (TypeError, ValueError, IndexError):
            pass
        try:
            b = int(float(raw.get("barrier")))
            if b >= 1: keys.append((trk, bd, "barrier", bgroup(b)))
        except (TypeError, ValueError):
            pass
        for k in keys:
            x = cells[k]; x[0] += 1; x[1] += w; x[2] += 1 / sp
if a.rows:
    print(f"{n_runs} runs before {a.before} (since {a.since})")
    print("CSV-BEGIN"); print("date,track,band,settle,barrier,win,inv_sp"); print("\n".join(sorted(ROWS))); print("CSV-END")
    sys.exit(0)
print(f"{n_runs} runs before {a.before} (since {a.since}), {len({k[0] for k in cells})} tracks, {len(cells)} cells")
print("CSV-BEGIN")
print("track,band,kind,group,runs,wins,expected")
for (t, bd, kd, g), (n, w, e) in sorted(cells.items()):
    print(f"{t},{bd},{kd},{g},{n},{w},{e:.3f}")
print("CSV-END")
