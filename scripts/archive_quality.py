"""Is Dave's archive point-in-time and complete? Checks on the unzipped archive (9 Oct 2026), per state and overall:
past runs dated on/after the race; odds flucs after the scheduled start; avgOpen vs the first fluc; results present
(one winner per race, BSP present); sectional benchmarks whose par was created or frozen after the race (a par built
from later races is post-race information); ratings stamped after the start; lws / exp missing.
python scripts/archive_quality.py ARCHIVE_DIR [STATE]"""
import json, os, sys, collections
root = sys.argv[1]; want_state = sys.argv[2] if len(sys.argv) > 2 else None
idx = json.load(open(os.path.join(root, "index.json")))
C = collections.Counter(); ex = collections.defaultdict(list)
def ms(v):
    try: v = float(v)
    except (TypeError, ValueError): return None
    return v if v > 1e11 else v * 1000   # seconds or ms -> ms
def note(k, s):
    C[k] += 1
    if len(ex[k]) < 4: ex[k].append(s)
for d in idx["days"]:
    for m in d["meetings"]:
        if want_state and m.get("state") != want_state: continue
        C["meetings"] += 1
        for rid in m["raceIds"]:
            fp = os.path.join(root, "meetings", m["meetingId"], "races", f"{rid}.json")
            if not os.path.exists(fp): note("race file missing", rid); continue
            A = json.load(open(fp)); C["races"] += 1
            start = ms(A.get("startTime") or A.get("scheduledStart") or A.get("date"))
            if A.get("lws") is None: note("race lws missing", rid)
            winners = 0; bsp_n = 0; runners = 0
            for e in A.get("entries", []):
                if e.get("scratched"): continue
                runners += 1; C["entries"] += 1
                hr = e.get("horseResult") or {}
                if str(hr.get("finishPosition")) == "1": winners += 1
                if hr.get("betfairStartingPrice"): bsp_n += 1
                r = e.get("ratings") or {}
                if r.get("exp") is None: note("entry exp missing", rid)
                rt = ms(r.get("timestamp"))
                if rt and start and rt > start: note("ratings stamped after the start", f"{rid} +{(rt-start)/6e4:.0f} min")
                o = e.get("odds") or {}; fl = o.get("flucs") or []
                if fl:
                    t_last = max(ms(f.get("time")) or 0 for f in fl)
                    if start and t_last > start + 60000: note("flucs after the scheduled start", f"{rid} +{(t_last-start)/6e4:.0f} min")
                    first = min(fl, key=lambda f: ms(f.get("time")) or 9e15)
                    if o.get("avgOpen") is not None and abs(float(o["avgOpen"]) - float(first.get("price") or 0)) > 1e-6:
                        note("avgOpen != first fluc", f"{rid} {o.get('avgOpen')} vs {first.get('price')}")
                else: note("no flucs", rid)
                for p in e.get("pastEvents") or []:
                    C["past runs"] += 1
                    pd = ms(p.get("date") or p.get("meetingDate"))
                    if pd and start and pd >= start - 12 * 3600 * 1000: note("past run on/after race day", f"{rid} {p.get('raceId')}")
                    b = p.get("benchmark") or {}
                    if b:
                        C["benchmarked past runs"] += 1
                        pc = ms(b.get("parCreationDate")); fz = ms(b.get("freezeDate"))
                        if pc and start and pc > start: note("par created after the race", f"{rid} par {(pc-start)/864e5:+.0f} days")
                        if b.get("frozen") is False or (fz and start and fz > start): note("par not frozen by race time", f"{rid}")
            if winners != 1: note(f"races with {winners} winners", rid)
            if runners and bsp_n == 0: note("races with no BSP", rid)
print(f"# Archive quality{(' ' + want_state) if want_state else ''}\n")
print(f"{C['meetings']} meetings, {C['races']} races, {C['entries']} runners, {C['past runs']} past runs ({C['benchmarked past runs']} benchmarked)\n")
print("| check | count | examples |\n|---|---|---|")
for k in sorted(k for k in C if k not in ("meetings", "races", "entries", "past runs", "benchmarked past runs")):
    print(f"| {k} | {C[k]} | {'; '.join(ex[k])} |")
err = os.path.join(root, "errors.md")
if os.path.exists(err): print(f"\n## errors.md\n```\n{open(err).read()[:4000]}\n```")
lic = os.path.join(root, "license.md")
if os.path.exists(lic): print(f"\n## license.md\n```\n{open(lic).read()[:2000]}\n```")
