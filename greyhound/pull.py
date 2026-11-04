"""Pull Topaz bulk runs, one gzipped JSON file per state and month, resumable.

    python -m greyhound.pull --probe                      # first run with a new key: health + one day's columns
    python -m greyhound.pull --states VIC --from 2020-01  # VIC from Jan 2020 to this month

Refuses to call Topaz at all unless TOPAZ_TERMS_READ=yes: the brief's rule is that a provider's terms are read before
any bulk download, and the terms arrive with the key. The founder sets that repository variable once they are read.

A month already on disk is never pulled again, except the current and previous month (results and late corrections
still land) and any month named in --refresh. Files are written to a temp name and renamed, so a killed run never
leaves a half file that looks complete. The workflow keeps the files on the `topaz-history` release of the private
data repository (GRV's data is personal use), never in git and never on this public repository.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from greyhound.topaz import AUTHORITIES, TopazClient, TopazError

DEFAULT_OUT = Path(__file__).resolve().parent / "cache" / "topaz"
VIC_FIRST = ("VIC",)


def months(start: str, end: str) -> list[tuple[int, int]]:
    """Inclusive list of (year, month) from 'YYYY-MM' to 'YYYY-MM'."""
    y, m = (int(x) for x in start.split("-"))
    ey, em = (int(x) for x in end.split("-"))
    if (y, m) > (ey, em):
        raise ValueError(f"--from {start} is after --to {end}")
    out = []
    while (y, m) <= (ey, em):
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def file_for(out: Path, state: str, y: int, m: int) -> Path:
    return out / f"runs_{state}_{y:04d}-{m:02d}.json.gz"


def still_moving(y: int, m: int, today: date) -> bool:
    """The current and previous month can still change, so they are always pulled again."""
    prev = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
    return (y, m) in ((today.year, today.month), prev)


def write_atomic(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(rows, f, separators=(",", ":"))
    os.replace(tmp, path)


def terms_read() -> bool:
    return os.environ.get("TOPAZ_TERMS_READ", "").strip().lower() == "yes"


def probe(client: TopazClient, day: date) -> int:
    """Health, then one Victorian day's bulk runs: the row count and column names only, never a row's contents."""
    print("health:", "answered" if client.health() is not None else "no answer (404)")
    rows = client.bulk_runs_day("VIC", day.year, day.month, day.day)
    print(f"VIC {day.isoformat()}: {len(rows)} runs")
    if rows:
        cols = sorted({k for r in rows for k in r})
        print(f"{len(cols)} columns:")
        for c in cols:
            filled = sum(1 for r in rows if r.get(c) not in (None, ""))
            print(f"  {c:<40} filled on {filled}/{len(rows)}")
        try:
            mapping_check(rows)
        except Exception as e:                       # noqa: BLE001 - the check informs, it never stops the probe
            print(f"\nmapping check skipped: {type(e).__name__}: {e}")
    return 0


def mapping_check(rows: list[dict]) -> None:
    """The three meanings topaz_to_runs assumes, tested on the probe day. Prints counts only, never a row: the
    winner's raw margin, whether each dog has its own time, whether margins match the time gaps, and race types."""
    import numpy as np
    import pandas as pd
    from greyhound.ratings import SEC_PER_LENGTH, topaz_to_runs
    raw = pd.DataFrame(rows)
    ran = raw[~raw.scratched.fillna(False).astype(bool)]
    won = ran[ran.place == 1]
    print(f"\nmapping check on {raw.raceId.nunique()} races, {len(ran)} runners who ran, {len(raw) - len(ran)} scratched")
    print(f"  winners per race: {won.groupby('raceId').size().value_counts().sort_index().to_dict()}")
    print(f"  winners whose raw resultMargin is 0: {int((won.resultMargin == 0).sum())}/{len(won)}"
          f" (the rest hold their margin over second, and the mapping sets them to 0)")
    times = ran.dropna(subset=["resultTime"]).groupby("raceId").resultTime
    print(f"  races where runners' resultTime differ (each dog's own time): {int((times.nunique() > 1).sum())}/{times.ngroups}")
    runs = topaz_to_runs(raw)
    ok = runs.dropna(subset=["time", "win_time", "margin"])
    ok = ok[ok.finish > 1]
    gap = (ok.time - ok.win_time) / SEC_PER_LENGTH
    if len(ok) > 2:
        r = np.corrcoef(gap, ok.margin)[0, 1]
        print(f"  placegetters 2nd+: margin vs time gap in lengths, r = {r:.3f}, median ratio {np.median(ok.margin / gap.where(gap > 0)):.2f}")
    print(f"  winner's time is the race's fastest: {int((runs[runs.finish == 1].time == runs.groupby('race_id').time.transform('min')[runs.finish == 1]).sum())}/{int((runs.finish == 1).sum())}")
    print(f"  race types: {raw.drop_duplicates('raceId').raceType.value_counts().to_dict()}")
    print(f"  marked as trials by the mapping: {int(runs.drop_duplicates('race_id').is_trial.sum())} races")


def pull(client: TopazClient, states, span, out: Path, refresh: set[str], today: date, max_calls: int) -> list[tuple]:
    """Returns one (state, 'YYYY-MM', rows or None, status) per month considered."""
    report = []
    for state in states:
        for y, m in span:
            ym = f"{y:04d}-{m:02d}"
            path = file_for(out, state, y, m)
            if path.exists() and ym not in refresh and not still_moving(y, m, today):
                report.append((state, ym, None, "held"))
                continue
            if client.calls >= max_calls:
                report.append((state, ym, None, "budget"))
                continue
            rows = client.bulk_runs_month(state, y, m)
            write_atomic(path, rows)
            report.append((state, ym, len(rows), "pulled" if rows else "pulled, empty"))
    return report


def main(argv=None) -> int:
    today = date.today()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--probe", action="store_true", help="health + one day's column list, nothing stored")
    ap.add_argument("--probe-day", default=(today - timedelta(days=7)).isoformat())
    ap.add_argument("--states", default=",".join(VIC_FIRST), help="comma separated, e.g. VIC,NSW,QLD")
    ap.add_argument("--from", dest="start", default="2020-01")
    ap.add_argument("--to", dest="end", default=f"{today.year:04d}-{today.month:02d}")
    ap.add_argument("--refresh", default="", help="months to pull again, comma separated YYYY-MM")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--max-calls", type=int, default=400, help="stop after this many API calls (resume next run)")
    ap.add_argument("--pause", type=float, default=2.0, help="seconds between calls")
    a = ap.parse_args(argv)

    if not terms_read():
        print("Refused: TOPAZ_TERMS_READ is not 'yes'. Read the terms that came with the Topaz key, then set the "
              "repository variable TOPAZ_TERMS_READ=yes (Settings > Secrets and variables > Actions > Variables).")
        return 2
    states = [s.strip().upper() for s in a.states.split(",") if s.strip()]
    bad = [s for s in states if s not in AUTHORITIES]
    if bad:
        print(f"unknown states {bad}; use {', '.join(AUTHORITIES)}")
        return 2
    try:
        client = TopazClient(pause=a.pause)
        if a.probe:
            return probe(client, date.fromisoformat(a.probe_day))
        refresh = {x.strip() for x in a.refresh.split(",") if x.strip()}
        report = pull(client, states, months(a.start, a.end), a.out, refresh, today, a.max_calls)
    except TopazError as e:
        print(f"Topaz refused or failed: {e}")
        return 1

    print(f"| state | month | runs | status |\n|---|---|---|---|")
    for state, ym, n, status in report:
        if status != "held":
            print(f"| {state} | {ym} | {'' if n is None else n} | {status} |")
    held = sum(1 for r in report if r[3] == "held")
    left = sum(1 for r in report if r[3] == "budget")
    print(f"\n{client.calls} calls; {held} months already held; {left} left for the next run (call budget)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
