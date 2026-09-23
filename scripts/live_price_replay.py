"""Replay every betting method at the REAL race-morning prices we stored.

    python scripts/live_price_replay.py [--history history] [--state VIC]

The back-test pays bets at Form King's average opening price, which nobody can take. The
morning odds job has stored the actual price on offer at about 9am Melbourne for every
race it priced since the pipeline started, and those races have since run. So: fit the
deployed model on every resulted race that ran BEFORE the first race with a morning
price, then price the races that have one with that 9am price as the market input (the
same price the bet is struck at, exactly as the live book now does), and score every
rule at the struck price and at Betfair SP. Small sample, honest prices. Read-only.
"""
from __future__ import annotations

import argparse
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import load_settings  # noqa: E402
from fk import backtest as B  # noqa: E402
from fk import fields as F  # noqa: E402
from fk import paper as P  # noqa: E402
from fk.db import Db  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
# Two price windows, both fetched_at in UTC relative to race day:
#   morning: the morning odds job, about 23:15 UTC the day before (9:15am Melbourne), up to noon Melbourne
#   evening: the nightly pull the evening before, 06:00 to 14:00 UTC (4pm to midnight Melbourne), the
#            first price we ever see, closest to the opening price the back-test pays
WINDOWS = {"morning": (-1, 20, 0, 2), "evening": (-1, 6, -1, 14)}


def morning_prices(db: Db, race_id: str, race_date: str, window: str = "morning") -> dict[str, float]:
    """{horse_id: price} from the latest 'current' snapshot fetched in the window."""
    d = datetime.fromisoformat(race_date[:10]).replace(tzinfo=timezone.utc)
    d0, h0, d1, h1 = WINDOWS[window]
    lo = d + timedelta(days=d0, hours=h0)
    hi = d + timedelta(days=d1, hours=h1)
    rows = db.conn.execute(
        """select distinct on (horse_id) horse_id, price
           from fk.odds_snapshots
           where race_id = %s and source = 'formking' and kind = 'current' and fetched_at between %s and %s
           order by horse_id, fetched_at desc""",
        (race_id, lo, hi),
    ).fetchall()
    return {r[0]: float(r[1]) for r in rows if r[1] is not None and float(r[1]) > 1}


def with_price(e: dict, price: float | None) -> dict:
    if not price:
        return e
    odds = dict(e.get("odds") or {})
    odds["avgOpen"] = price
    return {**e, "odds": odds}


def roi_se(returns: list[float], stakes: list[float]) -> tuple[float, float, float, float]:
    """(staked, returned, roi, se of roi) with stakes weighted."""
    staked = sum(stakes)
    if staked <= 0:
        return 0.0, 0.0, 0.0, 0.0
    returned = sum(returns)
    prof = [r - s for r, s in zip(returns, stakes)]
    n = len(prof)
    mean = sum(prof) / n
    var = sum((p - mean) ** 2 for p in prof) / (n - 1) if n > 1 else 0.0
    se_total = math.sqrt(var * n)
    return staked, returned, returned / staked - 1, se_total / staked


def blend_probs(scores: list[float], market: list[float], a: float, b: float) -> list[float]:
    """chance_i proportional to exp(a * log(market_i) + b * score_i)."""
    z = [a * math.log(max(m, 1e-9)) + b * s for s, m in zip(scores, market)]
    mx = max(z)
    w = [math.exp(v - mx) for v in z]
    t = sum(w)
    return [v / t for v in w]


def kl_to_bsp(probs: list[float], race) -> float:
    q = B.bsp_chances(race.runners)
    return sum(qi * math.log(qi / max(pi, 1e-12)) for qi, pi in zip(q, probs) if qi > 0)


GRID_A = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
GRID_B = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.3, 1.6, 2.0]


def fit_blend(days: dict[str, list[tuple[list[float], list[float], object]]]) -> tuple[float, float]:
    """(a, b) minimising KL to BSP over every race; days -> [(form scores, market, race)]."""
    best, best_kl = (1.0, 0.0), float("inf")
    for a in GRID_A:
        for b in GRID_B:
            kl = sum(kl_to_bsp(blend_probs(sc, mk, a, b), race) for rs in days.values() for sc, mk, race in rs)
            if kl < best_kl:
                best, best_kl = (a, b), kl
    return best


def form_plus_price(train, test, feats_form: list[str], ridge: float) -> tuple[float, tuple[float, float]]:
    """A form-only model (no market input, so nothing learned from the soft opening average),
    blended with the REAL price: chance ~ exp(a log(price chance) + b form score). a and b
    are the only things learned from the real-price races, leave-one-day-out, so every race
    is scored by weights that never saw its day. Returns (mean KL to BSP, (a, b) on all days)."""
    beta = B.fit(train, feats_form, ridge=ridge)
    days: dict[str, list] = {}
    for race in test:
        sc = [sum(beta.get(k, 0.0) * race.runners[i].x.get(k, 0.0) for k in feats_form) for i in range(len(race.runners))]
        mk = B.market_probs([race])[0]
        days.setdefault(race.date, []).append((sc, mk, race))
    total, n = 0.0, 0
    for d in days:
        a, b = fit_blend({k: v for k, v in days.items() if k != d})
        for sc, mk, race in days[d]:
            total += kl_to_bsp(blend_probs(sc, mk, a, b), race)
            n += 1
    return total / max(n, 1), fit_blend(days)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--history", default=str(ROOT / "history"))
    ap.add_argument("--window", choices=list(WINDOWS), default="morning")
    a = ap.parse_args()
    import json
    from backtest import races_from_rows
    from fk import history as H
    model_cfg = json.load(open(ROOT / "config" / "rated_price.json"))
    feats, ridge = model_cfg["features"], float(model_cfg.get("ridge") or 1e-8)

    db = Db(load_settings().database_url)
    rows = db.resulted_races(a.state)
    # Which resulted races carry a real morning price for at least 80% of their runners.
    test_rows, morning = [], {}
    for row in rows:
        active = [e for e in row["entries"] if not F.entry_scratched(e)]
        prices = morning_prices(db, row["race_id"], row["date"], a.window)
        have = sum(1 for e in active if F.horse_id(e) in prices)
        if active and have / len(active) >= 0.8:
            test_rows.append(row)
            morning[row["race_id"]] = prices
    if not test_rows:
        print("no resulted race carries a morning price snapshot yet")
        return
    first_day = min(r["date"] for r in test_rows)
    test_ids = {r["race_id"] for r in test_rows}
    train_rows = [r for r in rows if r["race_id"] not in test_ids and r["date"] < first_day]
    train_rows += [r for r in H.resulted_races(Path(a.history), a.state, skip={r["race_id"] for r in rows}) if r["date"] < first_day]
    label = "9am" if a.window == "morning" else "evening-before"
    print(f"{len(test_rows)} races with a real {label} price ({first_day} on); model fitted on {len(train_rows)} earlier races")

    train, _ = races_from_rows(train_rows)
    train = [r for r in train if B.bsp_chances(r.runners)]
    beta = B.fit(train, feats, ridge=ridge)
    # Test races: the model's market input IS the morning price, as live.
    test_rows = [{**r, "entries": [with_price(e, morning[r["race_id"]].get(F.horse_id(e))) for e in r["entries"]]} for r in test_rows]
    test, _ = races_from_rows(test_rows)
    test = [r for r in test if B.bsp_chances(r.runners)]
    probs = [B.predict(beta, r.runners) for r in test]
    market = B.market_probs(test)
    ours = B.score(probs, test)
    mkt = B.score(market, test)
    print(f"\nKL to Betfair SP on these races: {label} market {mkt.kl_to_bsp:.4f}, our model {ours.kl_to_bsp:.4f} "
          f"({'BEATS the ' + label + ' market' if ours.kl_to_bsp < mkt.kl_to_bsp else 'does NOT beat the ' + label + ' market'})")
    # The fair contender: form fitted without the market, blended with the real price.
    form_feats = [f for f in feats if f not in (B.MARKET_FEATURE, "market_prob", "market_x_neural", "first_starter_x_market")]
    blend_kl, (ba, bb) = form_plus_price(train, test, form_feats, ridge)
    verdict = "BEATS" if blend_kl < mkt.kl_to_bsp else "does NOT beat"
    print(f"Form-only model blended with the real {label} price (weights learned leave-one-day-out): {blend_kl:.4f} "
          f"({verdict} the {label} market; on all days the blend is {ba:.1f} x market + {bb:.1f} x form)")

    # Every method, paid at the struck (9am) price and at BSP.
    methods = {}
    def add(name, stake, price, won, bsp):
        m = methods.setdefault(name, {"st": [], "struck": [], "bsp": [], "w": 0})
        m["st"].append(stake); m["w"] += 1 if won else 0
        m["struck"].append(stake * price if won else 0.0)
        m["bsp"].append(stake * (bsp if bsp and bsp > 1 else 1.0) if won else 0.0)
    for race, pr, mk in zip(test, probs, market):
        top = max(range(len(pr)), key=lambda i: pr[i])
        for i, (r, pi, mi) in enumerate(zip(race.runners, pr, mk)):
            price = r.raw.get("open")
            if not price or price <= 1:
                continue
            won, bsp = r.finish == 1, r.bsp
            ev = pi * price - 1.0
            guard = pi <= 3.0 * mi
            if i == top:
                add("top pick, 1u", 1.0, price, won, bsp)
                add("top pick, to win 1u", 1.0 / (price - 1), price, won, bsp)
            for t in (0.05, 0.10, 0.15, 0.20, 0.25, 0.35, 0.50):
                if guard and ev > t:
                    add(f"value {int(t * 100)}c+, 1u", 1.0, price, won, bsp)
                    add(f"value {int(t * 100)}c+, quarter Kelly", P.kelly_stake(pi, price), price, won, bsp)
            for g in (0.03, 0.05, 0.10):
                if guard and pi - mi > g:
                    add(f"gap {int(g * 100)} points, 1u", 1.0, price, won, bsp)
            if guard and ev > 0.05:
                add("tiered 1u/2u/3u by band", 3.0 if ev > 0.20 else 2.0 if ev > 0.10 else 1.0, price, won, bsp)
            if guard and ev > 0.20:
                for lo, hi, lab in ((0, 4, "<$4"), (4, 8, "$4-8"), (8, 16, "$8-16"), (16, 999, "$16+")):
                    if lo <= price < hi:
                        add(f"value 20c+, 1u, price {lab}", 1.0, price, won, bsp)
            k = P.kelly_stake(pi, price)
            if k > 0:
                add("quarter Kelly, every positive edge", k, price, won, bsp)
    print(f"\n| method | bets | winners | staked | at the {label} price: returned | return | at BSP: returned | return |")
    print("|---|---|---|---|---|---|---|---|")
    for name, m in sorted(methods.items(), key=lambda kv: -sum(kv[1]['st'])):
        st, rs, roi_s, se_s = roi_se(m["struck"], m["st"])
        _, rb, roi_b, se_b = roi_se(m["bsp"], m["st"])
        print(f"| {name} | {len(m['st'])} | {m['w']} | {st:.1f} | {rs:.1f} | {roi_s:+.1%} ±{se_s:.0%} | {rb:.1f} | {roi_b:+.1%} ±{se_b:.0%} |")
    print("\nOne unit = 1. '±' is one standard error: inside about two of it is luck. No deductions or commission taken off.")


if __name__ == "__main__":
    main()
