"""Topaz: Greyhound Racing Victoria's racing data API, issued to Betfair Australia customers who bet with it
(research/greyhound/README.md has the eligibility rules and what the terms are known to say).

Endpoints are taken from the open-source Topaz-api wrapper (PyPI Topaz-api 0.0.7, MIT), because the official docs at
topaz.grv.org.au/docs could not be opened from the cloud session. The wrapper is unofficial, so `probe()` is the first
call made with a new key: it checks the server answers and prints the columns of one day's bulk file, nothing else.

The key is read from the environment (TOPAZ_API_KEY: a GitHub secret, never a file or a chat) and never printed: it
travels in one header, and no error message or repr carries the headers.
"""
from __future__ import annotations

import os
import time

import requests

BASE_URL = "https://topaz.grv.org.au/api"
# Owning authorities the bulk endpoint accepts. ACT has had no racing since 2018; NZ is GRNZ.
AUTHORITIES = ("ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA", "NZ")


class TopazError(RuntimeError):
    pass


class TopazClient:
    def __init__(self, api_key: str | None = None, session=None, pause: float = 2.0, retries: int = 4,
                 sleep=time.sleep):
        key = api_key if api_key is not None else os.environ.get("TOPAZ_API_KEY", "")
        if not key.strip():
            raise TopazError("TOPAZ_API_KEY is not set (it lives in the repository's Actions secrets)")
        self._headers = {"accept": "application/json", "X-API-Key": key.strip()}
        self._s = session or requests.Session()
        self.pause, self.retries, self._sleep = pause, retries, sleep
        self.calls = 0

    def __repr__(self) -> str:   # the key must never reach a log through a repr
        return f"TopazClient(calls={self.calls})"

    def _get(self, path: str, params: dict | None = None):
        """GET with a pause between calls, retrying 429 and 5xx with backoff (Retry-After honoured).
        404 means "no data for that request" and returns None. 401/403 is a permission refusal, never retried."""
        url = f"{BASE_URL}/{path.lstrip('/')}"
        for attempt in range(self.retries + 1):
            if self.calls:
                self._sleep(self.pause)
            self.calls += 1
            try:
                r = self._s.get(url, headers=self._headers, params=params, timeout=60)
            except requests.RequestException as e:   # network blip: retry, and name the path, not the headers
                if attempt == self.retries:
                    raise TopazError(f"{path}: {type(e).__name__} after {attempt + 1} tries") from None
                self._sleep(2 ** attempt * 5)
                continue
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
            if r.status_code in (401, 403):
                raise TopazError(f"{path}: HTTP {r.status_code}, the key is not allowed this data "
                                 "(wrong key, lapsed access, or a state/date outside the key's permissions)")
            if r.status_code == 429 or r.status_code >= 500:
                if attempt == self.retries:
                    raise TopazError(f"{path}: HTTP {r.status_code} after {attempt + 1} tries")
                wait = r.headers.get("Retry-After", "")
                self._sleep(float(wait) if wait.replace(".", "", 1).isdigit() else 2 ** attempt * 10)
                continue
            raise TopazError(f"{path}: HTTP {r.status_code}: {r.text[:300]}")
        raise TopazError(f"{path}: gave up")   # unreachable; keeps the type checker honest

    def health(self):
        return self._get("health")

    def bulk_runs_month(self, authority: str, year: int, month: int) -> list[dict]:
        """Every run (one row per dog per race) for one state and month. [] when Topaz holds nothing."""
        _check(authority)
        return self._get(f"bulk/runs/{authority}/{year}/{month}") or []

    def bulk_runs_day(self, authority: str, year: int, month: int, day: int) -> list[dict]:
        _check(authority)
        return self._get(f"bulk/runs/{authority}/{year}/{month}/{day}") or []


def _check(authority: str) -> None:
    if authority not in AUTHORITIES:
        raise ValueError(f"unknown owning authority {authority!r}; one of {', '.join(AUTHORITIES)}")
