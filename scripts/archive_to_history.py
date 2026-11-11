"""Form King's historical archive into history day files, the same files the export, the fit and the trials read
(11 Nov 2026, founder: "I want the training for other states as well ... I want the same model", and "I'm buying the
history ... that history saves us doing a full pull").

    python scripts/archive_to_history.py ARCHIVE_DIR [--out history_states] [--states NSW,QLD,SA,WA,TAS,ACT,NT]
                                         [--from 2025-07-01] [--to 2026-11-10]

Each race goes through fk.history.race_bundle, the transform the back-test pull uses, so a race from the archive is
read exactly like one we pulled ourselves; the race's going, number and lws are taken from the meeting summary where
the race form lacks them (as scripts/archive_export_states.py does). Each bundle keeps its own meeting's state.

The other states go to their OWN folder (history_states, release "history-states") and Victoria's files are never
touched: the live Victorian export reads ./history only, so nothing about tomorrow's Victorian prices can change
until an all-states model is tested and the founder says so. --states VIC --out history_arch_vic writes Dave's
Victorian races to a third folder, for comparing his point-in-time copy with ours.

The archive layout (scripts/archive_inspect.py): index.json lists days, each with its meetings (meetingId, state,
raceIds); meetings/<id>/summary.json is Get Meeting Summary, speedmaps.json Get Meeting Speedmaps and
races/<raceId>.json Get Race Form."""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fk import history as H  # noqa: E402
from fk import states as ST  # noqa: E402


def load(path: str):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("--out", default="history_states")
    ap.add_argument("--states", default="NSW,QLD,SA,WA,TAS,ACT,NT")
    ap.add_argument("--from", dest="date_from", default="0000-00-00")
    ap.add_argument("--to", dest="date_to", default="9999-99-99")
    a = ap.parse_args()
    want = ST.parse(a.states)
    root = a.archive
    idx = load(os.path.join(root, "index.json"))
    by_day: dict[str, list[dict]] = collections.defaultdict(list)
    tally = collections.defaultdict(collections.Counter)
    for d in idx["days"]:
        for m in d["meetings"]:
            st = str(m.get("state") or "").upper()
            if not ST.matches(st, want):
                continue
            md = os.path.join(root, "meetings", m["meetingId"])
            sp = os.path.join(md, "summary.json")
            if not os.path.exists(sp):
                print(f"NO SUMMARY {st} {m['meetingId']}", flush=True); tally[st]["meetings without a summary"] += 1
                continue
            meeting = load(sp)
            smp = os.path.join(md, "speedmaps.json")
            sms = load(smp) if os.path.exists(smp) else []
            sm_by = {str(s.get("raceId")): s for s in (sms if isinstance(sms, list) else [sms]) if isinstance(s, dict)}
            races_meta = {str(r.get("raceId")): r for r in meeting.get("races", []) or []}
            tally[st]["meetings"] += 1
            for rid in m.get("raceIds", []):
                rp = os.path.join(md, "races", f"{rid}.json")
                if not os.path.exists(rp):
                    tally[st]["races without a form file"] += 1
                    continue
                A = load(rp)
                try:
                    b = H.race_bundle(meeting, A, sm_by.get(str(rid)))
                except Exception as e:  # noqa: BLE001 - a race the transform cannot read is named, not skipped silently
                    print(f"SKIP {st} {m['meetingId']} {rid}: {type(e).__name__}: {e}", flush=True)
                    tally[st]["races the transform could not read"] += 1
                    continue
                day = str(b.get("date") or "")[:10]
                if not (a.date_from <= day <= a.date_to):
                    continue
                rm = races_meta.get(str(rid), {})
                g = " ".join(str(x) for x in (rm.get("going") or A.get("going"), rm.get("goingNumber") or A.get("goingNumber")) if x)
                b["going"] = g or None
                b["race_number"] = rm.get("number") or A.get("number")
                if b.get("lws") is None and rm.get("lws") is not None:
                    try:
                        b["lws"] = float(rm["lws"])
                    except (TypeError, ValueError):
                        pass
                if not b.get("state"):
                    b["state"] = st          # the index's state, if the summary did not carry one
                b["source"] = "archive"      # a race from Dave's archive, not one we pulled
                by_day[day].append(b)
                tally[st]["races"] += 1
                tally[st]["resulted"] += int(H.is_resulted(b))
                tally[st]["runners"] += len(b.get("entries") or [])
    out = Path(a.out)
    for day, bundles in sorted(by_day.items()):
        H.write_day(out, day, bundles)
    print(f"\nwrote {len(by_day)} day files to {out} ({sum(len(v) for v in by_day.values())} races)")
    print("| state | meetings | races | resulted | runners | other |\n|---|---|---|---|---|---|")
    for st in sorted(tally):
        c = tally[st]
        other = ", ".join(f"{k} {v}" for k, v in c.items() if k not in ("meetings", "races", "resulted", "runners"))
        print(f"| {st} | {c['meetings']} | {c['races']} | {c['resulted']} | {c['runners']} | {other} |")
    if by_day:
        print(f"days {min(by_day)} to {max(by_day)}")


if __name__ == "__main__":
    main()
