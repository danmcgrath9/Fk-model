"""What-if: add a horse to a race it is not in, and export that day for pricing. The horse's most recent stored entry
(form, profile) is copied into the target race, with every past event we hold for it merged in, so its latest run counts.
Barrier set to the middle of the field (its real draw is unknown); no speed-map line (it was never in this race's map).
Reads the database only, no credits. Prints the npz as base64 between NPZ-BEGIN / NPZ-END.

    python scripts/whatif_add.py 2026-10-10 Caulfield 3 "Cavill Avenue" "Good 4"
"""
import base64, os, sys, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import export_dataset as X
from fk import fields as F
from fk.config import load_settings
from fk.db import Db

day, track, rn, name, going = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
db = Db(load_settings().database_url)
rows = X.upcoming_rows(db, day, track, "VIC")
tgt = next(r for r in rows if int(r["race_number"]) == rn)
src = db.conn.execute("""select e.raw, r.meeting_id, r.race_number from fk.entries e join fk.races r using (race_id)
                         where lower(coalesce(e.raw->'horse'->>'name', e.raw->>'horseName', e.raw->>'name')) = lower(%s)
                         order by r.meeting_id desc limit 1""", (name,)).fetchone()
e = copy.deepcopy(src[0]); hid = F.horse_id(e)
have = {(str(p.get("raceId")), str(F.past_event_date(p))) for p in F.entry_past_events(e)}
extra = [pe["raw"] for pe in db.past_events_for_horse(hid, 40)
         if (str(pe["raw"].get("raceId")), str(F.past_event_date(pe["raw"]))) not in have]
e["pastEvents"] = list(F.entry_past_events(e)) + extra
n = len(tgt["entries"]) + 1
e["barrier"] = (n + 1) // 2
for k in ("scratched", "emergency"): e[k] = False
tgt["entries"] = list(tgt["entries"]) + [e]
print(f"{name} ({hid}) from {src[1]} R{src[2]}: {len(extra)} past events merged in, newest {max((str(F.past_event_date(p)) for p in e['pastEvents']), default='-')}; "
      f"added to {track} R{rn} as runner {n}, barrier {e['barrier']}", file=sys.stderr)
real = X.upcoming_rows
X.upcoming_rows = lambda db_, d, t, s: rows
out = "/tmp/whatif.npz"
sys.argv = ["export_dataset.py", "--date", day, "--track", track, "--going", going, "--out", out]
X.main()
print("NPZ-BEGIN"); print(base64.b64encode(open(out, "rb").read()).decode()); print("NPZ-END")
