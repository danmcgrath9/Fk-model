"""Betfair SP and finish for every paper bet in the given CSVs (race_id + horse), from stored
results. Prints CSV between CSV-BEGIN and CSV-END. Reads the database only: no Form King calls.

    python scripts/bsp_for.py data/live_bets/2026-10-01-warrnambool-bets-open.csv [...]
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fk import fields as F  # noqa: E402
from fk.config import load_settings  # noqa: E402
from fk.pg import connect  # noqa: E402

norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower())  # noqa: E731


def main() -> None:
    conn = connect(load_settings().database_url)
    want = {}
    for p in sys.argv[1:]:
        for r in csv.DictReader(open(p)):
            want.setdefault(r["race_id"], set()).add(norm(r["horse"]))
    print("CSV-BEGIN\nrace_id,horse,finish,bsp")
    for rid, horses in sorted(want.items()):
        rows = conn.execute("""select h.name, r.finish_position, r.raw from fk.results r join fk.horses h using (horse_id)
                               where r.race_id = %s""", (rid,)).fetchall()
        for name, fin, raw in rows:
            if norm(name) in horses:
                bsp = F.result_betfair_sp(raw or {})
                print(f"{rid},{name},{fin if fin is not None else ''},{bsp if bsp else ''}")
    print("CSV-END")


if __name__ == "__main__":
    main()
