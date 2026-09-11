"""Credit ledger CLI.

  python scripts/ledger.py show            this month's summary and rows
  python scripts/ledger.py show --month 2026-09
  python scripts/ledger.py reconcile --site-used 412 --note "usage tab 12 Sep 09:10"
      Compares Form King's reported usage with ours and writes ONE adjustment row for the
      difference, so the balance matches the site. If they differ, the ledger was wrong:
      find out why (a cost in credits.yaml, a failed call charged or not) before trusting it.
"""
from __future__ import annotations

import argparse

from _common import load_settings, open_ledger


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("--month")
    s.add_argument("--limit", type=int, default=50)
    r = sub.add_parser("reconcile")
    r.add_argument("--site-used", type=int, required=True, help="credits used this month per the Form King usage tab")
    r.add_argument("--note", required=True)
    r.add_argument("--month")
    a = ap.parse_args()

    settings = load_settings()
    ledger = open_ledger(settings)
    if a.cmd == "show":
        summ = ledger.summary(a.month)
        print(f"month {summ['month']}: allowance {summ['allowance']}, spent {summ['spent']}, balance {summ['balance']}")
        for row in summ["by_operation"]:
            print(f"  {row['operation']:30} {row['key_kind']:6} calls {row['calls']:5} credits {row['credits']:7}")
        print()
        for row in ledger.rows(a.month, a.limit):
            bal = "" if row.balance_after is None else f" balance {row.balance_after}"
            print(f"{row.id:5} {row.ts} {row.key_kind:6} {row.operation:28} {row.credits:5} http={row.http_status}{bal} {row.params}")
    else:
        ours = ledger.spent(a.month)
        diff = a.site_used - ours
        if diff == 0:
            print(f"ledger agrees with the site: {ours} credits used")
            return
        ledger.adjust(diff, f"{a.note}: site {a.site_used}, ledger {ours}, adjusted by {diff:+}")
        print(f"ledger said {ours}, site says {a.site_used}: adjustment of {diff:+} recorded. Find the cause.")


if __name__ == "__main__":
    main()
