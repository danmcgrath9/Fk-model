"""Credit ledger: one row per API call, with its cost and the running live balance.

Two backends with one interface:
  * SQLite (default, local): Ledger(path)
  * Postgres (unattended runs on GitHub Actions, where the runner's disk is gone after
    every job): Ledger.postgres(database_url), table fk.credit_ledger from
    sql/002_credit_ledger_and_reports.sql

The balance is derived (allowance less the month's live spend, plus any reconciliation
adjustments), never stored as a mutable counter, so it cannot drift from the rows that
explain it. Test-key calls are recorded but never charged: key_kind='test'.
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

    def __init__(self, path: str | Path | None = None, monthly_allowance: int = 20000, *, _pg_conn: Any = None):
        self.monthly_allowance = monthly_allowance
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
    def postgres(cls, database_url: str, monthly_allowance: int = 20000) -> "Ledger":
        import psycopg
        conn = psycopg.connect(database_url, autocommit=False)
        return cls(None, monthly_allowance, _pg_conn=conn)

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
            at.isoformat(timespec="seconds"), at.strftime("%Y-%m"), key_kind, operation, method, path,
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
        month = month or _utc_now().strftime("%Y-%m")
        row = self._run(
            f"select coalesce(sum(credits),0) from {self.table} where month=? and key_kind in ('live','adjust')", (month,)
        ).fetchone()
        return int(row[0])

    def balance(self, month: str | None = None) -> int:
        return self.monthly_allowance - self.spent(month)

    def rows(self, month: str | None = None, limit: int | None = None) -> list[LedgerRow]:
        q = f"select id, ts, month, key_kind, operation, method, path, params, http_status, credits, note from {self.table}"
        args: tuple = ()
        if month:
            q += " where month=?"
            args = (month,)
        q += " order by id"
        out: list[LedgerRow] = []
        running: dict[str, int] = {}
        for r in self._run(q, args).fetchall():
            m, kind, credits = r[2], r[3], r[9]
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
        month = month or _utc_now().strftime("%Y-%m")
        by_op = self._run(
            f"select operation, key_kind, count(*), sum(credits) from {self.table} where month=? "
            "group by operation, key_kind order by operation",
            (month,),
        ).fetchall()
        return {
            "month": month,
            "allowance": self.monthly_allowance,
            "spent": self.spent(month),
            "balance": self.balance(month),
            "by_operation": [
                {"operation": o, "key_kind": k, "calls": int(c), "credits": int(s)} for o, k, c, s in by_op
            ],
        }
