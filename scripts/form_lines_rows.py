"""Form lines: every stored run with the horse's NEXT run beside it, so a model can ask how the horses from a past race
went at their next start (10 Nov 2026, founder: "Yes" to testing Phil M's "subsequent runs from each race" from the
Form King Slack). DB only, no credits. One CSV line per run (trials out): race id, date, horse (short tag), finish,
margin, and the horse's next race run: its date, whether it won, and 1/SP. CSV between CSV-BEGIN and CSV-END.
    python scripts/form_lines_rows.py [--since 2023-01-01] [--full --history history]

--full (11 Nov 2026) reads every run we hold, not just fk.past_events: every runner of every stored race (fk.results)
and of every back-test race (the history files), with each runner's own past events on its card, through
scripts/racemates.py. A race held whole then lists its whole field, where fk.past_events gave about two horses a race.
Margins are not carried by the full source and print blank (t_formlines_ab.py does not read them)."""
from __future__ import annotations

import argparse
import collections
import hashlib
import os
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fk import fields as F  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument("--since", default="2023-01-01")
ap.add_argument("--full", action="store_true"); ap.add_argument("--history", default="history")
a = ap.parse_args()
num = lambda v: float(v) if v not in (None, "") else None
runs = collections.defaultdict(list)   # horse -> [(date, race_id, finish, margin, sp)]
if a.full:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import racemates as RM  # noqa: E402
    allruns, _, _, _ = RM.load(a.history, since=a.since, log=lambda m: print(m, file=sys.stderr))
    for hid, rs in allruns.items():
        for d, rid, fin, sp in rs:
            if d >= a.since and sp is not None and sp > 1:
                runs[hid].append((d, rid, fin, None, sp))
else:
    with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
        cur = c.cursor(name="fl"); cur.itersize = 5000
        cur.execute("select horse_id, event_date::date, raw from fk.past_events where event_date >= %s", (a.since,))
        for hid, d, raw in cur:
            if F.past_event_is_trial(raw) or not F.past_event_is_race(raw): continue
            rid = F.past_event_race_id(raw)
            if not rid: continue
            try:
                fin = int(F.past_event_finish(raw)); sp = float(raw.get("startingPrice"))
            except (TypeError, ValueError):
                continue
            if not (sp > 1) or sp == float("inf"): continue
            runs[hid].append((str(d), str(rid), fin, F.past_event_margin(raw), sp))
out = []
for hid, rs in runs.items():
    rs = sorted(set(rs))
    tag = hashlib.sha1(hid.encode()).hexdigest()[:10]
    for i, (d, rid, fin, mar, sp) in enumerate(rs):
        nxt = next((x for x in rs[i + 1:] if x[0] > d), None)
        out.append(f"{rid},{d},{tag},{fin},{'' if mar is None else round(mar, 2)},"
                   + (f"{nxt[0]},{int(nxt[2] == 1)},{1 / nxt[4]:.4f}" if nxt else ",,"))
print(f"{len(out)} runs of {len(runs)} horses since {a.since}")
print("CSV-BEGIN"); print("race_id,date,horse,finish,margin,next_date,next_won,next_inv_sp"); print("\n".join(sorted(out))); print("CSV-END")
