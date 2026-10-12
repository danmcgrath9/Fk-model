"""Scratched runners' opening prices, per resulted VIC race (13 Oct 2026, Dave: "are you handling scratchings at the
open?"). A fixed-odds bet struck at the open takes a deduction for every runner scratched after it, so settling at the
open needs each scratched runner's price. Prints CSV: race_id, starters, scratched, the scratched runners' average
opening prices (semicolon separated, blank when Form King holds none). Database and history files only, no credits.
    python scripts/scratch_opens.py 2025-07-01"""
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import load_settings
from fk import fields as F
from fk import history as H
from fk.db import Db
since = sys.argv[1] if len(sys.argv) > 1 else "2025-07-01"
ROOT = Path(__file__).resolve().parent.parent
db = Db(load_settings().database_url)
rows = [r for r in db.resulted_races("VIC") if str(r["date"])[:10] >= since]
held = {r["race_id"] for r in rows}
rows += [r for r in H.resulted_races(ROOT / "history", "VIC", skip=held) if str(r["date"])[:10] >= since]
print("CSV-BEGIN"); print("race_id,starters,scratched,scratched_with_open,scratched_opens")
tot = scr = withp = 0
for r in rows:
    ents = r["entries"]; s = [e for e in ents if F.entry_scratched(e)]
    ops = [F.odds_opening_price(e.get("odds") or {}) for e in s]
    tot += 1; scr += len(s); withp += sum(1 for o in ops if o)
    print(f"{r['race_id']},{len(ents) - len(s)},{len(s)},{sum(1 for o in ops if o)},{';'.join(str(o) for o in ops if o)}")
print("CSV-END"); print(f"{tot} races, {scr} scratched runners, {withp} with an opening price", file=sys.stderr)
