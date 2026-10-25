"""Day files from a Form King archive for ANY state (23 Oct 2026; in scripts/ from 25 Oct so the fk-archive workflow can run it: the npz_out folder is pushed to the archive-replay branch). Same transform as
scripts/archive_export.py (race_bundle -> export_dataset's day export) but the "ours_" side is skipped and
the Db is stubbed, because the cloud session holds no DATABASE_URL.
python arch_export_states.py ARCHIVE_DIR OUT_DIR STATE [STATE...]"""
import json, os, sys, collections
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts")); sys.path.insert(0, REPO)
os.environ.setdefault("DATABASE_URL", "postgresql://stub/stub")
import export_dataset as X
import fk.db as fkdb
from fk.history import race_bundle


class _StubDb:  # upcoming_rows is patched, so the connection is never used
    def __init__(self, url): self.conn = None


fkdb.Db = _StubDb
root, outdir, states = sys.argv[1], sys.argv[2], sys.argv[3:]
os.makedirs(outdir, exist_ok=True)
idx = json.load(open(os.path.join(root, "index.json")))
for state in states:
    by_day = collections.defaultdict(list)
    for d in idx["days"]:
        for m in d["meetings"]:
            if m.get("state") != state: continue
            md = os.path.join(root, "meetings", m["meetingId"])
            meeting = json.load(open(os.path.join(md, "summary.json")))
            smp = os.path.join(md, "speedmaps.json")
            sms = json.load(open(smp)) if os.path.exists(smp) else []
            sm_by = {str(s.get("raceId")): s for s in (sms if isinstance(sms, list) else [sms])}
            races_meta = {str(r.get("raceId")): r for r in meeting.get("races", [])}
            for rid in m["raceIds"]:
                rp = os.path.join(md, "races", f"{rid}.json")
                if not os.path.exists(rp): continue
                A = json.load(open(rp))
                try:
                    b = race_bundle(meeting, A, sm_by.get(rid))
                except Exception as e:  # a race the transform cannot read is named, not skipped silently
                    print(f"SKIP {state} {m['meetingId']} {rid}: {type(e).__name__}: {e}", flush=True); continue
                rm = races_meta.get(rid, {})
                b["going"] = " ".join(str(x) for x in (rm.get("going") or A.get("going"), rm.get("goingNumber") or A.get("goingNumber")) if x) or None
                b["race_number"] = rm.get("number") or A.get("number")
                if b.get("lws") is None and rm.get("lws") is not None: b["lws"] = float(rm["lws"])
                by_day[str(b["date"])[:10]].append(b)
    print(state, "days:", {k: len(v) for k, v in sorted(by_day.items())}, flush=True)
    for day, rows in sorted(by_day.items()):
        rows.sort(key=lambda r: (r["track"], r["race_number"] or 0))
        X.upcoming_rows = lambda db, dd, track, st, _rows=rows: _rows
        sys.argv = ["export_dataset.py", "--date", day, "--state", state, "--out", os.path.join(outdir, f"arch_{state}_{day}.npz")]
        X.main()
print(sorted(os.listdir(outdir)))
