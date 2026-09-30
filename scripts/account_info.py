"""Form King's own view of the account: bundled balance, top-up balance and the dates of the
current bundled-credit period (when the allowance resets). 1 credit.

Uses POST /b2c/account/keys with operation getAccountInfo, resolved by the API key, because the
GET form needs the account's Firebase uid, which we do not hold. The response carries the API
key, uid and email; none of them is printed.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

from _common import bootstrap, load_settings  # noqa: F401

MEL = ZoneInfo("Australia/Melbourne")


def fmt_ms(ms):
    if not ms:
        return "not given"
    t = datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc)
    return f"{t.astimezone(MEL):%a %d %b %Y %H:%M} Melbourne ({t:%Y-%m-%d %H:%M} UTC)"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="spend the 1 credit")
    a = ap.parse_args()
    import os
    api_key = os.environ.get("FK_API_KEY", "")
    if not api_key:
        sys.exit("FK_API_KEY is not set")
    if not a.yes:
        sys.exit("costs 1 credit; pass --yes")
    settings, spec, costs, ledger = bootstrap("live")
    url = (settings.base_url or spec.base_url()).rstrip("/") + "/b2c/account/keys"
    resp = requests.post(url, json={"operation": "getAccountInfo", "apiKey": api_key},
                         headers={spec.api_key_header(): api_key, "Accept": "application/json"}, timeout=60)
    ledger.record("Get Account Info", 1, method="POST", path="/b2c/account/keys",
                  params={"operation": "getAccountInfo"}, http_status=resp.status_code)
    if resp.status_code != 200:
        sys.exit(f"HTTP {resp.status_code} from Form King (body not printed: an account response can carry the key)")
    d = resp.json()
    print(f"tier:                   {d.get('tier')}")
    print(f"active:                 {d.get('active')}")
    print(f"bundled balance:        {d.get('bundledBalance')}")
    print(f"top-up balance:         {d.get('topupBalance')}")
    print(f"pending bundled:        {d.get('pendingBundledBalance')}")
    print(f"period started:         {fmt_ms(d.get('bundledPeriodStart'))}")
    print(f"period ends (resets):   {fmt_ms(d.get('bundledPeriodEnd'))}")
    s = ledger.summary(None)
    print(f"our ledger says:        {s['balance']} (calendar month {s['month']})")


if __name__ == "__main__":
    main()
