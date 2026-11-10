"""Track bias: win ROI by position in the run and by barrier at one track and distance, from every stored past run
(fk.past_events; each horse's run once, trials out). DB only, no credits. (10 Nov 2026, founder: "What's the ROI for
1200m sandown lakeside with position in run / barriers".)
    python scripts/track_bias.py Sandown_Lakeside 1200 [--tol 0] [--since 2024-01-01]
    python scripts/track_bias.py ALL 1200 --since 2025-01-01      (every track: the baseline)
Underscores stand for spaces. ROI is 1u level stakes at the bookmaker SP, and at Betfair SP where Form King has one
(8% commission on winnings). Position in the run is where the horse settled (Form King's first position call), known
only after the race: it says which running style the track rewards, the speedmap says who will run that way."""
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
ap.add_argument("track"); ap.add_argument("distance", type=int)
ap.add_argument("--tol", type=int, default=0, help="metres either side of the distance")
ap.add_argument("--since", default="2023-01-01")
a = ap.parse_args()
ALL = a.track.upper() == "ALL"    # every track: the baseline to compare one track against
want = re.sub(r"[^a-z]", "", a.track.replace("_", " ").lower())
words = [] if ALL else [w for w in a.track.replace("_", " ").split() if w]

num = lambda v: (float(v) if v not in (None, "") else None) if not isinstance(v, (int, float)) else float(v)
runs, seen = [], set()
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    q = "select horse_id, event_date::date, raw from fk.past_events where event_date >= %s" + "".join(
        " and raw::text ilike %s" for _ in words)
    for hid, d, raw in c.execute(q, (a.since, *[f"%{w}%" for w in words])):
        r = F.run_ratings(raw)
        if r.get("trial") or (not ALL and re.sub(r"[^a-z]", "", (r.get("track") or "").lower()) != want): continue
        dist = r.get("distance")
        if dist is None or abs(float(dist) - a.distance) > a.tol: continue
        if (hid, str(d)) in seen: continue
        seen.add((hid, str(d)))
        pos = r.get("positions") or []
        try:
            fin, n = int(r.get("finish")), int(r.get("runners"))
        except (TypeError, ValueError):
            continue
        runs.append(dict(date=str(d), fin=fin, n=n, settle=num(pos[0]) if pos else None, barrier=num(raw.get("barrier")),
                         sp=num(raw.get("startingPrice")), bsp=num(raw.get("bsp")), going=str(raw.get("going") or "")))
print(f"{a.track.replace('_', ' ')} {a.distance}m (+/-{a.tol}m) since {a.since}: {len(runs)} runs, "
      f"{len({r['date'] for r in runs})} race days, {sum(r['fin'] == 1 for r in runs)} winners; "
      f"settling position on {sum(r['settle'] is not None for r in runs)}, BSP on {sum(r['bsp'] is not None for r in runs)}\n")


def line(label, g):
    n = len(g); w = sum(r["fin"] == 1 for r in g)
    sp = [r for r in g if r["sp"] and r["sp"] > 1]; bsp = [r for r in g if r["bsp"] and r["bsp"] > 1]
    roi_sp = sum((r["sp"] - 1) if r["fin"] == 1 else -1 for r in sp) / len(sp) if sp else float("nan")
    roi_bsp = sum((r["bsp"] - 1) * 0.92 if r["fin"] == 1 else -1 for r in bsp) / len(bsp) if bsp else float("nan")
    exp = sum(1 / r["sp"] for r in sp)
    ae = sum(r["fin"] == 1 for r in sp) / exp if exp else float("nan")
    print(f"  {label:22} {n:5d} runs {w:4d} won ({100*w/max(n,1):4.1f}%)  A/E at SP {ae:4.2f}  ROI at SP {100*roi_sp:+6.1f}%"
          f"  at BSP {100*roi_bsp:+6.1f}% ({len(bsp)})")


def settle_band(r):
    s = r["settle"]
    if s is None: return None
    return "1 led" if s == 1 else "2-3 on pace" if s <= 3 else "4-6 midfield" if s <= 6 else "7+ back"


def bar_band(r):
    b = r["barrier"]
    if not b: return None
    return "1-3" if b <= 3 else "4-6" if b <= 6 else "7-9" if b <= 9 else "10+"


print("BY POSITION IN THE RUN (where it settled)")
for k in ("1 led", "2-3 on pace", "4-6 midfield", "7+ back"):
    line(k, [r for r in runs if settle_band(r) == k])
print("\nBY BARRIER")
for k in ("1-3", "4-6", "7-9", "10+"):
    line(f"barrier {k}", [r for r in runs if bar_band(r) == k])
print("\nPOSITION x BARRIER (win % and ROI at SP)")
for k in ("1 led", "2-3 on pace", "4-6 midfield", "7+ back"):
    for b in ("1-3", "4-6", "7-9", "10+"):
        g = [r for r in runs if settle_band(r) == k and bar_band(r) == b]
        if len(g) >= 15: line(f"{k}, barrier {b}", g)
gb = collections.defaultdict(list)
for r in runs:
    g = r["going"].lower()
    gb["good/firm" if g.startswith(("good", "firm")) else "soft/heavy" if g.startswith(("soft", "heavy")) else "other"].append(r)
print("\nPOSITION BY GOING")
for gk in ("good/firm", "soft/heavy"):
    for k in ("1 led", "2-3 on pace", "4-6 midfield", "7+ back"):
        g = [r for r in gb[gk] if settle_band(r) == k]
        if len(g) >= 15: line(f"{gk}: {k}", g)
