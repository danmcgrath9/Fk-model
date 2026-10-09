"""Model day files straight from Dave's archive, no pull (9 Oct 2026): each race's Get Race Form payload and its
meeting's speedmaps go through fk.history.race_bundle, the same transform the history files use, and then through
export_dataset's own day export. The same days are exported from our database too (ours_*.npz), so the two copies
can be priced side by side. Writes npz_out/arch_YYYY-MM-DD.npz and npz_out/ours_YYYY-MM-DD.npz.
python scripts/archive_export.py ARCHIVE_DIR [STATE]"""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import export_dataset as X
from fk.history import race_bundle
root = sys.argv[1]; state = sys.argv[2] if len(sys.argv) > 2 else "VIC"
idx = json.load(open(os.path.join(root, "index.json")))
by_day = collections.defaultdict(list)
for d in idx["days"]:
    for m in d["meetings"]:
        if m.get("state") != state: continue
        md = os.path.join(root, "meetings", m["meetingId"])
        meeting = json.load(open(os.path.join(md, "summary.json")))
        sms = json.load(open(os.path.join(md, "speedmaps.json"))) if os.path.exists(os.path.join(md, "speedmaps.json")) else []
        sm_by = {str(s.get("raceId")): s for s in (sms if isinstance(sms, list) else [sms])}
        races_meta = {str(r.get("raceId")): r for r in meeting.get("races", [])}
        for rid in m["raceIds"]:
            A = json.load(open(os.path.join(md, "races", f"{rid}.json")))
            b = race_bundle(meeting, A, sm_by.get(rid))
            rm = races_meta.get(rid, {})
            b["going"] = " ".join(str(x) for x in (rm.get("going") or A.get("going"), rm.get("goingNumber") or A.get("goingNumber")) if x) or None
            b["race_number"] = rm.get("number") or A.get("number")
            if b.get("lws") is None and rm.get("lws") is not None: b["lws"] = float(rm["lws"])
            by_day[str(b["date"])[:10]].append(b)
os.makedirs("npz_out", exist_ok=True)
real_upcoming = X.upcoming_rows
print("days:", {k: len(v) for k, v in sorted(by_day.items())}, flush=True)
for day, rows in sorted(by_day.items()):
    rows.sort(key=lambda r: (r["track"], r["race_number"] or 0))
    X.upcoming_rows = lambda db, dd, track, st, _rows=rows: _rows
    sys.argv = ["export_dataset.py", "--date", day, "--state", state, "--out", f"npz_out/arch_{day}.npz"]; X.main()
    X.upcoming_rows = real_upcoming
    sys.argv = ["export_dataset.py", "--date", day, "--state", state, "--out", f"npz_out/ours_{day}.npz"]; X.main()
print(sorted(os.listdir("npz_out")))
