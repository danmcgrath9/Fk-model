"""Past racing kept as compressed files instead of database rows.

The database filled at about 850 MB of a 1 GB disk, and a past race never changes, so
the back-test's history does not need to live there. Each day pulled for the back-test
becomes one gzip file of JSON lines, one line per race, holding exactly what the fit
reads (the same shape Db.resulted_races returns): the race's date, track, state and
distance, its lws, every runner's entry as Form King sent it (form, odds and result),
and the speedmap.

The files are kept as assets on the Fk-model repo's "history" release, which costs
nothing and has no total size cap. The fit reads the database and the files together,
and a race held in both is read once, from the database.
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any, Iterable, Iterator

from . import fields as F

SUFFIX = ".jsonl.gz"


def speedmap_runners(sm: dict) -> list[dict]:
    """The speedmap's runners in predicted early order: the list fk.speedmaps.runners
    holds, so the fit reads the same thing from a file as from the database."""
    return [dict(horse_id=F.horse_id(e), name=F.horse_name(e), number=F.entry_number(e), barrier=F.entry_barrier(e),
                 predicted_position=rank, early_speed=F.speedmap_early_speed(e), pir=F.speedmap_pir(e),
                 median_vs_benchmark=F.speedmap_median_vs_benchmark(e))
            for e, rank in F.speedmap_predicted_order(F.speedmap_entries(sm))]


def _num(v: Any) -> float | None:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def race_bundle(meeting: dict, race_payload: dict, speedmap: dict | None) -> dict:
    """One race as the fit reads it. `race_payload` is Get Race Form's response;
    `speedmap` is that race's entry in Get Meeting Speedmaps, or None."""
    return {
        "race_id": F.race_id(race_payload),
        "date": F.meeting_date(meeting),
        "track": F.meeting_track(meeting),
        "state": F.meeting_state(meeting),
        "distance_m": F.race_distance(race_payload),
        # fk.races reads (raw->>'lws')::numeric, the top-level field of the same payload
        "lws": _num(race_payload.get("lws")),
        "entries": list(F.race_entries(race_payload)),
        "speedmap": speedmap_runners(speedmap) if speedmap else None,
        # fk.speedmaps reads raw->'expectedTempo'
        "tempo": speedmap.get("expectedTempo") if speedmap else None,
    }


def is_resulted(bundle: dict) -> bool:
    """The same test Db.resulted_races applies: at least one runner carries its result."""
    return any(isinstance(e, dict) and "horseResult" in e for e in bundle.get("entries") or [])


def day_path(directory: Path, day: str) -> Path:
    return Path(directory) / f"{day}{SUFFIX}"


def read_file(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_day(directory: Path, day: str, bundles: Iterable[dict]) -> Path:
    """Write (or add to) one day's file. Races already in the file are kept and a race
    pulled again replaces its old line, so a day topped up later loses nothing."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = day_path(directory, day)
    by_id: dict[str, dict] = {}
    if path.exists():
        for b in read_file(path):
            by_id[b["race_id"]] = b
    for b in bundles:
        by_id[b["race_id"]] = b
    tmp = path.with_suffix(path.suffix + ".tmp")
    # mtime=0 keeps the bytes identical for identical content, so a re-upload of an
    # unchanged day is visibly unchanged
    with open(tmp, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as gz:
        for rid in sorted(by_id):
            gz.write((json.dumps(by_id[rid], separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8"))
    tmp.replace(path)
    return path


def files(directory: Path | None) -> list[Path]:
    if not directory or not Path(directory).is_dir():
        return []
    return sorted(Path(directory).glob(f"*{SUFFIX}"))


def held_race_ids(directory: Path | None) -> set[str]:
    return {b["race_id"] for p in files(directory) for b in read_file(p)}


def resulted_races(directory: Path | None, state: str | None = "VIC", skip: set[str] | None = None) -> Iterator[dict]:
    """Every resulted race in the files, oldest day first, for the given state (None =
    every state), leaving out the race ids in `skip` (the ones the database already holds)."""
    skip = skip or set()
    for p in files(directory):
        for b in read_file(p):
            if b["race_id"] in skip or not is_resulted(b):
                continue
            if state is not None and b.get("state") != state:
                continue
            yield b
