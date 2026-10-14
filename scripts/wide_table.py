"""Everything Form King sends that the model does not read yet, per stored runner, for feature trials (15 Oct 2026,
founder: "what else aren't we testing"). Read-only, no Form King calls.

    python scripts/wide_table.py [--state VIC] [--history history]

One line per runner: race_id <TAB> horse_id <TAB> JSON
  {"foal": foal date ms, "home": home track, "acc": number of other acceptances,
   "past": [[raceId, date, gear worn ("|"-joined), gear changes ("|"-joined), first fluc, last fluc, comment flags,
             comment summary (after the #), pos1200m, spellDays, raceType, nightMeeting], ...]}  newest first, up to 10.
Comment flags come from each past run's videoComment (a race-review comment the API docs do not list): S slow start,
B held up / checked / blocked, W wide / no cover, K keen / over-raced, E eased / pulled up / bled / lost a plate,
F ran on / strong late, L led.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import load_settings  # noqa: E402
from fk import fields as F  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FLAGS = {
    "S": r"slow (out|away|to begin|start)|bit slow|missed the start|dwelt|jumped (awkward|poor|slow|out|in|badly)|began (awkward|poor|slow)|blundered",
    "B": r"held up|no clear run|blocked|checked|steadied|crowded|inconvenienced|tightened|couldn'?t get (out|clear)|boxed|shuffled|hampered|bumped",
    "W": r"\b(3|4|5|three|four|five) wide|no cover|wide (throughout|trip|no cover|on turn|home turn)|raced wide|caught wide",
    "K": r"\bkeen|over-?rac|pulled hard|fought for (its|his|her) head|hard to hold|over-?raced",
    "E": r"eased|pulled up|bled|lost a plate|lame|vet|broke down|eased down",
    "F": r"ran on|strong late|flashing|closing|late (run|charge|burst)|finished (off )?(well|strongly|fast)|good late",
    "L": r"\bled\b|straight to the front|led all|set the pace",
}
RX = {k: re.compile(v, re.I) for k, v in FLAGS.items()}


def flags(txt: str) -> str:
    return "".join(k for k, rx in RX.items() if rx.search(txt or ""))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--history", default=str(ROOT / "history"))
    a = ap.parse_args()
    from fk import history as H
    from fk.db import Db
    db = Db(load_settings().database_url)
    rows = list(db.resulted_races(a.state))
    in_db = {r["race_id"] for r in rows}
    rows += list(H.resulted_races(Path(a.history), a.state, skip=in_db))
    n = with_comment = past_n = 0
    for row in rows:
        rdate = str(row.get("date") or "")[:10]
        for e in row.get("entries") or []:
            h = e.get("horse") or {}
            acc = e.get("acceptances")
            out = {"foal": h.get("foalDate"), "home": e.get("homeTrack"),
                   "acc": len(acc) if isinstance(acc, list) else None, "past": []}
            runs = []
            for p in F.entry_past_events(e):
                if str(p.get("scratched")).lower() == "true" or p.get("scratched") is True:
                    continue
                d = F.past_event_date(p)
                if d and d < rdate:
                    runs.append((d, p))
            runs.sort(key=lambda t: t[0], reverse=True)
            for d, p in runs[:10]:
                g = [x for x in (p.get("gear") or []) if isinstance(x, dict)]
                fl = [x.get("price") for x in (p.get("flucs") or []) if isinstance(x, dict) and x.get("price")]
                c = str(p.get("videoComment") or "")
                past_n += 1; with_comment += bool(c)
                out["past"].append([p.get("raceId"), d, "|".join(str(x.get("gear")) for x in g if x.get("on")),
                                    "|".join(f"{x.get('gear')}:{x.get('change')}" for x in g if x.get("change") not in (None, "", "STAYING_ON")),
                                    fl[0] if fl else None, fl[-1] if fl else None, flags(c),
                                    c.split("#", 1)[1].strip()[:40] if "#" in c else "",
                                    p.get("pos1200m"), p.get("spellDays"), p.get("raceType"), p.get("nightMeeting")])
            print(f"{row['race_id']}\t{F.horse_id(e)}\t{json.dumps(out, separators=(',', ':'))}")
            n += 1
    print(f"# {n} runners, {past_n} past runs, {with_comment} with a video comment")


if __name__ == "__main__":
    main()
