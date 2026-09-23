"""Fit the real-price model (fk/realprice.py) on every stored race that carries a real
9am price and a result. Needs the database; a few seconds to run.

    python scripts/real_price_model.py [--state VIC] [--window morning|evening]
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fk import backtest as B  # noqa: E402
from fk import fields as F  # noqa: E402
from fk import realprice as R  # noqa: E402

# Two price windows, both fetched_at in UTC relative to race day:
#   morning: the morning odds job, about 23:15 UTC the day before (9:15am Melbourne), up to noon Melbourne
#   evening: the nightly pull the evening before, 06:00 to 14:00 UTC (4pm to midnight Melbourne), the
#            first price we ever see, closest to the opening price the back-test pays
WINDOWS = {"morning": (-1, 20, 0, 2), "evening": (-1, 6, -1, 14)}


def snapshot_prices(db, race_id: str, race_date: str, window: str = "morning", field: str = "price") -> dict[str, float]:
    """{horse_id: price} from the latest 'current' snapshot fetched in the window. `field` is
    the stored best price ('price') or the raw object's average price ('avgNow')."""
    d = datetime.fromisoformat(race_date[:10]).replace(tzinfo=timezone.utc)
    d0, h0, d1, h1 = WINDOWS[window]
    lo, hi = d + timedelta(days=d0, hours=h0), d + timedelta(days=d1, hours=h1)
    col = "price" if field == "price" else "raw->>'avgNow'"
    rows = db.conn.execute(
        f"""select distinct on (horse_id) horse_id, {col}
            from fk.odds_snapshots
            where race_id = %s and source = 'formking' and kind = 'current' and fetched_at between %s and %s
            order by horse_id, fetched_at desc""",
        (race_id, lo, hi),
    ).fetchall()
    out = {}
    for hid, v in rows:
        try:
            if v is not None and float(v) > 1:
                out[hid] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def real_price_rows(db, state: str = "VIC", window: str = "morning") -> tuple[list[dict], dict[str, dict[str, float]]]:
    """(resulted rows whose runners carry the real price, {race_id: {horse_id: price}})."""
    rows, prices = [], {}
    for row in db.resulted_races(state):
        active = [e for e in row["entries"] if not F.entry_scratched(e)]
        p = snapshot_prices(db, row["race_id"], row["date"], window)
        have = sum(1 for e in active if F.horse_id(e) in p)
        if active and have / len(active) >= R.MIN_PRICE_COVERAGE:
            rows.append(row)
            prices[row["race_id"]] = p
    return rows, prices


def priced_races(rows: list[dict], prices: dict[str, dict[str, float]]) -> list[B.Race]:
    """Races built with the real price as the market input and the opening average attached
    as its own feature, in row order; races without a BSP to fit against are dropped."""
    from backtest import races_from_rows
    orig, _ = races_from_rows(rows)
    orig_by_id = {r.race_id: r for r in orig}
    priced_rows = [{**r, "entries": [R.with_price(e, prices[r["race_id"]].get(F.horse_id(e))) for e in r["entries"]]} for r in rows]
    races, _ = races_from_rows(priced_rows)
    out = []
    for race in races:
        if race.race_id in orig_by_id and B.bsp_chances(race.runners):
            R.attach_opening_average(race.runners, orig_by_id[race.race_id].runners)
            out.append(race)
    return out


def fit_real_price_model(db, state: str = "VIC", window: str = "morning") -> dict | None:
    """{model, features, beta, ridge, races, from, to} or None when too few real-price races exist."""
    rows, prices = real_price_rows(db, state, window)
    races = priced_races(rows, prices)
    if len(races) < R.MIN_REAL_PRICE_RACES:
        print(f"real-price model: {len(races)} races carry a real {window} price, under the floor of {R.MIN_REAL_PRICE_RACES}; not fitted")
        return None
    beta = B.fit(races, R.REAL_PRICE_FEATURES, ridge=R.REAL_PRICE_RIDGE)
    days = sorted(r.date for r in races)
    return {"model": R.MODEL_LABEL, "features": R.REAL_PRICE_FEATURES, "beta": beta, "ridge": R.REAL_PRICE_RIDGE,
            "races": len(races), "from": days[0], "to": days[-1], "window": window}


def main() -> None:
    from _common import load_settings
    from fk.db import Db
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--window", choices=list(WINDOWS), default="morning")
    a = ap.parse_args()
    m = fit_real_price_model(Db(load_settings().database_url), a.state, a.window)
    if m:
        print(f"{m['model']}: {m['races']} races {m['from']} to {m['to']}, ridge {m['ridge']}")
        for k, v in sorted(m["beta"].items(), key=lambda kv: -abs(kv[1])):
            print(f"  {k:26} {v:+.3f}")


if __name__ == "__main__":
    main()
