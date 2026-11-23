"""The highest Form King weight-for-age ratings by a group of horses since a date, from fk.past_events (founder, 23 Nov
2026: "That would nearly make her the best 3yo filly in the country cavill avenue"). DB only, no credits.

    python scripts/top_ratings.py [--age 3] [--sex filly] [--since 2026-08-01] [--top 30]

A horse's age and sex come from its stored entries (horse.age, horse.type: Filly / Mare / Colt / Gelding ...), so a horse
is in it if it has an entry still held (the weekly clear-out keeps 21 days of entries). Coverage: every horse that has run in a race we pulled, with the runs
Form King gave us for it, which is Victoria plus the interstate runs of horses that came here; a filly that has
only raced interstate and never met a horse we pulled is not in it.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fk import fields as F  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--age", default="3", help="age as Form King gives it on the horse's entries this season")
ap.add_argument("--sex", default="filly")
ap.add_argument("--since", default="2026-08-01")
ap.add_argument("--top", type=int, default=30)
a = ap.parse_args()

with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    sex = {}
    print("sample ids:", c.execute("select horse_id, raw->'horse'->>'age', raw->'horse'->>'type' from fk.entries limit 3").fetchall())
    for hid, age, s in c.execute(
            "select horse_id, raw->'horse'->>'age', raw->'horse'->>'type' from fk.entries where raw->'horse'->>'age' = %s", (a.age,)):
        if s:
            sex[hid] = s.lower()
    names = dict(c.execute("select horse_id, name from fk.horses where horse_id = any(%s)", (list(sex),)).fetchall())
    want = {h for h, s in sex.items() if s.startswith(a.sex[0]) or (a.sex == "filly" and s.startswith("m"))}   # Filly or F, Mare or M
    best = {}
    for hid, d, raw in c.execute(
            "select horse_id, event_date::date, raw from fk.past_events where horse_id = any(%s) and event_date >= %s",
            (list(want), a.since)):
        if hid not in want or raw.get("trial"):
            continue
        r = F.run_ratings(raw)
        w = r["wfaRat"] or r["wfa"]
        if not w:
            continue
        run = (float(w), str(d), r["track"], r["distance"], r["finish"], r["runners"], raw.get("startingPrice"))
        b = best.setdefault(hid, {"best": run, "last": run, "n": 0})
        b["n"] += 1
        if run[0] > b["best"][0]:
            b["best"] = run
        if run[1] > b["last"][1]:
            b["last"] = run

print(f"age {a.age}, {a.sex}, runs since {a.since}: {len(want)} horses of that sex held, {len(best)} with a rated run")
print("| # | Horse | Best | Best run | Last | Last run |")
print("|---|---|---|---|---|---|")
for i, (hid, b) in enumerate(sorted(best.items(), key=lambda x: -x[1]["best"][0])[: a.top], 1):
    f = lambda r: f"{r[4]}/{r[5]} {r[2]} {r[3]}m {r[1]} ${r[6]}"
    print(f"| {i} | {names.get(hid, hid)} | {b['best'][0]:.1f} | {f(b['best'])} | {b['last'][0]:.1f} | {f(b['last'])} |")
