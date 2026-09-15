"""Shared bootstrap for the scripts: settings, spec, costs, ledger, client."""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fk.client import FormKingClient  # noqa: E402
from fk.config import TEST_API_KEY, Settings, load_settings  # noqa: E402
from fk.credits import CostTable, build_cost_table  # noqa: E402
from fk.guard import CreditCapExceeded, check_spend  # noqa: E402
from fk.ledger import Ledger  # noqa: E402
from fk.spec import Spec  # noqa: E402

AEST = timezone(timedelta(hours=10))  # Victoria is +10, +11 in daylight saving; date maths only


def now_melbourne() -> datetime:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Australia/Melbourne"))
    except Exception:
        return datetime.now(AEST)


def today_melbourne() -> date:
    # zoneinfo is exact; fall back to a fixed offset if tzdata is missing on the machine.
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Australia/Melbourne")).date()
    except Exception:
        return datetime.now(AEST).date()


def bootstrap(key: str) -> tuple[Settings, Spec, CostTable, Ledger]:
    settings = load_settings()
    spec = Spec.load(settings.spec_path)
    costs = build_cost_table(spec, settings.credits_overrides_path)
    ledger = open_ledger(settings)
    return settings, spec, costs, ledger


def open_ledger(settings: Settings) -> Ledger:
    """FK_LEDGER=postgres keeps the ledger in the database (unattended runs have no disk
    that survives the job); anything else is the local SQLite file."""
    import os
    if os.environ.get("FK_LEDGER", "sqlite").lower() == "postgres":
        if not settings.database_url:
            sys.exit("FK_LEDGER=postgres but DATABASE_URL is not set")
        return Ledger.postgres(settings.database_url, settings.monthly_credits)
    return Ledger(settings.ledger_path, settings.monthly_credits)


def make_client(key: str, settings: Settings, spec: Spec, costs: CostTable, ledger: Ledger, allow_live: bool) -> FormKingClient:
    """key: 'test' or 'live'. The live key only comes from .env, never from an argument."""
    if key == "test":
        api_key = TEST_API_KEY
    elif key == "live":
        if not settings.live_key_present:
            sys.exit("FK_API_KEY is not set in .env (or is the test key); cannot run --key live")
        api_key = settings.api_key  # type: ignore[assignment]
    else:
        sys.exit("--key must be test or live")
    return FormKingClient(spec, api_key, ledger, costs, base_url=settings.base_url, allow_live=allow_live)


def confirm(prompt: str, assume_yes: bool, *, estimated: int = 0, balance: int | None = None, live: bool = False) -> bool:
    """Interactive: ask. Unattended (--yes): nobody can say no, so the credit cap and the
    balance floor say it instead, before the first paid call."""
    if assume_yes:
        if live:
            try:
                check_spend(estimated, balance if balance is not None else 0)
            except CreditCapExceeded as e:
                sys.exit(f"STOPPED: {e}")
        return True
    answer = input(f"{prompt} [y/N] ").strip().lower()
    return answer in ("y", "yes")
