"""The FORM-ONLY price: Form King's inputs and nothing from today's market, so a race can be
priced before any book opens (the evening before, or a meeting whose market has not formed).

    python scripts/fit_form_only.py [--state VIC] [--history history] [--out config/form_price.json]

Every other model this repo deploys carries today's price as an input, which is why its
rated price sits within a few per cent of the market: it IS the market, nudged by form. This
one is barred from every feature built from today's price (open_logit, market_prob,
market_x_neural, first_starter_x_market) and from the quarantined leaky ones (EXP, the
collateral form). What it may use is everything Form King publishes about the horse, the
race and the connections, plus what the market thought of the horse's PAST runs (settled
before today, so not leakage).

It is still fitted to Betfair SP, the best estimate of each runner's true chance we hold,
so it learns how much each form figure is worth in the market's own currency.

Honest scoring: candidate sets and the ridge are chosen on the older 70% of racing (its
newest fifth held out for the choice), the winner is judged ONCE on the newer 30% it never
saw, beside the opening market on the same races, and split by whether the race was pulled
before the jump (a figure that only helps back-filled races is reading the future). Then it
is refitted on everything and written to config/form_price.json for the report build.

The fit is fk.backtest.fit's objective (conditional logit, Newton, ridge added to the
gradient and Hessian as there) vectorised with numpy, because the pure-Python fit takes
minutes per candidate on 3,500 races; tests/test_fit_form_only.py holds the two equal.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fk import backtest as B  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "config" / "form_price.json"
TRAIN_SHARE = 0.7
RIDGES = [0.1, 1.0, 10.0, 30.0]

# Built from TODAY'S price, or quarantined as leaky: never in a form-only model.
BARRED = {B.MARKET_FEATURE, "market_prob", "market_x_neural", "first_starter_x_market"} | set(B.NON_DEPLOYABLE)
EXPERIENCE_FORM = [f for f in B.EXPERIENCE if f not in BARRED]
CANDIDATES = {
    "form_kitchen_sink": B.MODEL_SETS["kitchen_sink"],
    "form_kitchen_sink_experience": B.MODEL_SETS["kitchen_sink"] + EXPERIENCE_FORM,
    "form_kitchen_sink_memory": B.MODEL_SETS["kitchen_sink"] + EXPERIENCE_FORM + B.MARKET_MEMORY,
    "form_kitchen_sink_memory_intent": B.MODEL_SETS["kitchen_sink"] + EXPERIENCE_FORM + B.MARKET_MEMORY + B.INTENT,
}
for _name, _feats in CANDIDATES.items():
    assert not BARRED & set(_feats), f"{_name} carries a barred feature: {BARRED & set(_feats)}"


class Stack:
    """The races as one flat matrix, runners in race order, for the vectorised fit."""

    def __init__(self, races: list[B.Race], features: list[str]):
        xs, qs, sizes = [], [], []
        for race in races:
            q = B.bsp_chances(race.runners)
            if q is None:
                continue
            xs.extend([[r.x.get(f, 0.0) for f in features] for r in race.runners])
            qs.extend(q)
            sizes.append(len(race.runners))
        self.X = np.asarray(xs, dtype=float).reshape(-1, len(features))
        self.q = np.asarray(qs, dtype=float)
        self.starts = np.concatenate([[0], np.cumsum(sizes)[:-1]]).astype(int)
        self.idx = np.repeat(np.arange(len(sizes)), sizes)

    def probs(self, beta: np.ndarray) -> np.ndarray:
        s = self.X @ beta
        s = s - np.maximum.reduceat(s, self.starts)[self.idx]
        w = np.exp(s)
        return w / np.add.reduceat(w, self.starts)[self.idx]


def fit_np(races: list[B.Race], features: list[str], ridge: float, iterations: int = 60) -> dict[str, float]:
    st = Stack(races, features)
    if not len(st.starts):
        raise ValueError("no race with a Betfair SP to fit against")
    d = len(features)
    beta = np.zeros(d)
    for _ in range(iterations):
        p = st.probs(beta)
        g = st.X.T @ (p - st.q) + ridge * beta
        xbar = np.add.reduceat(st.X * p[:, None], st.starts)[st.idx]
        D = st.X - xbar
        H = (D * p[:, None]).T @ D + ridge * np.eye(d)
        step = np.linalg.solve(H, -g)
        beta = beta + step
        if np.max(np.abs(step)) < 1e-9:
            break
    return dict(zip(features, beta.tolist()))


def kl(beta: dict[str, float], races: list[B.Race]) -> float:
    return B.score([B.predict(beta, r.runners) for r in races], races).kl_to_bsp


def split_by_date(races: list[B.Race], share: float) -> tuple[list[B.Race], list[B.Race]]:
    ordered = sorted(races, key=lambda r: (r.date, r.race_id))
    cut = min(int(len(ordered) * share), len(ordered) - 1)
    day = ordered[cut].date
    return [r for r in ordered if r.date < day], [r for r in ordered if r.date >= day]


def choose(train: list[B.Race]) -> tuple[str, float, list[tuple[str, float, float]]]:
    """The candidate set and ridge closest to BSP on the newest fifth of the training races,
    fitted on the rest of them. The test races take no part in the choice."""
    inner, valid = split_by_date(train, 0.8)
    table, best = [], None
    for name, feats in CANDIDATES.items():
        for ridge in RIDGES:
            v = kl(fit_np(inner, feats, ridge), valid)
            table.append((name, ridge, v))
            if best is None or v < best[2]:
                best = (name, ridge, v)
    return best[0], best[1], table


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--history", default=str(ROOT / "history"))
    ap.add_argument("--out", default=str(OUT_PATH))
    a = ap.parse_args()
    from backtest import load_races
    races, _ = load_races(a.state, Path(a.history))
    races = [r for r in races if B.bsp_chances(r.runners)]
    train, test = split_by_date(races, TRAIN_SHARE)
    print(f"{len(races)} races with a Betfair SP; choosing on the older {len(train)} ({train[0].date} to {train[-1].date}), "
          f"judged once on the newer {len(test)} ({test[0].date} to {test[-1].date}).\n")

    name, ridge, table = choose(train)
    print("Choice (fitted on the older four fifths of the training races, scored on its newest fifth):\n")
    print("| set | features | ridge | KL to BSP |")
    print("|---|---|---|---|")
    for n, r, v in table:
        print(f"| {n}{' **chosen**' if (n, r) == (name, ridge) else ''} | {len(CANDIDATES[n])} | {r:g} | {v:.4f} |")

    feats = CANDIDATES[name]
    beta = fit_np(train, feats, ridge)
    form_kl = kl(beta, test)
    mkt_kl = B.score(B.market_probs(test), test).kl_to_bsp
    neural_kl = kl(fit_np(train, B.NEURAL, ridge), test)
    top = B.score([B.predict(beta, r.runners) for r in test], test).winner_top_rated
    mkt_top = B.score(B.market_probs(test), test).winner_top_rated
    print(f"\nOn the {len(test)} newer races it never saw (KL to BSP, lower is sharper; 0 would be BSP itself):\n")
    print("| price | KL to BSP | top pick won |")
    print("|---|---|---|")
    print(f"| Neural rating alone | {neural_kl:.4f} | |")
    print(f"| form-only model ({name}) | {form_kl:.4f} | {top:.1%} |")
    print(f"| Form King's opening average (a market) | {mkt_kl:.4f} | {mkt_top:.1%} |")

    leak = {}
    try:
        from _common import load_settings
        from fk.db import Db
        pre = Db(load_settings().database_url).races_pulled_before_the_jump(a.state)
        before = [r for r in test if r.race_id in pre]
        after = [r for r in test if r.race_id not in pre]
        print(f"\nLeakage check: pulled before the jump {len(before)}, back-filled {len(after)}. "
              "A form figure that only helps the back-filled races is reading the future.\n")
        print("| races | form-only KL | market KL | gap |")
        print("|---|---|---|---|")
        for label, subset in (("pulled before the jump", before), ("back-filled", after)):
            if len(subset) < 20:
                print(f"| {label} | too few ({len(subset)}) | | |")
                continue
            f_, m_ = kl(beta, subset), B.score(B.market_probs(subset), subset).kl_to_bsp
            leak[label] = {"races": len(subset), "form_kl": round(f_, 4), "market_kl": round(m_, 4)}
            print(f"| {label} ({len(subset)}) | {f_:.4f} | {m_:.4f} | {f_ - m_:+.4f} |")
    except Exception as ex:  # noqa: BLE001
        print(f"\nleakage check skipped: {type(ex).__name__}: {ex}")

    final = fit_np(races, feats, ridge)
    ordered = sorted(races, key=lambda r: r.date)
    model = {
        "model": name, "features": feats, "beta": final, "ridge": ridge, "races": len(races),
        "from": str(ordered[0].date), "to": str(ordered[-1].date),
        "fitted_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "out_of_sample": {"test_races": len(test), "form_kl": round(form_kl, 4), "market_kl": round(mkt_kl, 4),
                          "neural_only_kl": round(neural_kl, 4), "top_pick_won": round(top, 4),
                          "market_top_pick_won": round(mkt_top, 4), "leakage": leak},
    }
    Path(a.out).write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {a.out}: {name}, ridge {ridge:g}, refitted on all {len(races)} races ({model['from']} to {model['to']})")
    for f, b in sorted(final.items(), key=lambda kv: -abs(kv[1]))[:12]:
        print(f"  {f:28s} {b:+.3f}")


if __name__ == "__main__":
    main()
