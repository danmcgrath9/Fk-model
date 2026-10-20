"""Pull the NBA's official injury reports for one month of game days.

Source: the league's own report, filed by every team (status by 5pm local the day before a
game, 1pm on the second night of a back-to-back) and archived by the NBA as PDFs at
ak-static.cms.nba.com, hourly until 19 Dec 2025 and every 15 minutes since. Read with the
free `nbainjuries` package (github.com/mxufc29/nbainjuries), which needs Java. No API key.

Runs in the `nba injuries pull` GitHub workflow (the cloud box cannot reach nba.com), one
job per month, and writes nba/injuries/raw/YYYY-MM.csv: every row of every report fetched,
with `report_time` (US Eastern, the time in the report's own file name).

Snapshots per game day D, all US Eastern: 5pm on D-1 (the filing deadline), then 11am,
1pm, 3pm, 5pm and 7pm on D. Together they show what was known at any point before tip-off,
which is what a projection made at a line's open is allowed to use. A report that does not
exist (the NBA skips some hours) is logged, not guessed.

    python nba/pull_injuries.py 2025-01
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "injuries" / "raw"
SAME_DAY_HOURS = [11, 13, 15, 17, 19]
PAUSE = 1.0   # seconds between reports: the NBA's server, not ours


def snapshot_times(month: str) -> list[datetime]:
    days = json.loads((HERE / "injuries" / "game_days.json").read_text())["days"]
    game_days = sorted(d for v in days.values() for d in v if d.startswith(month))
    times = set()
    for d in game_days:
        day = datetime.strptime(d, "%Y-%m-%d")
        times.add((day - timedelta(days=1)).replace(hour=17))
        times.update(day.replace(hour=h) for h in SAME_DAY_HOURS)
    return sorted(times)


def main(month: str, fetch=None) -> int:
    if fetch is None:
        from nbainjuries import injury

        def fetch(ts):
            return injury.get_reportdata(ts, return_df=True)

    OUT.mkdir(parents=True, exist_ok=True)
    frames, log = [], []
    for ts in snapshot_times(month):
        try:
            df = fetch(ts)
            df = df.assign(report_time=ts.strftime("%Y-%m-%d %H:%M"))
            frames.append(df)
            log.append((ts, "ok", len(df)))
        except Exception as exc:                       # a missing hour is normal; log it
            log.append((ts, f"missing: {type(exc).__name__}", 0))
        time.sleep(PAUSE)

    got = sum(1 for _, s, _ in log if s == "ok")
    print(f"{month}: {got} of {len(log)} reports read, {sum(n for *_, n in log):,} rows")
    pd.DataFrame(log, columns=["report_time", "status", "rows"]).to_csv(OUT / f"{month}_log.csv", index=False)
    if frames:
        pd.concat(frames, ignore_index=True).to_csv(OUT / f"{month}.csv", index=False)
    return 0 if got else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
