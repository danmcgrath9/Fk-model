"""One stored meeting's runners with their average price at the race's open and 30/40/45/50/60/90 min after it, and the
latest best/average and the bookmakers on the best (27 Oct 2026, for the 30-90 min after-open top-up on a meeting that
has not run). DB only, no credits; the flucs are as of the last stored pull. CSV between CSV-BEGIN and CSV-END.
    python scripts/fluc_meeting.py swan-hill-20261027"""
import os, sys
from datetime import datetime, timezone
import psycopg
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fk import fields as F
def ms(v):
    if v is None: return None
    if isinstance(v, (int, float)): return float(v)
    try: return datetime.fromisoformat(str(v).replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp() * 1000
    except Exception: return None
MINS = (30, 40, 45, 50, 60, 90)
print("CSV-BEGIN"); print("race,race_id,horse_id,number,name,scratched,race_open_ms,last_ms,open," + ",".join(f"m{m}" for m in MINS) + ",avg_now,best_now,best_bookies")
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for mid in sys.argv[1:]:
        races = {}
        for rn, rid, raw in c.execute("""select r.race_number, r.race_id, e.raw from fk.entries e join fk.races r using (race_id)
                                         where r.meeting_id = %s order by r.race_number""", (mid,)).fetchall():
            o = raw.get("odds") or {}
            fl = sorted((t, float(p)) for t, p in ((ms(f.get("time")), f.get("price")) for f in (o.get("flucs") or [])) if t and p)
            races.setdefault((rn, rid), []).append((raw, o, fl))
        for (rn, rid), ents in sorted(races.items()):
            opens = [fl[0][0] for _, _, fl in ents if fl]
            t0 = min(opens) if opens else None
            for raw, o, fl in ents:
                def upto(cut):
                    p = [x for t, x in fl if t <= cut]; return p[-1] if p else ""
                a = [upto(t0 + m * 60e3) if t0 and fl and t0 + m * 60e3 <= fl[-1][0] else "" for m in MINS]
                nm = str(raw.get("name") or (raw.get("horse") or {}).get("name") or "").replace(",", " ")
                bb = " ".join(str(b).replace(",", " ") for b in (o.get("bestBookies") or []))
                print(f"{rn},{rid},{F.horse_id(raw)},{F.entry_number(raw) or ''},{nm},{int(bool(F.entry_scratched(raw)))},{int(t0) if t0 else ''},"
                      f"{int(fl[-1][0]) if fl else ''},{fl[0][1] if fl else ''},{','.join(str(x) for x in a)},"
                      f"{o.get('avgNow') or ''},{o.get('bestNow') or ''},{bb}")
print("CSV-END")
