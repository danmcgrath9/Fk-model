"""Read-only probe: does TAB's public racing data carry scratchings and fixed-odds deductions?
python scripts/tab_probe.py --date 2026-10-01 --venue Warrnambool --race 5
Prints the meeting list match, then every key path in the race JSON that mentions scratch or deduct."""
from __future__ import annotations
import argparse, json, sys
import requests

BASE = "https://api.beta.tab.com.au/v1/tab-info-service/racing"


def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o[:40]):
            yield from walk(v, f"{path}[{i}]")
    else:
        yield path, o


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--date"); ap.add_argument("--venue"); ap.add_argument("--race", type=int)
    ap.add_argument("--jurisdiction", default="VIC"); a = ap.parse_args()
    r = requests.get(f"{BASE}/dates/{a.date}/meetings", params={"jurisdiction": a.jurisdiction}, timeout=30)
    print("meetings HTTP", r.status_code)
    if r.status_code != 200:
        print(r.text[:300]); sys.exit(1)
    meets = [m for m in r.json().get("meetings", []) if a.venue.lower() in str(m.get("meetingName", "")).lower() and m.get("raceType") == "R"]
    print("matched meetings:", [(m.get("meetingName"), m.get("venueMnemonic"), m.get("raceType")) for m in meets])
    if not meets:
        sys.exit(1)
    m = meets[0]
    r = requests.get(f"{BASE}/dates/{a.date}/meetings/R/{m['venueMnemonic']}/races/{a.race}", params={"jurisdiction": a.jurisdiction}, timeout=30)
    print("race HTTP", r.status_code)
    if r.status_code != 200:
        print(r.text[:300]); sys.exit(1)
    d = r.json()
    print("top-level keys:", list(d)[:40])
    runners = d.get("runners", [])
    if runners:
        print("runner keys:", list(runners[0]))
        print("first runner fixedOdds:", json.dumps(runners[0].get("fixedOdds"), default=str)[:600])
    for p, v in walk(d):
        if "scratch" in p.lower() or "deduct" in p.lower():
            print(p, "=", v)


if __name__ == "__main__":
    main()
