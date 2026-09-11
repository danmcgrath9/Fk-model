"""Runtime configuration. Everything comes from the environment (.env), never from code."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# The key Form King publishes for testing. Calls made with it are recorded in the
# ledger under key_kind='test' and never count against the live balance.
TEST_API_KEY = "FK-TEST-API-KEY"

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    spec_path: Path
    base_url: str | None
    database_url: str | None
    ledger_path: Path
    monthly_credits: int
    credits_overrides_path: Path

    @property
    def live_key_present(self) -> bool:
        return bool(self.api_key) and self.api_key != TEST_API_KEY


def load_settings(env_file: str | os.PathLike | None = None) -> Settings:
    """Load .env from the project root (or the given file) and build Settings.

    Missing values stay None; the code that needs them raises a clear error at the
    point of use rather than here, so a report build does not demand a database.
    """
    load_dotenv(env_file or PROJECT_ROOT / ".env", override=False)

    def path(name: str, default: str) -> Path:
        raw = os.environ.get(name, default)
        p = Path(raw)
        return p if p.is_absolute() else PROJECT_ROOT / p

    return Settings(
        api_key=os.environ.get("FK_API_KEY") or None,
        spec_path=path("FK_SPEC_PATH", "b2c-openapi.yaml"),
        base_url=os.environ.get("FK_BASE_URL") or None,
        database_url=os.environ.get("DATABASE_URL") or None,
        ledger_path=path("FK_LEDGER_PATH", "credits.sqlite"),
        monthly_credits=int(os.environ.get("FK_MONTHLY_CREDITS", "20000")),
        credits_overrides_path=path("FK_CREDITS_PATH", "credits.yaml"),
    )
