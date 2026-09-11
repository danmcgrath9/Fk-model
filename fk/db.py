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
                      m.track, m.meeting_date
               from fk.races r join fk.meetings m using (meeting_id)
               where m.meeting_date = %s and m.state = %s
               order by m.track, r.race_number""",
            (meeting_date, state),
        ).fetchall()
        keys = ["race_id", "meeting_id", "race_number", "race_name", "distance_m", "scheduled_at", "track", "meeting_date"]
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

    def speedmap_for_race(self, race_id: str) -> list[dict[str, Any]] | None:
        row = self.conn.execute("select runners from fk.speedmaps where race_id = %s", (race_id,)).fetchone()
        return row[0] if row else None

    def speedmap_tempo(self, race_id: str) -> str | None:
        row = self.conn.execute("select raw->'expectedTempo'->>'description' from fk.speedmaps where race_id = %s", (race_id,)).fetchone()
        return row[0] if row else None

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
