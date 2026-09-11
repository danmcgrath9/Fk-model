"""One place that opens a Postgres connection, with the Supabase networking trap handled.

Supabase's "direct connection" host (db.<ref>.supabase.co) resolves to IPv6 only, and
GitHub-hosted runners have no IPv6, so a DATABASE_URL copied from that panel fails with
"Network is unreachable". The Session pooler (postgres.<ref>@aws-N-<region>.pooler.
supabase.com:5432) is reachable over IPv4. When the given URL is the direct form and the
connection fails, the pooler candidates are tried in turn and the one that works is
printed, so the secret can be corrected at leisure.
"""
from __future__ import annotations

import os
import re
from urllib.parse import urlsplit, urlunsplit

import psycopg

DIRECT_HOST = re.compile(r"^db\.([a-z0-9]+)\.supabase\.co$")


def pooler_candidates(url: str, region: str | None = None) -> list[str]:
    """Pooler URLs equivalent to a direct-connection Supabase URL; [] for any other URL."""
    parts = urlsplit(url)
    m = DIRECT_HOST.match(parts.hostname or "")
    if not m:
        return []
    ref = m.group(1)
    region = region or os.environ.get("FK_SUPABASE_REGION", "ap-southeast-2")
    user = parts.username or "postgres"
    if "." not in user:
        user = f"{user}.{ref}"
    password = parts.password or ""
    auth = f"{user}:{password}@" if password else f"{user}@"
    out = []
    for n in (0, 1):
        for port in (5432, 6543):
            netloc = f"{auth}aws-{n}-{region}.pooler.supabase.com:{port}"
            out.append(urlunsplit((parts.scheme, netloc, parts.path or "/postgres", parts.query, parts.fragment)))
    return out


def redact(url: str) -> str:
    parts = urlsplit(url)
    host = f"{parts.hostname}:{parts.port}" if parts.port else str(parts.hostname)
    return f"{parts.scheme}://{parts.username}:***@{host}{parts.path}"


def connect(database_url: str, *, autocommit: bool = False) -> psycopg.Connection:
    database_url = (database_url or "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set; put the Supabase connection string in .env or the FK_DATABASE_URL secret")
    if "YOUR-PASSWORD" in database_url.upper() or "YOUR_PASSWORD" in database_url.upper():
        raise RuntimeError(
            "FK_DATABASE_URL still contains the [YOUR-PASSWORD] placeholder. Replace it (brackets included) with the "
            "database password from Supabase, Settings, Database, and save the secret again."
        )
    try:
        return psycopg.connect(database_url, autocommit=autocommit, connect_timeout=15)
    except psycopg.OperationalError as first:
        candidates = pooler_candidates(database_url)
        if not candidates:
            raise
        print(f"database: {redact(database_url)} is Supabase's direct (IPv6-only) address and failed: {str(first).strip().splitlines()[0]}")
        for cand in candidates:
            try:
                conn = psycopg.connect(cand, autocommit=autocommit, connect_timeout=15)
            except psycopg.OperationalError as e:
                msg = str(e).strip().splitlines()[0]
                print(f"database: {redact(cand)} failed: {msg}")
                if "password authentication failed" in msg:
                    raise RuntimeError(
                        f"the database at {redact(cand)} answered, but refused the PASSWORD in FK_DATABASE_URL. "
                        "Reset the database password in Supabase (Settings, Database, Reset database password; letters "
                        "and numbers only), then save the secret as "
                        f"{cand.split('//')[0]}//{urlsplit(cand).username}:<new password>@{urlsplit(cand).hostname}:{urlsplit(cand).port}/postgres"
                    ) from e
                continue
            print(f"database: connected via {redact(cand)}. Set FK_DATABASE_URL to this Session pooler form to skip the retries.")
            return conn
        raise RuntimeError(
            "could not reach the database by the direct address or any pooler candidate. In Supabase: Connect, "
            "Connection string, choose Session pooler, and use that URI (region may differ from ap-southeast-2: set FK_SUPABASE_REGION)."
        ) from first
