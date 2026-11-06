"""Topaz's track codes and names, from the bulk runs (6 Nov 2026: Tests 34 and 35 name tracks by code).

    python research/greyhound/topaz_track_codes.py DIR LABEL      (counts only: code, name, races, first and last day)
"""
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path


def main(d, label):
    seen = defaultdict(lambda: [set(), set(), "9999", "0000"])
    for f in sorted(Path(d).glob("runs_VIC_*.json.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for r in json.load(fh):
                k = (str(r.get("trackCode")), str(r.get("trackName")))
                s = seen[k]
                s[0].add(r.get("raceId"))
                day = str(r.get("meetingDate"))[:10]
                s[2], s[3] = min(s[2], day), max(s[3], day)
    print(f"# {label}\n\n| code | name | races | first day | last day |\n|---|---|---|---|---|")
    for (code, name), s in sorted(seen.items(), key=lambda kv: -len(kv[1][0])):
        print(f"| {code} | {name} | {len(s[0]):,} | {s[2]} | {s[3]} |")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "track codes")
