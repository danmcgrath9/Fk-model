"""Everything a pricing run reads, for every Victorian meeting on the given dates, in one go (12 Nov 2026, founder: "Are
you fucking kidding, the run takes an hour? Thats way to fkn long"). The hour was mostly waiting: three pull runs, then
twelve fk-experiment runs one at a time (about a minute and a half each, almost all of it the runner starting), then
four exports one after another. This does the reading part of all of that inside one runner.

    python scripts/price_inputs.py OUTDIR DATE[,DATE...] [--all]

For each date: meeting_status.py once, then for every Victorian meeting that has no order sheet yet
(data/live_bets/<date>-<track>-betmatic-preopen.csv; --all takes them all): scratchings.py, entry_numbers.py,
race_times.py, fluc_meeting.py and track_forecast.py, each into OUTDIR/<meeting id>/<name>.md, the scripts run side by
side. Then the day's races exported once (export_dataset.py --date, the official going) into
OUTDIR/upcoming-<date>.npz; the pricer cuts each meeting out of it by track. OUTDIR/index.tsv lists the meetings:
date, meeting id, track, sheet prefix, new (1) or already on a sheet (0). DB and history files only: no credits."""
from __future__ import annotations

import concurrent.futures as cf
import os
import re
import subprocess
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent.parent
LIVE = ROOT / "data" / "live_bets"


def prefix(date: str, mid: str) -> str:
    """The order-sheet prefix the live_bets files use: date + the meeting id's track, Sandown's courses as 'sandown'."""
    slug = re.sub(r"-\d{8}$", "", mid)
    slug = re.sub(r"-(hillside|lakeside)$", "", slug)
    return f"{date}-{slug}"


def forecast_name(track: str, mid: str) -> str:
    """The name track_forecast.py knows the course by (its COORDS keys are lower-case track names)."""
    src = (ROOT / "scripts" / "track_forecast.py").read_text()
    keys = set(re.findall(r'"([a-z ]+)": \(', src))
    slug = re.sub(r"-\d{8}$", "", mid).replace("-", " ")
    for k in (track.lower(), slug, re.sub(r" (hillside|lakeside|park)$", "", slug), slug.split(" ")[0]):
        if k in keys:
            return k
    return ""


def run(args: list[str], out: Path, timeout: int = 600) -> str:
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        p = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        out.write_text(p.stdout + (("\n" + p.stderr) if p.returncode else ""))
        return f"{'ok ' if p.returncode == 0 else 'FAILED'} {' '.join(args)}"
    except subprocess.TimeoutExpired:
        out.write_text(f"TIMED OUT after {timeout}s\n")
        return f"TIMED OUT {' '.join(args)}"


def main() -> None:
    outdir = Path(sys.argv[1]); dates = sys.argv[2].split(","); take_all = "--all" in sys.argv[3:]
    outdir.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
        meets = c.execute("""select m.meeting_date::text, m.meeting_id, m.track, count(r.race_id)
                             from fk.meetings m left join fk.races r using (meeting_id)
                             where m.state = 'VIC' and m.meeting_date = any(%s::date[])
                             group by 1, 2, 3 order by 1, 2""", (dates,)).fetchall()
    rows, jobs = [], []
    for d, mid, track, nr in meets:
        p = prefix(d, mid)
        new = take_all or not (LIVE / f"{p}-betmatic-preopen.csv").exists()
        rows.append((d, mid, track, p, int(new), nr))
        if not new or not nr:
            continue
        md = outdir / mid
        jobs += [(["scripts/scratchings.py", mid], md / "scratchings.md"),
                 (["scripts/entry_numbers.py", mid], md / "entry_numbers.md"),
                 (["scripts/race_times.py", mid], md / "race_times.md"),
                 (["scripts/fluc_meeting.py", mid], md / "fluc.md")]
        fn = forecast_name(track, mid)
        if fn:
            jobs.append((["scripts/track_forecast.py", d, fn], md / "forecast.md"))
        else:
            md.mkdir(parents=True, exist_ok=True); (md / "forecast.md").write_text(f"no coordinates for {track}\n")
    new_dates = sorted({r[0] for r in rows if r[4] and r[5]})
    for d in new_dates:
        jobs.append((["scripts/meeting_status.py", d], outdir / f"meeting_status-{d}.md"))
        jobs.append((["scripts/export_dataset.py", "--date", d, "--state", "VIC", "--out", str(outdir / f"upcoming-{d}.npz")],
                     outdir / f"export-{d}.md"))
    with open(outdir / "index.tsv", "w") as fh:
        fh.write("date\tmeeting_id\ttrack\tprefix\tnew\traces\n")
        for r in rows:
            fh.write("\t".join(map(str, r)) + "\n")
    for r in rows:
        print(f"{r[0]} {r[2]} ({r[1]}, {r[5]} races): {'NEW' if r[4] else 'already on a sheet'}", flush=True)
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for msg in ex.map(lambda j: run(*j), jobs):
            print(msg, flush=True)


if __name__ == "__main__":
    main()
