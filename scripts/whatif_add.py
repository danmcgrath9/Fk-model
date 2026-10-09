"""What-if: add a horse to a race it is not in, and export that day for pricing. The horse's most recent stored entry
(form, profile) is copied into the target race, with every past event we hold for it merged in, so its latest run counts.
The entry is brought up to today: days since its last run, run in prep, and its conditions records (career, distance,
first-up, going, track) count that last run. Barrier set to the middle of the field (its real draw is unknown); no
speed-map line (it was never in this race's map). Reads the database only, no credits.

Optional scenario, rewriting the horse's run on one date (and everything derived from it):
    --run 2026-09-30 finish=1 margin=3 rating=85 sections=closing,mid
  rating sets atWeights; the other ratings, the lengths-vs-benchmark figures and the speed rating move by the same gap
  (about 2 rating points a length, 1.4 speed points a length, Form King's own scales on this horse's run); the chosen
  200m splits (closing = the last 600, mid = 1000 to 600) share that many lengths.
Prints each export as base64 between NPZ-BEGIN <label> / NPZ-END.

    python scripts/whatif_add.py 2026-10-10 Caulfield 2 "Cavill Avenue" "Good 4" [--run ...]
"""
import base64, os, sys, copy
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import export_dataset as X
from fk import fields as F
from fk import backtest as B
from fk.config import load_settings
from fk.db import Db

args = sys.argv[1:]
run_over = {}
if "--run" in args:
    i = args.index("--run"); run_date = args[i + 1]; kv = args[i + 2:]; args = args[:i]
    run_over = dict(x.split("=", 1) for x in kv)
day, track, rn, name, going = args[0], args[1], int(args[2]), args[3], args[4]
db = Db(load_settings().database_url)
rows0 = X.upcoming_rows(db, day, track, "VIC")
src = db.conn.execute("""select e.raw, r.meeting_id, r.race_number from fk.entries e join fk.races r using (race_id)
                         where lower(coalesce(e.raw->'horse'->>'name', e.raw->>'horseName', e.raw->>'name')) = lower(%s)
                         order by r.meeting_id desc limit 1""", (name,)).fetchone()
base = copy.deepcopy(src[0]); hid = F.horse_id(base)
have = {(str(p.get("raceId")), str(F.past_event_date(p))) for p in F.entry_past_events(base)}
extra = [pe["raw"] for pe in db.past_events_for_horse(hid, 40)
         if (str(pe["raw"].get("raceId")), str(F.past_event_date(pe["raw"]))) not in have]
base["pastEvents"] = list(F.entry_past_events(base)) + extra
tgt0 = next(r for r in rows0 if int(r["race_number"]) == rn)
today_dist = int(tgt0["distance_m"] or 0); today_band = B.going_band(going); today_track = (track or "").lower()
SPLITS = {"closing": ["6-4", "4-2", "2-F"], "mid": ["10-8", "8-6"]}
COMPOSITE = {"6-F": ["6-4", "4-2", "2-F"], "4-F": ["4-2", "2-F"], "8-4": ["8-6", "6-4"], "8-F": ["8-6", "6-4", "4-2", "2-F"],
             "S-6": ["10-8", "8-6"], "S-8": ["10-8"]}


def bump(rec, finish):
    s, w, p2, p3 = X.record(rec) or (0, 0, 0, 0)
    return f"{s + 1}:{w + (finish == 1)}-{p2 + (finish == 2)}-{p3 + (finish == 3)}"


def rewrite(p, over):
    b = p.setdefault("benchmark", {})
    rating = float(over["rating"]); d = rating - float(b.get("atWeights") or rating); L = d / 2.0
    b["atWeights"] = rating
    for k in ("wfaRat",):
        if b.get(k) is not None: b[k] = float(b[k]) + d
    for k in ("weightForAgeRating", "adjustedForTodaysWeight"):
        if p.get(k) is not None: p[k] = float(p[k]) + d
    for k in ("vsClass", "vsTrack", "vsAllAvg"):
        if b.get(k) is not None: b[k] = float(b[k]) + L
    if b.get("speedRating") is not None: b["speedRating"] = float(b["speedRating"]) + 1.4 * L
    chosen = [s for g in str(over.get("sections", "")).split(",") if g for s in SPLITS[g]]
    if chosen:
        per = L / len(chosen); secs = b.setdefault("sections", {})
        gain = {k: per for k in chosen}
        for k, parts in COMPOSITE.items(): gain[k] = sum(per for x in parts if x in chosen)
        for k, g in gain.items():
            if not g: continue
            sec = secs.setdefault(k, {})
            for m in ("vsClass", "vsLeader", "vsField"):
                sec[m] = float(sec.get(m) or 0.0) + g
        if "closing" in over.get("sections", "") and b.get("finishingSpeed") is not None:
            b["finishingSpeed"] = float(b["finishingSpeed"]) + 0.4 * sum(per for x in SPLITS["closing"] if x in chosen)
    p["finishPosition"] = int(over.get("finish", p.get("finishPosition") or 1)); p["margin"] = float(over.get("margin", p.get("margin") or 0))
    if p["finishPosition"] == 1:
        b["pir2"], b["pir4"] = 1, min(int(b.get("pir4") or 3), 3); p["pos400m"] = b["pir4"]
    return d


def bring_to_today(e, over_date=None, over=None):
    """The entry as of today: its newest run counted in days, prep and conditions records."""
    runs = sorted([p for p in F.entry_past_events(e) if not p.get("scratched") and F.past_event_date(p) and F.past_event_date(p) < day],
                  key=lambda p: F.past_event_date(p), reverse=True)
    last = runs[0]; note = ""
    if over_date and F.past_event_date(last) == over_date:
        d = rewrite(last, over); note = f"rewritten: finish {last['finishPosition']} margin {last['margin']} rating {over['rating']} ({d:+.1f})"
        pk = e.setdefault("ratings", {})
        for k in ("peak", "peak12m"):
            pk[k] = max(float(pk.get(k) or 0), float(over["rating"]))
    fin = int(last.get("finishPosition") or 0); ld = F.past_event_date(last)
    e["daysSinceLastRace"] = (date.fromisoformat(day) - date.fromisoformat(ld)).days
    e["raceInPrep"] = int(last.get("raceInPrep") or 1) + 1
    if fin == 1: e["daysSinceLastWin"] = e["daysSinceLastRace"]
    form = e.setdefault("form", {})
    keys = ["careerForm"]
    if int(last.get("distance") or 0) == today_dist: keys += ["distanceForm"]
    if abs(int(last.get("distance") or 0) - today_dist) <= 200: keys += ["similarDistance"]
    if int(last.get("raceInPrep") or 0) == 1: keys += ["firstUpForm"]
    if B.going_band(last.get("going")) == today_band: keys += ["todaysGoingForm"]
    if str(last.get("track") or "").lower() == today_track: keys += ["trackForm"]
    for k in keys:
        form[k] = bump(form.get(k), fin)
    return f"last run {ld} ({last.get('track')}) finish {fin}; {note} days since {e['daysSinceLastRace']}, run {e['raceInPrep']} in prep; records bumped: {keys}"


def export(e, label):
    rows = copy.deepcopy(rows0); tgt = next(r for r in rows if int(r["race_number"]) == rn)
    n = len(tgt["entries"]) + 1; e["barrier"] = (n + 1) // 2
    for k in ("scratched", "emergency"): e[k] = False
    tgt["entries"] = list(tgt["entries"]) + [e]
    X.upcoming_rows = lambda db_, d, t, s: rows
    out = f"/tmp/whatif_{label}.npz"
    sys.argv = ["export_dataset.py", "--date", day, "--track", track, "--going", going, "--out", out]
    X.main()
    print(f"NPZ-BEGIN {label}"); print(base64.b64encode(open(out, "rb").read()).decode()); print("NPZ-END")


e0 = copy.deepcopy(base)
print(f"{name} from {src[1]} R{src[2]}, added to {track} R{rn} (barrier mid-field). As run: " + bring_to_today(e0), file=sys.stderr)
export(e0, "asrun")
if run_over:
    e1 = copy.deepcopy(base)
    print(f"Scenario: " + bring_to_today(e1, run_date, run_over), file=sys.stderr)
    export(e1, "scenario")
