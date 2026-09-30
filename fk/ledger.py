"""Credit ledger: one row per API call, with its cost and the running live balance.

Two backends with one interface:
  * SQLite (default, local): Ledger(path)
  * Postgres (unattended runs on GitHub Actions, where the runner's disk is gone after
    every job): Ledger.postgres(database_url), table fk.credit_ledger from
    sql/002_credit_ledger_and_reports.sql

The balance is derived (allowance less the billing period's live spend, plus any
reconciliation adjustments), never stored as a mutable counter, so it cannot drift from
the rows that explain it. Test-key calls are recorded but never charged: key_kind='test'.

The allowance resets on the subscription's billing day, not the 1st (FK_PERIOD_START_DAY,
the day of the month the invoice was paid; 11 for this account). Spend is summed over the
period by timestamp, so rows written when the ledger assumed calendar months still land in
the right period. A period is keyed by the month it starts in: "2026-09" is 11 Sep to 10 Oct.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SQLITE_SCHEMA = """
create table if not exists calls (
    id            integer primary key autoincrement,
    ts            text not null,                 -- ISO-8601 UTC
    month         text not null,                 -- YYYY-MM (UTC) for the allowance window
    key_kind      text not null check (key_kind in ('live','test','adjust')),
    operation     text not null,
    method        text,
    path          text,
    params        text,                          -- JSON
    http_status   integer,
    credits       integer not null,              -- charged credits; negative allowed on 'adjust'
    note          text
);
create index if not exists calls_month on calls(month, key_kind);
"""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def period_bounds(key_or_dt: str | datetime | None, start_day: int) -> tuple[str, datetime, datetime]:
    """(key, start, end) of the billing period holding a moment, or named by its key "YYYY-MM"
    (the month it starts in). Bounds are UTC midnights on start_day."""
    if isinstance(key_or_dt, str):
        y, m = int(key_or_dt[:4]), int(key_or_dt[5:7])
    else:
        dt = key_or_dt or _utc_now()
        y, m = dt.year, dt.month
        if dt.day < start_day:
            y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    start = datetime(y, m, start_day, tzinfo=timezone.utc)
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    return f"{y:04d}-{m:02d}", start, datetime(ny, nm, start_day, tzinfo=timezone.utc)


@dataclass(frozen=True)
class LedgerRow:
    id: int
    ts: str
    month: str
    key_kind: str
    operation: str
    method: str | None
    path: str | None
    params: dict[str, Any]
    http_status: int | None
    credits: int
    note: str | None
    balance_after: int | None  # live balance after this row, None for test rows


class Ledger:
    """Construct with a SQLite path, or use Ledger.postgres(url)."""

    def __init__(self, path: str | Path | None = None, monthly_allowance: int = 20000, *, _pg_conn: Any = None,
                 period_start_day: int = 1):
        self.monthly_allowance = monthly_allowance
        self.period_start_day = period_start_day
        if _pg_conn is not None:
            self.conn = _pg_conn
            self.table = "fk.credit_ledger"
            self.ph = "%s"
            self.path = None
        else:
            if path is None:
                raise ValueError("Ledger needs a SQLite path or Ledger.postgres(url)")
            self.path = str(path)
            self.conn = sqlite3.connect(self.path)
            self.conn.executescript(SQLITE_SCHEMA)
            self.table = "calls"
            self.ph = "?"

    @classmethod
    def postgres(cls, database_url: str, monthly_allowance: int = 20000, period_start_day: int = 1) -> "Ledger":
        from .pg import connect
        return cls(None, monthly_allowance, _pg_conn=connect(database_url, autocommit=False), period_start_day=period_start_day)

    def period(self, key_or_dt: str | datetime | None = None) -> tuple[str, datetime, datetime]:
        return period_bounds(key_or_dt, self.period_start_day)

    def _ts(self, dt: datetime) -> Any:
        return dt if self.is_postgres else dt.isoformat(timespec="seconds")

    @property
    def is_postgres(self) -> bool:
        return self.table.startswith("fk.")

    def close(self) -> None:
        self.conn.close()

    def _run(self, sql: str, args: tuple = ()) -> Any:
        return self.conn.execute(sql.replace("?", self.ph), args)

    # ---- writes ----------------------------------------------------------------

    def record(
        self,
        operation: str,
        credits: int,
        *,
        key_kind: str = "live",
        method: str | None = None,
        path: str | None = None,
        params: dict[str, Any] | None = None,
        http_status: int | None = None,
        note: str | None = None,
        at: datetime | None = None,
    ) -> int:
        at = at or _utc_now()
        values = (
            at.isoformat(timespec="seconds"), self.period(at)[0], key_kind, operation, method, path,
            json.dumps(params or {}, sort_keys=True, default=str), http_status, int(credits), note,
        )
        cols = "(ts, month, key_kind, operation, method, path, params, http_status, credits, note)"
        if self.is_postgres:
            row = self._run(f"insert into {self.table} {cols} values (?,?,?,?,?,?,?,?,?,?) returning id", values).fetchone()
            self.conn.commit()
            return int(row[0])
        cur = self._run(f"insert into {self.table} {cols} values (?,?,?,?,?,?,?,?,?,?)", values)
        self.conn.commit()
        return int(cur.lastrowid)

    def adjust(self, credits: int, note: str, at: datetime | None = None) -> int:
        """Reconcile against the Form King usage tab. Positive credits = we under-counted
        (charge more); negative = we over-counted. The row keeps the reason."""
        return self.record("reconciliation", credits, key_kind="adjust", note=note, at=at)

    # ---- reads -----------------------------------------------------------------

    def spent(self, month: str | None = None) -> int:
        _, start, end = self.period(month)
        row = self._run(
            f"select coalesce(sum(credits),0) from {self.table} where ts >= ? and ts < ? and key_kind in ('live','adjust')",
            (self._ts(start), self._ts(end)),
        ).fetchone()
        return int(row[0])

    def balance(self, month: str | None = None) -> int:
        return self.monthly_allowance - self.spent(month)

    def rows(self, month: str | None = None, limit: int | None = None) -> list[LedgerRow]:
        q = f"select id, ts, month, key_kind, operation, method, path, params, http_status, credits, note from {self.table}"
        args: tuple = ()
        if month:
            _, start, end = self.period(month)
            q += " where ts >= ? and ts < ?"
            args = (self._ts(start), self._ts(end))
        q += " order by id"
        out: list[LedgerRow] = []
        running: dict[str, int] = {}
        for r in self._run(q, args).fetchall():
            ts = r[1] if isinstance(r[1], datetime) else datetime.fromisoformat(str(r[1]))
            m, kind, credits = self.period(ts)[0], r[3], r[9]
            bal = None
            if kind in ("live", "adjust"):
                running[m] = running.get(m, 0) + credits
                bal = self.monthly_allowance - running[m]
            params = r[7]
            out.append(
                LedgerRow(
                    id=r[0], ts=str(r[1]), month=m, key_kind=kind, operation=r[4], method=r[5], path=r[6],
                    params=params if isinstance(params, dict) else json.loads(params or "{}"),
                    http_status=r[8], credits=credits, note=r[10], balance_after=bal,
                )
            )
        return out[-limit:] if limit else out

    def summary(self, month: str | None = None) -> dict[str, Any]:
        month, start, end = self.period(month)
        by_op = self._run(
            f"select operation, key_kind, count(*), sum(credits) from {self.table} where ts >= ? and ts < ? "
            "group by operation, key_kind order by operation",
            (self._ts(start), self._ts(end)),
        ).fetchall()
        return {
            "month": f"{month} (billing period {start:%d %b} to {end:%d %b})",
            "allowance": self.monthly_allowance,
            "spent": self.spent(month),
            "balance": self.balance(month),
            "by_operation": [
                {"operation": o, "key_kind": k, "calls": int(c), "credits": int(s)} for o, k, c, s in by_op
            ],
        }
