"""Spending guards for runs nobody is watching."""
from __future__ import annotations

import os


class CreditCapExceeded(Exception):
    pass


def credit_cap() -> int:
    """FK_MAX_CREDITS_PER_RUN, default 600: about two nine-race meetings plus profiles.
    A run whose estimate exceeds it stops before the first paid call."""
    return int(os.environ.get("FK_MAX_CREDITS_PER_RUN", "600"))


def balance_floor() -> int:
    """FK_MIN_BALANCE, default 1000: never let an unattended run spend the month's last credits."""
    return int(os.environ.get("FK_MIN_BALANCE", "1000"))


def check_spend(estimated: int, balance: int, *, cap: int | None = None, floor: int | None = None) -> None:
    cap = credit_cap() if cap is None else cap
    floor = balance_floor() if floor is None else floor
    if estimated > cap:
        raise CreditCapExceeded(
            f"estimated {estimated} credits exceeds the per-run cap of {cap} (FK_MAX_CREDITS_PER_RUN). "
            "Not spending. If the estimate is right, raise the cap on purpose."
        )
    if balance - estimated < floor:
        raise CreditCapExceeded(
            f"estimated {estimated} credits would take the balance from {balance} to {balance - estimated}, "
            f"below the floor of {floor} (FK_MIN_BALANCE). Not spending."
        )
