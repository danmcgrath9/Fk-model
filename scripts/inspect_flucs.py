"""What the stored odds hold for a few races on given dates (12 Nov 2026: why Nov 2025 - Aug 2026 has no timed prices).
DB and history files only, no credits.  python scripts/inspect_flucs.py 2025-12-13 2026-03-14 ..."""
import json, os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import load_settings
from fk import history as H
from fk.db import Db
ROOT = Path(__file__).resolve().parent.parent
db = Db(load_settings().database_url)
want = set(sys.argv[1:])
src = {}
for r in db.resulted_races("VIC"):
    d = str(r["date"])[:10]
    if d in want and d not in src: src[d] = ("db", r)
for r in H.resulted_races(ROOT / "history", "VIC"):
    d = str(r["date"])[:10]
    if d in want and d not in src: src[d] = ("history", r)
for d in sorted(want):
    if d not in src: print(f"## {d}: no resulted VIC race found"); continue
    where, r = src[d]; e = r["entries"][0]; o = e.get("odds") or {}
    fl = o.get("flucs") or []
    print(f"## {d} {r.get('track')} {r['race_id']} (from {where}, source {r.get('source')}, pulled {r.get('fetched_at') or r.get('pulled_at')})")
    print(f"  odds keys: {sorted(o.keys())}")
    print(f"  flucs: {len(fl)}; first three: {json.dumps(fl[:3])[:300]}")
    print(f"  entry keys with price/odd/fluc/open in the name: {[k for k in e.keys() if any(w in k.lower() for w in ('price', 'odd', 'fluc', 'open', 'sp'))]}")
    print(f"  race keys: {sorted(k for k in r.keys() if k != 'entries')[:40]}")
