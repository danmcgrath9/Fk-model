"""Point-in-time check: Dave's clean historical archive against the same races in our database (8 Oct 2026).

For every race in the archive that we also hold, each entry's race-form JSON is flattened to numeric leaves and
compared field by field with our stored copy (fk.entries.raw, matched by horse), and each race's own fields with
fk.races.raw. Reports, per field (list positions folded to []), how many values were compared, how many differ, and
the typical size of the difference: the fields that moved between our pull and Dave's point-in-time rebuild are the
ones that could have leaked post-race information into our training data. DB read only, no credits.
python scripts/archive_compare.py ARCHIVE_DIR [STATE]"""
import json, os, re, sys, collections
import psycopg

root = sys.argv[1]; state = sys.argv[2] if len(sys.argv) > 2 else "VIC"
idx = json.load(open(os.path.join(root, "index.json")))
want = [(m["meetingId"], m["raceIds"]) for d in idx["days"] for m in d["meetings"] if m.get("state") == state]

def flat(x, pre="", out=None):
    out = {} if out is None else out
    if isinstance(x, dict):
        for k, v in x.items(): flat(v, f"{pre}.{k}" if pre else k, out)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            k = None
            if isinstance(v, dict):   # key list items by their own id/date, not position: lists can be shifted
                for kk in ("raceId", "eventId", "id", "pastEventId", "date", "meetingDate"):
                    if v.get(kk) not in (None, ""): k = f"{kk}={v[kk]}"; break
            flat(v, f"{pre}[{k or i}]", out)
    elif isinstance(x, bool) or x is None: pass
    elif isinstance(x, (int, float)): out[pre] = float(x)
    return out
fold = lambda p: re.sub(r"\[[^\]]*\]", "[]", p)
hid = lambda e: (e.get("horse") or {}).get("id") or e.get("horseId") or (e.get("horse") or {}).get("breedingId") or e.get("breedingId")
hname = lambda e: ((e.get("horse") or {}).get("name") or e.get("horseName") or e.get("name") or "").lower()

stats = collections.defaultdict(lambda: [0, 0, 0.0, []])   # field -> compared, differ, sum abs diff, examples
only_arch = collections.Counter(); only_db = collections.Counter()
n_races = n_entries = missing_races = 0
contam = [0, 0, 0, 0]; contam_ex = []
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for mid, race_ids in want:
        for rid in race_ids:
            fp = os.path.join(root, "meetings", mid, "races", f"{rid}.json")
            if not os.path.exists(fp): continue
            A = json.load(open(fp))
            row = c.execute("select raw from fk.races where race_id=%s", (rid,)).fetchone()
            if not row: missing_races += 1; continue
            n_races += 1
            ents = {r[0]: r[1] for r in c.execute("select horse_id, raw from fk.entries where race_id=%s", (rid,)).fetchall()}
            byname = {hname(v): v for v in ents.values()}
            pairs = [("race", {k: v for k, v in A.items() if k != "entries"}, {k: v for k, v in (row[0] or {}).items() if k != "entries"})]
            for e in A.get("entries", []):
                d = ents.get(hid(e)) or byname.get(hname(e))
                if d is None: continue
                n_entries += 1; pairs.append(("entry", e, d))
            rdate = str(A.get("date") or "")
            for kind, a, b in pairs:
                if kind == "entry":   # contamination: past events in OUR copy dated on/after this race
                    for lst in ("pastEvents",):
                        ours = [str(x.get("date") or x.get("meetingDate") or "") for x in (b.get(lst) or []) if isinstance(x, dict)]
                        arch = [str(x.get("date") or x.get("meetingDate") or "") for x in (a.get(lst) or []) if isinstance(x, dict)]
                        later_ours = sum(1 for d in ours if rdate and d and d[:8] >= rdate[:8])
                        later_arch = sum(1 for d in arch if rdate and d and d[:8] >= rdate[:8])
                        contam[0] += 1; contam[1] += later_ours > 0; contam[2] += later_arch > 0; contam[3] += len(ours) - len(arch)
                        if later_ours and len(contam_ex) < 5: contam_ex.append(f"{rid} {hname(a)}: race {rdate}, our latest past event {max(ours)}")
                fa, fb = flat(a), flat(b)
                for p in fa.keys() - fb.keys(): only_arch[f"{kind}:{fold(p)}"] += 1
                for p in fb.keys() - fa.keys(): only_db[f"{kind}:{fold(p)}"] += 1
                for p in fa.keys() & fb.keys():
                    s = stats[f"{kind}:{fold(p)}"]; s[0] += 1
                    dif = abs(fa[p] - fb[p])
                    if dif > 1e-6:
                        s[1] += 1; s[2] += dif
                        if len(s[3]) < 3: s[3].append(f"{rid} {hname(a) if kind=='entry' else ''} {fb[p]:g}->{fa[p]:g}")
print(f"# Archive vs our database, {state}: {len(want)} meetings, {n_races} races matched ({missing_races} not in our DB), {n_entries} entries\n")
print(f"Past events: {contam[0]} entries; ours hold a past event dated on/after the race for {contam[1]}, the archive for {contam[2]}; ours hold {contam[3]:+d} more past events in total. Examples: {contam_ex}\n")
print("Our copy -> Dave's point-in-time copy. Fields where 1%+ of values differ, most-changed first.\n")
print("| field | compared | differ | % | mean abs diff when different | examples (our -> archive) |\n|---|---|---|---|---|---|")
rows = sorted(((k, v) for k, v in stats.items() if v[0] >= 20 and v[1] / v[0] >= 0.01), key=lambda kv: -kv[1][1] / kv[1][0])
for k, (n, nd, sd, ex) in rows[:120]:
    print(f"| {k} | {n} | {nd} | {nd/n*100:.0f}% | {sd/nd:.3g} | {'; '.join(ex)} |")
print(f"\n{sum(1 for v in stats.values() if v[0] >= 20 and v[1] == 0)} fields identical everywhere (20+ values compared).\n")
print("## Fields in the archive but not in our copy (top 40)\n"); [print(f"- {k}: {n}") for k, n in only_arch.most_common(40)]
print("\n## Fields in our copy but not in the archive (top 40)\n"); [print(f"- {k}: {n}") for k, n in only_db.most_common(40)]
