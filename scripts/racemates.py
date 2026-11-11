"""Last-start race-mates: who they were, and which of their next runs we hold (11 Nov 2026, founder: "Everything
except the field watcher", the second item being full histories for every horse's last-start race-mates so the
form-line test can be redone properly). Shared by racemate_gaps.py (the free coverage report) and horse_batch.py
(the paid fetch), so the two cannot disagree about who is worth a credit.

Every run we hold, from three places, deduplicated by (horse, race):
  fk.results          every runner of every race the live pipeline stored, with finish and SP
  fk.entries          a race pulled after it ran, whose result rides on each entry (horseResult)
  the history files   every runner of every back-test race, plus each runner's own past events on its race card
  fk.past_events      the runs listed on every Get Horse Form and race-form entry we have stored

A runner's last start is its latest race (trials out) before race day D. A race whose whole field we hold (it is in
fk.results or a history file) gives every race-mate; any other race gives only the horses we happen to hold.

A race-mate's next run "counts" for the runner when it fell after the last start and before D, the same no-leak rule
as t_formlines_ab.py. When no such run is known, the race-mate is SETTLED if what we know of it reaches D (a race card
or a profile of it dated on or after D lists every run up to then, so there was none), and OPEN otherwise. An OPEN
race-mate is the only kind a Get Horse Form can improve: it is the horse that went somewhere we do not pull (interstate,
or a day we were missing) or has not been looked at since. Its benefit is the number of runners it is OPEN for."""
from __future__ import annotations

import collections
import os
from pathlib import Path

import psycopg

from fk import fields as F
from fk import history as H

SINCE = "2025-07-01"     # the dataset's first day


def _f(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if x == x and x not in (float("inf"), float("-inf")) else None


def load(history_dir: str | None = "history", since: str = SINCE, log=print):
    """Returns (runs, fields, horizon, runners).
    runs[h]      sorted [(date, race_id, finish, sp)] for races (never trials)
    fields[r]    set of horses, only for races whose whole field we hold
    horizon[h]   latest date our knowledge of h reaches (a race card it was on, or a profile fetch)
    runners      [(horse, race_id, date)] every runner of a resulted VIC race on or after `since`"""
    runs: dict[str, dict[str, tuple]] = collections.defaultdict(dict)
    fields: dict[str, set] = collections.defaultdict(set)
    horizon: dict[str, str] = {}
    runners: list[tuple] = []

    def run(h, d, rid, fin, sp):
        if h and d and rid and rid not in runs[h]:
            runs[h][rid] = (d, rid, fin, sp)

    def reach(h, d):
        if h and d and d > horizon.get(h, ""):
            horizon[h] = d

    def past(h, p):
        if not isinstance(p, dict) or F.past_event_is_trial(p) or not F.past_event_is_race(p) or p.get("scratched"):
            return
        fin = F.past_event_finish(p)
        if fin is not None and fin > 0:
            run(h, F.past_event_date(p), F.past_event_race_id(p), fin, _f(p.get("startingPrice")))

    # ---- the history files: whole fields, and each runner's past events as of race day -------------------------------
    nf = nr = 0
    for path in H.files(Path(history_dir) if history_dir else None):
        nf += 1
        for b in H.read_file(path):
            d, rid, st = b.get("date"), b.get("race_id"), b.get("state")
            res = H.is_resulted(b)
            for e in b.get("entries") or []:
                if not isinstance(e, dict):
                    continue
                h = F.horse_id(e)
                reach(h, d)
                for p in F.entry_past_events(e):
                    past(h, p)
                r = F.entry_result(e)
                fin = F.result_finish_position(r) if r else None
                if res and fin is not None and fin > 0:
                    run(h, d, rid, fin, F.result_starting_price(r))
                    fields[rid].add(h)
                    if st == "VIC" and d >= since:
                        runners.append((h, rid, d)); nr += 1
    log(f"history files: {nf} days, {nr} VIC runners since {since}")

    with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
        # ---- fk.results: the live pipeline's races, whole fields ---------------------------------------------------
        k = 0
        for rid, d, st, h, fin, sp in c.execute(
                """select res.race_id, m.meeting_date::text, m.state, res.horse_id, res.finish_position, res.starting_price
                   from fk.results res join fk.races r using (race_id) join fk.meetings m using (meeting_id)
                   where res.finish_position is not null and res.finish_position > 0"""):
            reach(h, d)
            if rid not in runs[h]:
                run(h, d, rid, int(fin), _f(sp))
            if h not in fields[rid]:
                fields[rid].add(h)
                if st == "VIC" and d >= since:
                    runners.append((h, rid, d)); k += 1
        log(f"fk.results: {k} more VIC runners since {since}")
        # a race pulled AFTER it ran carries its result inside each entry (horseResult), not in fk.results
        # (Db.resulted_races reads both; the first cut of this file read only fk.results and missed the 11 Nov gap fill)
        k = 0
        for rid, d, st, h, fin, sp in c.execute(
                """select e.race_id, m.meeting_date::text, m.state, e.horse_id,
                          (e.raw->'horseResult'->>'finishPosition')::int, e.raw->'horseResult'->>'startingPrice'
                   from fk.entries e join fk.races r using (race_id) join fk.meetings m using (meeting_id)
                   where (e.raw->'horseResult'->>'finishPosition') ~ '^[0-9]+$'
                     and (e.raw->'horseResult'->>'finishPosition')::int > 0"""):
            reach(h, d)
            if rid not in runs[h]:
                run(h, d, rid, int(fin), _f(sp))
            if h not in fields[rid]:
                fields[rid].add(h)
                if st == "VIC" and d >= since:
                    runners.append((h, rid, d)); k += 1
        log(f"entries with horseResult: {k} more VIC runners since {since}")
        # race cards the pipeline stored but has no result for yet still date what we know of the horse
        for h, d in c.execute("""select e.horse_id, max(m.meeting_date)::text from fk.entries e
                                 join fk.races r using (race_id) join fk.meetings m using (meeting_id) group by e.horse_id"""):
            reach(h, d)
        # ---- fk.past_events and the profile fetch dates ------------------------------------------------------------
        cur = c.cursor(name="pe"); cur.itersize = 20000
        cur.execute("""select horse_id, event_date::text, raw->>'raceId', finish_position, raw->>'startingPrice',
                              coalesce((raw->>'trial')::boolean, false), coalesce((raw->>'race')::boolean, true),
                              (fetched_at at time zone 'Australia/Melbourne')::date::text
                       from fk.past_events""")
        n = 0
        for h, d, rid, fin, sp, tr, israce, fat in cur:
            n += 1
            reach(h, fat)
            if not tr and israce and fin is not None and fin > 0:
                run(h, d, rid, int(fin), _f(sp))
        log(f"fk.past_events: {n} rows")
        for h, d in c.execute("""select horse_id, (profile_fetched_at at time zone 'Australia/Melbourne')::date::text
                                 from fk.horses where profile_fetched_at is not null"""):
            reach(h, d)
    srt = {h: sorted(v.values()) for h, v in runs.items()}
    return srt, fields, horizon, runners


def analyse(runs, fields, horizon, runners):  # call index_partial(runs, fields) first
    """Per runner: race-mates known, counting, settled, open. Returns (stats, benefit) where benefit[h] counts the
    runners for which race-mate h is OPEN, and stats holds the per-runner rows (date, mates, counting, open, whole)."""
    benefit = collections.Counter()
    rows = []
    seen = set()
    for h, rid, D in runners:
        if (h, rid) in seen:
            continue
        seen.add((h, rid))
        last = None
        for x in runs.get(h, ()):
            if x[0] < D:
                last = x
            else:
                break
        if last is None:
            continue
        d0, r0 = last[0], last[1]
        whole = r0 in fields
        mates = fields[r0] if whole else _partial.get(r0, set())
        counting = opened = 0
        for m in mates:
            if m == h:
                continue
            nxt = next((x for x in runs.get(m, ()) if x[0] > d0), None)
            if nxt and nxt[0] < D:
                counting += 1
            elif horizon.get(m, "") < D:
                opened += 1
                benefit[m] += 1
        rows.append((D, len(mates) - (h in mates), counting, opened, whole))
    return rows, benefit


_partial: dict[str, set] = {}


def index_partial(runs, fields):
    """Races we do not hold whole: the horses we hold that ran in them."""
    _partial.clear()
    for h, rs in runs.items():
        for x in rs:
            if x[1] not in fields:
                _partial.setdefault(x[1], set()).add(h)
