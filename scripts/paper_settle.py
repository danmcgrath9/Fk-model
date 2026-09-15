"""Settle the paper book: every open bet whose race now has a result is settled at Betfair
SP (else starting price). No Form King calls.

    python scripts/paper_settle.py
"""
from __future__ import annotations

from _common import load_settings
from fk import paper as P
from fk.db import Db


def main() -> None:
    db = Db(load_settings().database_url)
    db.ensure_paper_book()
    n = winners = 0
    for b in db.open_paper_bets_with_results():
        won = b["finish"] == 1
        price = b["bsp"] if b["bsp"] else b["sp"]
        db.settle_paper_bet(b["bet_id"], price, b["finish"], won, P.settle(b["stake"], won, price))
        n += 1
        winners += 1 if won else 0
    db.conn.commit()
    print(f"settled {n} paper bets, {winners} winners")


if __name__ == "__main__":
    main()
