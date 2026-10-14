"""Scratched runners of a stored meeting with their timed flucs: the price each stood at when it was withdrawn (its last
fluc) and when, against the race's market open (first fluc of any runner). DB only, no credits. For deductions
(14 Oct 2026, founder: "We have to find a better way for deductions"): a fixed-odds deduction is set by the scratched
runner's price AT WITHDRAWAL, and only counts if the runner was scratched after the bet was struck.
    python scripts/scratch_flucs.py caulfield-20261014 [more meeting ids]"""
import os, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import psycopg
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fk import fields as F
MEL = ZoneInfo("Australia/Melbourne")
def ms(v):
    if v is None: return None
    if isinstance(v, (int, float)): return float(v)
    try: return datetime.fromisoformat(str(v).replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp() * 1000
    except Exception: return None
mel = lambda t: datetime.fromtimestamp(t / 1000, MEL).strftime("%a %H:%M")
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for mid in sys.argv[1:]:
        print(f"## {mid}")
        races = {}
        for rn, raw in c.execute("""select r.race_number, e.raw from fk.entries e join fk.races r using (race_id)
                                    where r.meeting_id = %s order by r.race_number""", (mid,)).fetchall():
            fl = sorted((t, float(p)) for t, p in ((ms(f.get("time")), f.get("price")) for f in ((raw.get("odds") or {}).get("flucs") or [])) if t and p)
            races.setdefault(rn, []).append((raw, fl))
        for rn, ents in sorted(races.items()):
            opens = [fl[0][0] for _, fl in ents if fl]
            t_open = min(opens) if opens else None
            for raw, fl in ents:
                if not F.entry_scratched(raw): continue
                name = raw.get("name") or (raw.get("horse") or {}).get("name")
                flt = " ".join(f"{mel(t)} ${p:g}" for t, p in fl[-6:])
                print(f"R{rn} {name} | market open {mel(t_open) if t_open else '?'} | first ${fl[0][1]:g} | last ${fl[-1][1]:g} at {mel(fl[-1][0])} | {len(fl)} flucs: {flt}" if fl else f"R{rn} {name} | no flucs (scratched before the market)")
