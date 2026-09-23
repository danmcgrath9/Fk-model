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
    """{horse_id: best bookmaker price} from the latest 'current' snapshot fetched in the window."""
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


def average_prices(db: Db, race_id: str, race_date: str, window: str = "morning") -> dict[str, float]:
    """{horse_id: AVERAGE bookmaker price} from the same snapshots: the raw odds object the
    morning job stored carries avgNow beside bestNow. The best of a dozen books is inflated
    on every runner by construction (whoever is longest wins the column), most of all on
    outsiders; the average is the books' consensus, and the fairer market to learn from,
    while the best price is still the one a bet is struck at."""
    d = datetime.fromisoformat(race_date[:10]).replace(tzinfo=timezone.utc)
    d0, h0, d1, h1 = WINDOWS[window]
    lo = d + timedelta(days=d0, hours=h0)
    hi = d + timedelta(days=d1, hours=h1)
    rows = db.conn.execute(
        """select distinct on (horse_id) horse_id, raw->>'avgNow'
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
        except ValueError:
            continue
    return out


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


def cull_long(probs: list[float], cap_price: float = 50.0, keep: float = 0.5) -> list[float]:
    """The founder's question: a runner rated at `cap_price` or longer keeps only `keep` of its
    chance and the rest is handed back to the field, pro rata. Never zero: BSP gives every
    runner some chance, and a zero on the one that wins scores as infinitely wrong.
    Hand-checked: [0.6, 0.38, 0.02] at $50, keep 0.5 -> the 2% runner keeps 1%, the other 1%
    goes 0.6/0.98 and 0.38/0.98 of the way, so [0.6061, 0.3839, 0.01]."""
    long = [p < 1.0 / cap_price for p in probs]
    freed = sum(p * (1 - keep) for p, l in zip(probs, long) if l)
    rest = sum(p for p, l in zip(probs, long) if not l)
    if not freed or rest <= 0:
        return list(probs)
    return [p * keep if l else p + freed * p / rest for p, l in zip(probs, long)]


def kl_to_bsp(probs: list[float], race) -> float:
    q = B.bsp_chances(race.runners)
    return sum(qi * math.log(qi / max(pi, 1e-12)) for qi, pi in zip(q, probs) if qi > 0)


GRID_A = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
GRID_B = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0, 1.3, 1.6, 2.0]
# Ridge strengths tried when the deployed features are refitted on the real-price races
# themselves: a few dozen races and fifty-odd features need a heavy hand, so every strength
# is reported rather than one picked quietly.
REFIT_RIDGES = [0.1, 1.0, 10.0]
# A small model for the same job: the market plus the handful of form figures that carry the
# most weight in the big fit. Fewer coefficients, so a small sample can actually pin them.
# One definition of the compact set and the two average-price features: fk/realprice.py,
# which the live paper book prices with.
from fk.realprice import AVG_NOW_FEATURE, AVG_OPEN_FEATURE, COMPACT_FEATURES  # noqa: E402


def fit_blend(days: dict[str, list[tuple[list[float], list[float], object]]]) -> tuple[float, float]:
    """(a, b) minimising KL to BSP over every race; days -> [(form scores, market, race)]."""
    best, best_kl = (1.0, 0.0), float("inf")
    for a in GRID_A:
        for b in GRID_B:
            kl = sum(kl_to_bsp(blend_probs(sc, mk, a, b), race) for rs in days.values() for sc, mk, race in rs)
            if kl < best_kl:
                best, best_kl = (a, b), kl
    return best


def form_plus_price(train, test, feats_form: list[str], ridge: float, target=B.bsp_chances) -> tuple[float, tuple[float, float], list[list[float]]]:
    """A form-only model (no market input, so nothing learned from the soft opening average),
    blended with the REAL price: chance ~ exp(a log(price chance) + b form score). a and b
    are the only things learned from the real-price races, leave-one-day-out, so every race
    is scored by weights that never saw its day. Returns (mean KL to BSP, (a, b) on all days,
    the blend's chances per test race in test order)."""
    beta = B.fit(train, feats_form, ridge=ridge, target=target)
    scores = [[sum(beta.get(k, 0.0) * r.x.get(k, 0.0) for k in feats_form) for r in race.runners] for race in test]
    return blend_scores(test, scores)


def blend_scores(test, scores: list[list[float]]) -> tuple[float, tuple[float, float], list[list[float]]]:
    """Blend any per-runner score with the real price, weights learned leave-one-day-out."""
    days: dict[str, list] = {}
    for idx, race in enumerate(test):
        sc = scores[idx]
        mk = B.market_probs([race])[0]
        days.setdefault(race.date, []).append((sc, mk, race, idx))
    total, n = 0.0, 0
    out: list[list[float]] = [[] for _ in test]
    for d in days:
        a, b = fit_blend({k: [t[:3] for t in v] for k, v in days.items() if k != d})
        for sc, mk, race, idx in days[d]:
            out[idx] = blend_probs(sc, mk, a, b)
            total += kl_to_bsp(out[idx], race)
            n += 1
    return total / max(n, 1), fit_blend({k: [t[:3] for t in v] for k, v in days.items()}), out


def day_blocks(races, folds: int = 5) -> list[list[int]]:
    """Indices of `races` cut into `folds` blocks of consecutive DAYS, a day never split, so
    a race is never priced by a fit that saw another race from the same afternoon."""
    days = sorted({r.date for r in races})
    n = len(days)
    groups = [days[i * n // folds:(i + 1) * n // folds] for i in range(folds)]
    return [[i for i, r in enumerate(races) if r.date in set(g)] for g in groups if g]


def refit_on_real(test, feats: list[str], ridges: list[float] = REFIT_RIDGES) -> list[tuple[float, float, list[list[float]]]]:
    """The deployed feature set fitted on the real-price races THEMSELVES, so the market
    coefficient is learned against the price we actually bet at rather than the soft opening
    average. Five blocks of whole days: each block is priced by a fit on the other four.
    Returns [(ridge, mean KL to BSP, chances per test race)] for every ridge, because
    picking the best of three on this sample and reporting only it would flatter it."""
    rows = []
    blocks = day_blocks(test)
    for ridge in ridges:
        probs: list[list[float]] = [[] for _ in test]
        for block in blocks:
            hold = set(block)
            train = [r for i, r in enumerate(test) if i not in hold]
            if not train:
                continue
            beta = B.fit(train, feats, ridge=ridge)
            for i in block:
                probs[i] = B.predict(beta, test[i].runners)
        scored = [(p, r) for p, r in zip(probs, test) if p]
        kl = sum(kl_to_bsp(p, r) for p, r in scored) / max(len(scored), 1)
        rows.append((ridge, kl, probs))
    return rows


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
    test_rows, morning, averages = [], {}, {}
    for row in rows:
        active = [e for e in row["entries"] if not F.entry_scratched(e)]
        prices = morning_prices(db, row["race_id"], row["date"], a.window)
        have = sum(1 for e in active if F.horse_id(e) in prices)
        if active and have / len(active) >= 0.8:
            test_rows.append(row)
            morning[row["race_id"]] = prices
            averages[row["race_id"]] = average_prices(db, row["race_id"], row["date"], a.window)
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
    # The opening average as the market input, the way the model was trained: its chances are
    # a score to blend with the real price, and its logit a feature the refit may use BESIDE
    # the real price (the founder's call: train on the opening price and the 9am price).
    orig, _ = races_from_rows(test_rows)
    orig_by_id = {r.race_id: r for r in orig}
    # And the AVERAGE bookmaker price as the market input: the consensus rather than the best.
    avg_rows = [{**r, "entries": [with_price(e, averages[r["race_id"]].get(F.horse_id(e))) for e in r["entries"]]} for r in test_rows]
    avg_races, _ = races_from_rows(avg_rows)
    avg_by_id = {r.race_id: r for r in avg_races}
    avg_cover = sum(len(averages[r["race_id"]]) for r in test_rows) / max(1, sum(len(morning[r["race_id"]]) for r in test_rows))
    # Test races: the model's market input IS the morning price, as live.
    test_rows = [{**r, "entries": [with_price(e, morning[r["race_id"]].get(F.horse_id(e))) for e in r["entries"]]} for r in test_rows]
    test, _ = races_from_rows(test_rows)
    test = [r for r in test if B.bsp_chances(r.runners) and r.race_id in orig_by_id and r.race_id in avg_by_id]
    opening_scores, avg_market = [], []
    for race in test:
        o = orig_by_id[race.race_id]
        by_horse = {r.horse_id: r for r in o.runners}
        av = {r.horse_id: r for r in avg_by_id[race.race_id].runners}
        for r in race.runners:
            r.x[AVG_OPEN_FEATURE] = by_horse[r.horse_id].x.get(B.MARKET_FEATURE, 0.0) if r.horse_id in by_horse else 0.0
            r.x[AVG_NOW_FEATURE] = av[r.horse_id].x.get(B.MARKET_FEATURE, r.x.get(B.MARKET_FEATURE, 0.0)) if r.horse_id in av else r.x.get(B.MARKET_FEATURE, 0.0)
        opening_scores.append([math.log(max(p, 1e-9)) for p in B.predict(beta, [by_horse.get(r.horse_id, r) for r in race.runners])])
        avg_market.append(B.softmax([r.x[AVG_NOW_FEATURE] for r in race.runners]))
    probs = [B.predict(beta, r.runners) for r in test]
    market = B.market_probs(test)
    ours = B.score(probs, test)
    mkt = B.score(market, test)
    print(f"\nKL to Betfair SP on these races: {label} market {mkt.kl_to_bsp:.4f}, our model {ours.kl_to_bsp:.4f} "
          f"({'BEATS the ' + label + ' market' if ours.kl_to_bsp < mkt.kl_to_bsp else 'does NOT beat the ' + label + ' market'})")
    # The market two ways: the BEST bookmaker price (what a bet is struck at, inflated on
    # outsiders by construction) and the AVERAGE bookmaker price (the books' consensus).
    avg_score = B.score(avg_market, test)
    print(f"The same {label} market read from the AVERAGE bookmaker price instead of the best: {avg_score.kl_to_bsp:.4f} "
          f"({'sharper' if avg_score.kl_to_bsp < mkt.kl_to_bsp else 'not sharper'} than the best price; average prices cover {avg_cover:.0%} of the priced runners)")
    # The fair contender: form fitted without the market, blended with the real price.
    form_feats = [f for f in feats if f not in (B.MARKET_FEATURE, "market_prob", "market_x_neural", "first_starter_x_market")]
    blend_kl, (ba, bb), blend_pr = form_plus_price(train, test, form_feats, ridge)
    verdict = "BEATS" if blend_kl < mkt.kl_to_bsp else "does NOT beat"
    print(f"Form-only model blended with the real {label} price (weights learned leave-one-day-out): {blend_kl:.4f} "
          f"({verdict} the {label} market; on all days the blend is {ba:.2f} x market + {bb:.2f} x form)")
    contenders = [("blend", blend_pr)]
    # The same blend with the form model fitted to WINNERS rather than to the close. A model
    # taught to copy the close can at best equal the market; one taught to be right about who
    # won is noisier but is the only kind that can carry something the price does not.
    win_kl, (wa, wb), win_pr = form_plus_price(train, test, form_feats, ridge, target=B.winner_chances)
    verdict = "BEATS" if win_kl < mkt.kl_to_bsp else "does NOT beat"
    print(f"Form fitted to winners, blended with the real {label} price: {win_kl:.4f} "
          f"({verdict} the {label} market; {wa:.2f} x market + {wb:.2f} x form)")
    contenders.append(("winners blend", win_pr))
    # The deployed model as trained (opening average inside it), blended with the real price.
    op_kl, (oa, ob), op_pr = blend_scores(test, opening_scores)
    verdict = "BEATS" if op_kl < mkt.kl_to_bsp else "does NOT beat"
    print(f"Deployed model (opening average inside it) blended with the real {label} price: {op_kl:.4f} "
          f"({verdict} the {label} market; {oa:.2f} x market + {ob:.2f} x model)")
    contenders.append(("opening+9am blend", op_pr))
    # The consensus price as the model, bets struck at the best price: the plainest edge there
    # is, if it exists, is a best price standing further from the consensus than usual.
    contenders.append(("average price", avg_market))
    av_kl, (va, vb), av_pr = blend_scores(test, [[math.log(max(p, 1e-9)) for p in pr] for pr in avg_market])
    print(f"Average price blended with the best price: {av_kl:.4f} ({'BEATS' if av_kl < mkt.kl_to_bsp else 'does NOT beat'} the best-price market; "
          f"{va:.2f} x best + {vb:.2f} x average)")
    contenders.append(("average+best blend", av_pr))
    # The deployed features, and a compact set, refitted on the real-price races themselves.
    print(f"\nRefitted on the real-price races (five blocks of whole days, each priced by the other four):")
    print("| model | ridge | KL to BSP | vs the market |")
    print("|---|---|---|---|")
    best_kl = float("inf")
    for name, fs in (("deployed features", feats), ("deployed + opening average", feats + [AVG_OPEN_FEATURE]),
                     ("compact", COMPACT_FEATURES), ("compact + opening average", COMPACT_FEATURES + [AVG_OPEN_FEATURE]),
                     ("compact + average price", COMPACT_FEATURES + [AVG_NOW_FEATURE]),
                     ("compact + both averages", COMPACT_FEATURES + [AVG_OPEN_FEATURE, AVG_NOW_FEATURE])):
        for rg, kl, pr in refit_on_real(test, fs):
            print(f"| {name} | {rg:g} | {kl:.4f} | {'beats it' if kl < mkt.kl_to_bsp else 'does not'} |")
            if kl < best_kl:
                best_kl, best_name, best_pr = kl, f"refit {name} r{rg:g}", pr
    contenders.append((best_name, best_pr))
    print(f"The best of those, '{best_name}', is chosen on this same sample, so its figure flatters it a little.")

    # The founder's question (23 Sep): if a runner we rate $50 or longer gives its chance back to
    # the field, are we closer to BSP? Scored for the market itself and for each model.
    print(f"\nIf every runner rated $50 or longer hands back part of its chance to the rest of the field (KL to BSP, {label} market {mkt.kl_to_bsp:.4f}):")
    print("| chances | as they are | long shots keep half | keep a quarter | keep a tenth |")
    print("|---|---|---|---|---|")
    for name, pr_set in [(f"the {label} market", market), ("our model as deployed", probs)] + [(f"[{n}]", p) for n, p in contenders if n.startswith("refit") or n == "blend"]:
        cells = []
        for keep in (1.0, 0.5, 0.25, 0.1):
            kl = sum(kl_to_bsp(cull_long(pr, 50.0, keep), race) for pr, race in zip(pr_set, test) if pr) / max(1, sum(1 for pr in pr_set if pr))
            cells.append(f"{kl:.4f}")
        print(f"| {name} | " + " | ".join(cells) + " |")

    # Every method, paid at the struck (9am) price and at BSP. The deployed model's methods
    # carry no prefix; the contenders that beat or approach the market are prefixed so the
    # same rule can be read side by side.
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
    # The founder's cap: drop any runner WE rate at $50 or longer, and the shorter caps beside
    # it, on the value rule, so the table shows what a cap costs and saves at the real price.
    RATED_CAPS = (10, 15, 20, 30, 50)
    def add_capped(prefix, model_probs, thresholds):
        for race, pr, mk in zip(test, model_probs, market):
            if not pr:
                continue
            for r, pi, mi in zip(race.runners, pr, mk):
                price = r.raw.get("open")
                if not price or price <= 1 or not pi or pi > 3.0 * mi:
                    continue
                rated = 1.0 / pi
                ev = pi * price - 1.0
                for cap in RATED_CAPS:
                    for t in thresholds:
                        if rated < cap and ev > t:
                            add(f"{prefix}value {int(t * 100)}c+, rated under ${cap}, 1u", 1.0, price, r.finish == 1, r.bsp)
    add_capped("", probs, (0.05, 0.20))
    # The contenders: the same core rules from each model that was fitted against the real price.
    for prefix, model_probs in contenders:
        if prefix.startswith("refit"):
            add_capped(f"[{prefix}] ", model_probs, (0.05, 0.10))
        for race, pr, mk in zip(test, model_probs, market):
            if not pr:
                continue
            top = max(range(len(pr)), key=lambda i: pr[i])
            for i, (r, pi, mi) in enumerate(zip(race.runners, pr, mk)):
                price = r.raw.get("open")
                if not price or price <= 1:
                    continue
                won, bsp = r.finish == 1, r.bsp
                ev = pi * price - 1.0
                if i == top:
                    add(f"[{prefix}] top pick, 1u", 1.0, price, won, bsp)
                for t in (0.03, 0.05, 0.10, 0.20):
                    if pi <= 3.0 * mi and ev > t:
                        add(f"[{prefix}] value {int(t * 100)}c+, 1u", 1.0, price, won, bsp)
                        add(f"[{prefix}] value {int(t * 100)}c+, quarter Kelly", P.kelly_stake(pi, price), price, won, bsp)
    print(f"\n| method | bets | winners | staked | at the {label} price: returned | return | at BSP: returned | return |")
    print("|---|---|---|---|---|---|---|---|")
    for name, m in sorted(methods.items(), key=lambda kv: -sum(kv[1]['st'])):
        st, rs, roi_s, se_s = roi_se(m["struck"], m["st"])
        _, rb, roi_b, se_b = roi_se(m["bsp"], m["st"])
        print(f"| {name} | {len(m['st'])} | {m['w']} | {st:.1f} | {rs:.1f} | {roi_s:+.1%} ±{se_s:.0%} | {rb:.1f} | {roi_b:+.1%} ±{se_b:.0%} |")
    print("\nOne unit = 1. '±' is one standard error: inside about two of it is luck. No deductions or commission taken off.")


if __name__ == "__main__":
    main()
