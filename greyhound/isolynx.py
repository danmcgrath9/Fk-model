"""Isolynx tracking data from Topaz: every tracked run of every dog that has raced at a tracked track, one call per
dog (4 Nov 2026, founder: "BUILD THE BEST MODEL IN THE WORLD"; MODELS_RESEARCH.md item 3).

    python -m greyhound.isolynx pull  --runs DIR --out DIR [--since 2022-01-01] [--workers 8] [--per-minute 72]
                                      [--max-minutes 280]
    python -m greyhound.isolynx table --out DIR          # prints the flattened table's shape and fill rates
    python -m greyhound.isolynx probe --runs DIR [--since] # one tracked race: which Isolynx endpoints the key may call

GET /api/isolynx/dog/{dogId}/splits returns, for one dog, every race the tracking system timed
(IsoLynxSplitsRunnerWithRaceInfo: race id, date, venue, distance, box, place, result time, average and maximum
speed, average/min/max distance to the rail, the jump split, and 50-metre splits from the start, to the finish, and
at the track marks, each with elapsed time, speed, rail distance and position). Tracked tracks (GRV's Race Data page):
The Meadows, Sandown Park, Healesville, Traralgon (and Cranbourne when it returns).

The pull is resumable: dogs are taken in groups of GROUP, one gzipped JSON per group, written whole or not at all; a
group file that exists is never pulled again. Dogs are those with a run at a tracked track since --since in the
cached bulk runs. `table()` flattens the files to one row per (race, dog) for the ratings engine.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from greyhound.topaz import TopazClient, TopazError, TopazForbidden, TopazNoAccess

TRACKED = ("MEADOWS", "SANDOWN", "HEALESVILLE", "TRARALGON", "CRANBOURNE")
GROUP = 200


def tracked_runs(runs_dir: Path, since: str):
    """(raceId, dogId, meetingDate) of every run at a tracked track on or after `since`, from the pull's
    runs_*.json.gz, in file order."""
    for f in sorted(Path(runs_dir).glob("runs_*_*.json.gz")):
        ym = f.stem.split("_")[-1].replace(".json", "")
        if ym < since[:7]:
            continue
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for r in json.load(fh):
                name = str(r.get("trackName") or "").upper()
                day = str(r.get("meetingDate") or "")[:10]
                if any(t in name for t in TRACKED) and day >= since and r.get("dogId") is not None:
                    yield r.get("raceId"), int(r["dogId"]), day


def tracked_dogs(runs_dir: Path, since: str) -> list[int]:
    """Dog ids with at least one run at a tracked track on or after `since`."""
    return sorted({dog for _, dog, _ in tracked_runs(runs_dir, since)})


def probe(client: TopazClient, runs_dir: Path, since: str) -> int:
    """One tracked run, three calls: the per-race splits and positions the Topaz-api wrapper documents
    (/isolynx/{raceId}/splits, /positions) and the per-dog splits this pull was built on. Prints, per endpoint,
    whether the key is allowed it and the SHAPE of the answer (type, count, the first element's field names);
    never a value. 4 Nov 2026: the per-dog pull answered 401 on every one of 14,129 dogs."""
    latest = None
    for race, dog, day in tracked_runs(runs_dir, since):
        if race is not None and (latest is None or day > latest[2]):
            latest = (race, dog, day)
    if latest is None:
        print(f"no run at a tracked track since {since} in {runs_dir}")
        return 2
    race, dog, day = latest
    print(f"probing race {race} ({day}), dog {dog}")
    ok = 0
    for path in (f"isolynx/{race}/splits", f"isolynx/{race}/positions", f"isolynx/dog/{dog}/splits"):
        try:
            ans = client._get(path)
        except TopazForbidden as e:
            print(f"  {path}: NOT ALLOWED ({str(e).split(',')[0]})")
            continue
        except TopazNoAccess as e:
            print(f"  {path}: no access ({e})")
            continue
        except TopazError as e:
            print(f"  {path}: failed ({e})")
            continue
        ok += 1
        if isinstance(ans, list):
            first = next((x for x in ans if isinstance(x, dict)), None)
            print(f"  {path}: ok, a list of {len(ans)}; fields: {', '.join(sorted(first)) if first else 'none'}")
        elif isinstance(ans, dict):
            print(f"  {path}: ok, an object; fields: {', '.join(sorted(ans))}")
        else:
            print(f"  {path}: ok, {type(ans).__name__}")
    return 0 if ok else 1


def group_file(out: Path, i: int) -> Path:
    return out / f"isolynx_dogs_{i:04d}.json.gz"


def pull(client: TopazClient, dogs: list[int], out: Path, workers: int, max_minutes: float) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + max_minutes * 60
    groups = [dogs[i:i + GROUP] for i in range(0, len(dogs), GROUP)]
    report = {"groups": len(groups), "held": 0, "pulled": 0, "left": 0, "dogs_with_data": 0, "runs": 0, "failed": 0}

    def one(dog):
        try:
            rows = client._get(f"isolynx/dog/{dog}/splits")
            return dog, (rows if isinstance(rows, list) else []), None
        except TopazNoAccess:
            return dog, [], None
        except TopazForbidden:
            raise                        # the key is not allowed this endpoint: stop, do not try 14,000 more dogs
        except TopazError as e:
            return dog, None, str(e)

    for gi, grp in enumerate(groups):
        path = group_file(out, gi)
        if path.exists():
            report["held"] += 1
            continue
        if time.monotonic() > deadline:
            report["left"] += 1
            continue
        with ThreadPoolExecutor(max_workers=workers) as ex:
            got = list(ex.map(one, grp))
        if any(err for _, _, err in got):
            report["failed"] += 1
            print(f"group {gi}: {sum(1 for _, _, e in got if e)} dogs failed, e.g. {next(e for _, _, e in got if e)[:120]}; "
                  "not written, next run retries it")
            continue
        payload = [{"dogId": d, "runs": rows} for d, rows, _ in got]
        tmp = path.with_suffix(".part")
        with gzip.open(tmp, "wt", encoding="utf-8") as fh:
            json.dump(payload, fh, separators=(",", ":"))
        os.replace(tmp, path)
        report["pulled"] += 1
        report["dogs_with_data"] += sum(1 for d, rows, _ in got if rows)
        report["runs"] += sum(len(rows) for _, rows, _ in got if rows)
    return report


def _by_distance(splits, dist):
    for s in splits or []:
        if isinstance(s, dict) and s.get("splitDistance") == dist:
            return s
    return None


def flatten(run: dict) -> dict:
    """One tracked run to a flat row (times in seconds, speeds in m/s as Topaz gives them, rail in metres)."""
    j = run.get("jumpSplit") or {}
    start, finish, marks = run.get("runnerSplitsFromStart50") or [], run.get("runnerSplitsToFinish50") or [], \
        run.get("runnerSplitsTrackMarks") or []
    row = {"race_id": run.get("raceId"), "dog": run.get("dogId"), "date": str(run.get("raceDate") or "")[:10],
           "venue": run.get("venueCode"), "distance": run.get("raceDistance"), "box": run.get("boxNumber"),
           "place": run.get("place"), "time": run.get("resultTime"), "avg_speed": run.get("averageSpeed"),
           "max_speed": run.get("maxSpeed"), "avg_rail": run.get("averageToRail"), "min_rail": run.get("minToRail"),
           "max_rail": run.get("maxToRail"), "jump_time": j.get("elapsedTime"), "jump_speed": j.get("splitSpeed"),
           "jump_rail": j.get("averageToRail"), "jump_pos": j.get("positionInRunning")}
    for d in (50, 100, 200, 300, 400, 500):
        s = _by_distance(start, d)
        row[f"t{d}"] = s.get("elapsedTime") if s else None
        row[f"v{d}"] = s.get("splitSpeed") if s else None
        row[f"pos{d}"] = s.get("positionInRunning") if s else None
    # the run home: the last two 50 m splits to the finish, summed
    fin = [s for s in finish if isinstance(s, dict) and s.get("deltaTime") is not None]
    fin = sorted(fin, key=lambda s: -(s.get("splitDistance") or 0))    # distance TO the finish: last = the finish
    row["last100"] = sum(s["deltaTime"] for s in fin[-2:]) if len(fin) >= 2 else None
    row["last50"] = fin[-1]["deltaTime"] if fin else None
    for k, s in enumerate(marks[:3]):
        if isinstance(s, dict):
            row[f"mark{k + 1}_time"] = s.get("elapsedTime")
            row[f"mark{k + 1}_pos"] = s.get("positionInRunning")
    return row


def table(out: Path):
    import pandas as pd
    rows = []
    for f in sorted(Path(out).glob("isolynx_dogs_*.json.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for d in json.load(fh):
                for run in d.get("runs") or []:
                    if isinstance(run, dict):
                        rows.append(flatten(run))
    t = pd.DataFrame(rows)
    if len(t):
        t["date"] = pd.to_datetime(t.date, errors="coerce")
        t = t.drop_duplicates(["race_id", "dog"])
    return t


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("pull")
    p.add_argument("--runs", type=Path, required=True); p.add_argument("--out", type=Path, required=True)
    p.add_argument("--since", default="2022-01-01"); p.add_argument("--workers", type=int, default=8)
    p.add_argument("--per-minute", type=float, default=72); p.add_argument("--max-minutes", type=float, default=280)
    t = sp.add_parser("table"); t.add_argument("--out", type=Path, required=True)
    pr = sp.add_parser("probe"); pr.add_argument("--runs", type=Path, required=True); pr.add_argument("--since", default="2022-01-01")
    a = ap.parse_args(argv)
    if a.cmd == "table":
        df = table(a.out)
        print(f"{len(df):,} tracked runs, {df.dog.nunique() if len(df) else 0:,} dogs, "
              f"{df.date.min() if len(df) else ''} to {df.date.max() if len(df) else ''}")
        if len(df):
            for c in df.columns:
                print(f"  {c:<14} filled on {df[c].notna().mean():.0%}")
        return 0
    if os.environ.get("TOPAZ_TERMS_READ", "").strip().lower() != "yes":
        print("Refused: TOPAZ_TERMS_READ is not 'yes'")
        return 2
    if a.cmd == "probe":
        try:
            return probe(TopazClient(pause=1.0), a.runs, a.since)
        except TopazError as e:
            print(f"Topaz refused or failed: {e}")
            return 1
    dogs = tracked_dogs(a.runs, a.since)
    print(f"{len(dogs):,} dogs raced at a tracked track since {a.since}: {-(-len(dogs) // GROUP)} groups of {GROUP}")
    try:
        client = TopazClient(max_per_minute=a.per_minute)
        rep = pull(client, dogs, a.out, a.workers, a.max_minutes)
    except TopazError as e:
        print(f"Topaz refused or failed: {e}")
        return 1
    print(f"{client.calls} calls; groups held {rep['held']}, pulled {rep['pulled']}, failed {rep['failed']}, "
          f"{rep['left']} left for the next run; this run: {rep['dogs_with_data']:,} dogs with tracking data, "
          f"{rep['runs']:,} tracked runs")
    return 0 if rep["left"] == 0 and rep["failed"] == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
