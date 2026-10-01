"""Late scratchings and the bookmaker deduction they cause, per race, for a day and track.

python scripts/scratch_report.py --date 2026-10-01 --track Warrnambool [--track Flemington ...]

A runner counts as scratched when it has a stored price for the race and either carries
scratched=true, has no entry any more (a re-pull drops runners Race Form no longer lists),
or is missing from the results of a run race. An emergency that never gained a start was
never in the field and causes no deduction, so it is listed but not counted. The deduction
is fk.paper.deduction_for over the counted runners' last fixed price. Prints CSV between
CSV-BEGIN and CSV-END. Reads the database only: no Form King calls.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fk import paper as P  # noqa: E402
from fk.config import load_settings  # noqa: E402
from fk.pg import connect  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--track", action="append", required=True)
    a = ap.parse_args()
    conn = connect(load_settings().database_url)
    out = ["track,race,horse,emergency,status,opening,last_price,counts,race_deduction"]
    for track in a.track:
        races = conn.execute(
            """select r.race_id, r.race_number from fk.races r join fk.meetings m using (meeting_id)
               where m.meeting_date = %s and lower(m.track) = lower(%s) order by r.race_number""",
            (a.date, track)).fetchall()
        for race_id, rn in races:
            ents = {h: (bool(s), raw or {}) for h, s, raw in conn.execute(
                "select horse_id, scratched, raw from fk.entries where race_id = %s", (race_id,)).fetchall()}
            ran = {r[0] for r in conn.execute("select horse_id from fk.results where race_id = %s", (race_id,)).fetchall()}
            odds = {}
            for h, kind, price in conn.execute(
                    """select distinct on (horse_id, kind) horse_id, kind, price from fk.odds_snapshots
                       where race_id = %s order by horse_id, kind, observed_at desc""", (race_id,)).fetchall():
                odds.setdefault(h, {})[kind] = float(price)
            names = dict(conn.execute("select horse_id, name from fk.horses where horse_id = any(%s)",
                                      (list(set(odds) | set(ents)),)).fetchall())
            rows = []
            for h in sorted(set(odds) | set(ents)):
                scratched, raw = ents.get(h, (None, {}))
                if h not in ents:
                    status = "dropped from field"
                elif scratched:
                    status = "scratched"
                elif ran and h not in ran:
                    status = "did not run"
                else:
                    continue
                emerg = raw.get("emergency")
                counts = emerg is not True
                rows.append((names.get(h, h), emerg, status, odds.get(h, {}).get("opening"), odds.get(h, {}).get("current"), counts))
            ded = P.deduction_for([r[4] for r in rows if r[5]])
            for n, e, s, o, c, k in rows:
                out.append(f"{track},{rn},{n},{'' if e is None else e},{s},{o or ''},{c or ''},{k},{ded:.3f}")
            print(f"{track} R{rn}: {len(rows)} not running ({sum(1 for r in rows if r[5])} counted), deduction {ded:.0%}")
    print("CSV-BEGIN"); print("\n".join(out)); print("CSV-END")


if __name__ == "__main__":
    main()
