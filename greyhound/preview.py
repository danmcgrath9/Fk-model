"""Is GRV's per-runner `comment` written BEFORE the race, and is it changed after? (4 Nov 2026: the field's commonest
words are DANGER, SAFE, NEEDS, LUCK, DRAW, PREFER, THREAT, LEAD: a form-guide preview, not a stewards' report.)

    python -m greyhound.preview snapshot [--dir D] [--max-races N]   # today's remaining VIC races, before they run
    python -m greyhound.preview compare YYYY-MM-DD [--dir D]         # the next day: the same runs from the bulk feed

snapshot: GET /api/race/upcoming (VIC, from now) and, per race, /api/race/{id}/runs/form; stores per run the SHA-1
of the comment, its length, GRV's rating, isBestBet and the pre-race startPrice, plus the race's analystComment hash,
tips and suggested bet, in preview_<date>.json under --dir (the workflow keeps it in the Actions cache, never in
git). compare: pulls the bulk runs for that day and reports, run by run, whether the comment, rating, isBestBet and
startPrice came back the same, changed, or empty. Counts only are printed; no comment text ever is.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from greyhound.topaz import TopazClient, TopazError

SYDNEY = timezone(timedelta(hours=11))      # AEDT in November; the probe only needs the civil date and hour


def _h(text) -> str:
    t = "" if text is None else str(text).strip()
    return hashlib.sha1(t.encode("utf-8")).hexdigest()[:10] if t else ""


def snapshot(client: TopazClient, out: Path, max_races: int, day: str | None = None) -> int:
    """`day` (YYYY-MM-DD): that day's races instead of the rest of today, e.g. tomorrow's the evening before, which
    is the test that matters: the TAB opens on race morning, so a preview is usable only if it is out the day before
    (founder, 4 Nov 2026: "we want to bet before the preview and odds come out")."""
    now = datetime.now(SYDNEY)
    frm = f"{day} 00:00" if day else now.strftime("%Y-%m-%d %H:%M")
    races = client._get("race/upcoming", params={"from": frm}) or []
    races = [r for r in races if isinstance(r, dict)]
    print(f"{len(races)} VIC races to run from {frm} Sydney, asked at {now:%Y-%m-%d %H:%M} Sydney")
    rows, race_rows = [], []
    for r in races[:max_races]:
        rid = r.get("raceId")
        runs = client._get(f"race/{rid}/runs/form") or []
        race_rows.append({"raceId": rid, "startTime": r.get("startTime"), "analystComment": _h(r.get("analystComment")),
                          "tips": [r.get(f"tip{i}") for i in range(1, 5)], "suggestedBet": r.get("suggestedBet"),
                          "resultEntered": r.get("isRaceResultEntered")})
        for u in runs:
            if not isinstance(u, dict):
                continue
            rows.append({"runId": u.get("runId"), "raceId": rid, "dogId": u.get("dogId"), "comment": _h(u.get("comment")),
                         "comment_len": len(str(u.get("comment") or "").strip()), "rating": u.get("rating"),
                         "isBestBet": u.get("isBestBet"), "startPrice": u.get("startPrice"),
                         "startingPrice": u.get("startingPrice"), "scratched": u.get("scratched")})
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"preview_{day or now.strftime('%Y-%m-%d')}.json"
    path.write_text(json.dumps({"taken": now.isoformat(), "races": race_rows, "runs": rows}))
    n = len(rows)
    print(f"snapshot of {len(race_rows)} races, {n} runners -> {path.name}")
    if n:
        print(f"  comment filled on {sum(1 for x in rows if x['comment'])}/{n}; rating on "
              f"{sum(1 for x in rows if x['rating'] not in (None, ''))}/{n}; isBestBet true on "
              f"{sum(1 for x in rows if x['isBestBet'])}/{n}; startPrice filled on "
              f"{sum(1 for x in rows if x['startPrice'] not in (None, '', 0))}/{n}; startingPrice filled on "
              f"{sum(1 for x in rows if x['startingPrice'] not in (None, '', 0))}/{n}")
        print(f"  race analystComment filled on {sum(1 for x in race_rows if x['analystComment'])}/{len(race_rows)}; "
              f"tips filled on {sum(1 for x in race_rows if any(x['tips']))}/{len(race_rows)}; results already "
              f"entered on {sum(1 for x in race_rows if x['resultEntered'])}")
    return 0


def compare(client: TopazClient, out: Path, day: str) -> int:
    path = out / f"preview_{day}.json"
    if not path.exists():
        print(f"no snapshot for {day} under {out}")
        return 2
    snap = json.loads(path.read_text())
    before = {x["runId"]: x for x in snap["runs"] if x.get("runId") is not None}
    y, m, d = (int(v) for v in day.split("-"))
    bulk = client.bulk_runs_day("VIC", y, m, d)
    after = {u.get("runId"): u for u in bulk if isinstance(u, dict)}
    both = [k for k in before if k in after]
    print(f"{day}: {len(before)} runners in the pre-race snapshot, {len(after)} in the bulk feed, {len(both)} in both")
    if not both:
        return 0
    c = {"same": 0, "changed": 0, "empty before, filled after": 0, "filled before, empty after": 0, "empty both": 0}
    rt = sp = bb = 0
    for k in both:
        b, a = before[k], after[k]
        ha = _h(a.get("comment"))
        if not b["comment"] and not ha:
            c["empty both"] += 1
        elif not b["comment"]:
            c["empty before, filled after"] += 1
        elif not ha:
            c["filled before, empty after"] += 1
        elif b["comment"] == ha:
            c["same"] += 1
        else:
            c["changed"] += 1
        rt += (b.get("rating") == a.get("rating"))
        sp += (b.get("startPrice") == a.get("startPrice"))
        bb += (bool(b.get("isBestBet")) == bool(a.get("isBestBet")))
    print("  comment: " + ", ".join(f"{k} {v}" for k, v in c.items()))
    print(f"  rating the same {rt}/{len(both)}; isBestBet the same {bb}/{len(both)}; pre-race startPrice equal to "
          f"the bulk startPrice {sp}/{len(both)} (if few, the bulk startPrice is the SP, not the price before the race)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dir", type=Path, default=Path(__file__).resolve().parent / "cache" / "preview")
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("snapshot"); s.add_argument("--max-races", type=int, default=60)
    s.add_argument("--date", default="", help="YYYY-MM-DD: that day's races (tomorrow's, the evening before)")
    c = sp.add_parser("compare"); c.add_argument("day")
    a = ap.parse_args(argv)
    if os.environ.get("TOPAZ_TERMS_READ", "").strip().lower() != "yes":
        print("Refused: TOPAZ_TERMS_READ is not 'yes'")
        return 2
    try:
        client = TopazClient(pause=1.0)
        return snapshot(client, a.dir, a.max_races, a.date or None) if a.cmd == "snapshot" else compare(client, a.dir, a.day)
    except TopazError as e:
        print(f"Topaz refused or failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
