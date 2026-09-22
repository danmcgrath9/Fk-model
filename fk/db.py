"""Postgres (Supabase) store. Thin: upserts keyed on the primary key, raw payload kept."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Iterable

from psycopg.types.json import Jsonb

from .pg import connect


class Db:
    """Writes are buffered per (table, key) and flushed on commit() in psycopg's pipeline
    mode, so a race's thousand-odd past-event rows cost one batched round to the server
    rather than one round trip each. From a GitHub runner to Sydney that is the
    difference between seconds and minutes per race. Reads see committed data only, which
    is how the scripts already use them (commit after each unit, then read)."""

    def __init__(self, database_url: str):
        self.conn = connect(database_url, autocommit=False)
        self._pending: dict[tuple[str, tuple[str, ...], tuple[str, ...]], list[list[Any]]] = {}

    def close(self) -> None:
        self.conn.close()

    def migrate(self, sql_path: str) -> None:
        with open(sql_path, "r", encoding="utf-8") as fh:
            self.conn.execute(fh.read())
        self.conn.commit()

    # ---- generic upsert ----------------------------------------------------------

    def upsert(self, table: str, key_cols: list[str], row: dict[str, Any]) -> None:
        cols = tuple(row)
        vals = [Jsonb(v) if isinstance(v, (dict, list)) else v for v in row.values()]
        self._pending.setdefault((table, tuple(key_cols), cols), []).append(vals)

    def flush(self) -> None:
        """Send every buffered write, one executemany per (table, column set), pipelined."""
        if not self._pending:
            return
        pending, self._pending = self._pending, {}
        with self.conn.pipeline():
            with self.conn.cursor() as cur:
                for (table, key_cols, cols), rows in pending.items():
                    updates = [c for c in cols if c not in key_cols]
                    sql = (
                        f"insert into fk.{table} ({', '.join(cols)}) values ({', '.join(['%s'] * len(cols))})"
                        f" on conflict ({', '.join(key_cols)}) do update set "
                        + (", ".join(f"{c} = excluded.{c}" for c in updates) if updates else f"{cols[0]} = excluded.{cols[0]}")
                    )
                    cur.executemany(sql, rows)

    def commit(self) -> None:
        self.flush()
        self.conn.commit()

    def rollback(self) -> None:
        self._pending.clear()
        self.conn.rollback()

    # ---- typed reads the scripts need -------------------------------------------

    def known_horses(self, horse_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
        ids = list(horse_ids)
        if not ids:
            return {}
        rows = self.conn.execute(
            "select horse_id, profile_depth, profile_fetched_at from fk.horses where horse_id = any(%s)", (ids,)
        ).fetchall()
        return {r[0]: {"profile_depth": r[1], "profile_fetched_at": r[2]} for r in rows}

    def benchmarked_run_counts(self, horse_ids: Iterable[str]) -> dict[str, int]:
        ids = list(horse_ids)
        if not ids:
            return {}
        rows = self.conn.execute(
            "select horse_id, count(*) from fk.benchmarked_runs where horse_id = any(%s) group by horse_id", (ids,)
        ).fetchall()
        return {r[0]: int(r[1]) for r in rows}

    def meetings_on(self, meeting_date: str, state: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "select meeting_id, track, raw from fk.meetings where meeting_date = %s and state = %s order by track",
            (meeting_date, state),
        ).fetchall()
        return [{"meeting_id": r[0], "track": r[1], "raw": r[2]} for r in rows]

    def races_on(self, meeting_date: str, state: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """select r.race_id, r.meeting_id, r.race_number, r.race_name, r.distance_m, r.scheduled_at,
                      m.track, m.meeting_date, r.raw
               from fk.races r join fk.meetings m using (meeting_id)
               where m.meeting_date = %s and m.state = %s
               order by m.track, r.race_number""",
            (meeting_date, state),
        ).fetchall()
        keys = ["race_id", "meeting_id", "race_number", "race_name", "distance_m", "scheduled_at", "track", "meeting_date", "raw"]
        return [dict(zip(keys, r)) for r in rows]

    def entries_for_race(self, race_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """select e.horse_id, h.name, e.barrier, e.weight_kg, e.jockey, e.trainer, e.scratched,
                      e.neural_rating, e.exp_rating, e.days_since_last_run, e.raw
               from fk.entries e join fk.horses h using (horse_id)
               where e.race_id = %s order by e.barrier nulls last""",
            (race_id,),
        ).fetchall()
        keys = ["horse_id", "name", "barrier", "weight_kg", "jockey", "trainer", "scratched", "neural_rating", "exp_rating", "days_since_last_run", "raw"]
        return [dict(zip(keys, (_plain(v) for v in r))) for r in rows]

    def runs_for_horse(self, horse_id: str, limit: int) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """select run_id, event_date, track_speed_verified, sections, positions, vs_class, raw
               from fk.benchmarked_runs where horse_id = %s
               order by event_date desc nulls last, run_id desc limit %s""",
            (horse_id, limit),
        ).fetchall()
        keys = ["run_id", "event_date", "track_speed_verified", "sections", "positions", "vs_class", "raw"]
        return [dict(zip(keys, r)) for r in rows]

    def past_events_for_horse(self, horse_id: str, limit: int) -> list[dict[str, Any]]:
        """Newest first, races and trials, with the whole PastEvent for the ratings profile."""
        rows = self.conn.execute(
            """select past_event_id, event_date, raw from fk.past_events
               where horse_id = %s order by event_date desc nulls last, past_event_id desc limit %s""",
            (horse_id, limit),
        ).fetchall()
        return [{"past_event_id": r[0], "event_date": r[1], "raw": r[2]} for r in rows]

    def resulted_races(self, state: str | None = "VIC") -> list[dict[str, Any]]:
        """Every stored race with an official result, for the back-test: (race_id, date,
        track, entries raw). A race pulled AFTER it ran carries the result inside each entry
        (horseResult); a race pulled the night before, the live pipeline's way, has its
        result in fk.results from the morning job, and that is folded into the entry here
        under the same horseResult key, so the fit sees the form as it stood before the
        jump and the result as it came in. Without this the fit stopped at the last
        back-test pull and never learned from a day the pipeline ran."""
        rows = self.conn.execute(
            """select r.race_id, m.meeting_date, m.track, r.distance_m, (r.raw->>'lws')::numeric as lws,
                      jsonb_agg(
                        case when e.raw ? 'horseResult' or res.finish_position is null then e.raw
                             else e.raw || jsonb_build_object('horseResult', jsonb_strip_nulls(jsonb_build_object(
                                    'finishPosition', res.finish_position,
                                    'startingPrice', res.starting_price,
                                    'betfairStartingPrice', (res.raw->>'betfairStartingPrice')::numeric)))
                        end order by e.barrier nulls last) as entries,
                      sm.runners, sm.raw->'expectedTempo'
               from fk.races r join fk.meetings m using (meeting_id) join fk.entries e using (race_id)
                    left join fk.results res on res.race_id = e.race_id and res.horse_id = e.horse_id
                    left join fk.speedmaps sm on sm.race_id = r.race_id
               where (%s::text is null or m.state = %s)
               group by r.race_id, m.meeting_date, m.track, r.distance_m, r.raw->>'lws', sm.runners, sm.raw
               having bool_or(e.raw ? 'horseResult' or res.finish_position is not null)
               order by m.meeting_date, m.track, r.race_id""",
            (state, state),
        ).fetchall()
        return [{"race_id": r[0], "date": str(r[1]), "track": r[2], "distance_m": r[3],
                 "lws": float(r[4]) if r[4] is not None else None, "entries": r[5],
                 "speedmap": r[6], "tempo": r[7]} for r in rows]

    # ---- the paper book ------------------------------------------------------------

    def ensure_paper_book(self) -> None:
        """Apply sql/003 when fk.paper_bets is missing and sql/004 when its later columns
        are (both files are guarded, so re-running either is a no-op)."""
        from pathlib import Path
        sql_dir = Path(__file__).resolve().parents[1] / "sql"
        row = self.conn.execute("select to_regclass('fk.paper_bets')").fetchone()
        if not (row and row[0]):
            self.conn.execute((sql_dir / "003_paper_book.sql").read_text(encoding="utf-8"))
            self.conn.commit()
        have = self.conn.execute(
            "select 1 from information_schema.columns where table_schema = 'fk' and table_name = 'paper_bets' "
            "and column_name = 'first_priced_at'"
        ).fetchone()
        if not have:
            self.conn.execute((sql_dir / "004_paper_opening_and_snapshot.sql").read_text(encoding="utf-8"))
            self.conn.commit()

    def race_first_priced_at(self, race_id: str):
        """When this race was first priced into the book, or None if it never was. A race is
        bet ONCE, at its first pricing; a later run must not add to it."""
        row = self.conn.execute(
            "select min(coalesce(first_priced_at, placed_at)) from fk.paper_bets where race_id = %s", (race_id,)
        ).fetchone()
        return row[0] if row else None

    def place_paper_bets(self, rows: list[dict[str, Any]]) -> int:
        """Insert bets that are not already there; a bet once placed is never re-priced."""
        if not rows:
            return 0
        cols = list(rows[0].keys())
        placeholders = ", ".join(["%s"] * len(cols))
        n = 0
        with self.conn.cursor() as cur:
            for r in rows:
                cur.execute(
                    f"insert into fk.paper_bets ({', '.join(cols)}) values ({placeholders}) on conflict (bet_id) do nothing",
                    [r[c] for c in cols],
                )
                n += cur.rowcount
        self.conn.commit()
        return n

    def open_paper_bets_with_results(self) -> list[dict[str, Any]]:
        """Unsettled bets whose race now has a result: the finish, SP and Betfair SP for the horse."""
        rows = self.conn.execute(
            """select b.bet_id, b.stake, r.finish_position, r.starting_price, (r.raw->>'betfairStartingPrice')::numeric
               from fk.paper_bets b join fk.results r using (race_id, horse_id)
               where b.settled_at is null"""
        ).fetchall()
        return [{"bet_id": r[0], "stake": float(r[1]), "finish": r[2], "sp": float(r[3]) if r[3] is not None else None,
                 "bsp": float(r[4]) if r[4] is not None else None} for r in rows]

    def open_paper_bets_with_jump(self) -> list[dict[str, Any]]:
        """Unsettled bets with when they were placed and when their race was due to start."""
        rows = self.conn.execute(
            """select b.bet_id, b.placed_at, m.meeting_date, r.raw->>'startTime', b.track, b.race_number
               from fk.paper_bets b join fk.races r using (race_id) join fk.meetings m using (meeting_id)
               where b.settled_at is null"""
        ).fetchall()
        keys = ["bet_id", "placed_at", "meeting_date", "start_time", "track", "race_number"]
        return [dict(zip(keys, r)) for r in rows]

    def delete_paper_bets(self, bet_ids: list[str]) -> int:
        if not bet_ids:
            return 0
        cur = self.conn.execute("delete from fk.paper_bets where bet_id = any(%s)", (bet_ids,))
        return cur.rowcount

    def settle_paper_bet(self, bet_id: str, settle_price: float | None, finish: int | None, won: bool, returned: float) -> None:
        self.conn.execute(
            "update fk.paper_bets set settled_at = now(), settle_price = %s, finish = %s, won = %s, returned = %s where bet_id = %s",
            (settle_price, finish, won, returned, bet_id),
        )

    def paper_bets(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """select bet_id, plan, meeting_date, track, race_number, horse_name, price, rated_price, stake,
                      settled_at, settle_price, finish, won, returned, opening_price, placed_at, race_id
               from fk.paper_bets order by meeting_date, race_number, bet_id"""
        ).fetchall()
        keys = ["bet_id", "plan", "meeting_date", "track", "race_number", "horse_name", "price", "rated_price", "stake",
                "settled_at", "settle_price", "finish", "won", "returned", "opening_price", "placed_at", "race_id"]
        return [dict(zip(keys, (_plain(v) for v in r))) for r in rows]

    def races_fetched_since(self, since: datetime) -> set[str]:
        """Race ids whose race form (entries) was fetched at or after `since`."""
        rows = self.conn.execute(
            "select distinct race_id from fk.entries where fetched_at >= %s", (since,)
        ).fetchall()
        return {r[0] for r in rows}

    def results_for_race(self, race_id: str) -> dict[str, dict[str, Any]]:
        """{horse_id: {finish, sp}} from the results the morning job stores."""
        rows = self.conn.execute(
            "select horse_id, finish_position, starting_price from fk.results where race_id = %s", (race_id,)
        ).fetchall()
        return {r[0]: {"finish": r[1], "sp": float(r[2]) if r[2] is not None else None} for r in rows}

    def speedmap_for_race(self, race_id: str) -> list[dict[str, Any]] | None:
        row = self.conn.execute("select runners from fk.speedmaps where race_id = %s", (race_id,)).fetchone()
        return row[0] if row else None

    def speedmap_tempo(self, race_id: str) -> str | None:
        row = self.conn.execute("select raw->'expectedTempo'->>'description' from fk.speedmaps where race_id = %s", (race_id,)).fetchone()
        return row[0] if row else None

    def speedmap_tempo_raw(self, race_id: str) -> dict[str, Any] | None:
        """Form King's whole expectedTempo object (description, min, max, categories)."""
        row = self.conn.execute("select raw->'expectedTempo' from fk.speedmaps where race_id = %s", (race_id,)).fetchone()
        return row[0] if row and isinstance(row[0], dict) else None

    def latest_odds(self, race_id: str) -> dict[str, dict[str, float]]:
        """{horse_id: {opening: p, current: p}} using the newest observation of each kind."""
        rows = self.conn.execute(
            """select distinct on (horse_id, kind) horse_id, kind, price
               from fk.odds_snapshots where race_id = %s
               order by horse_id, kind, observed_at desc""",
            (race_id,),
        ).fetchall()
        out: dict[str, dict[str, float]] = {}
        for horse_id, kind, price in rows:
            out.setdefault(horse_id, {})[kind] = float(price)
        return out


def _plain(v: Any) -> Any:
    """Postgres numeric arrives as Decimal; the report maths wants float."""
    return float(v) if isinstance(v, Decimal) else v


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
