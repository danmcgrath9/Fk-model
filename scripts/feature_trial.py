"""A quick trial of a feature group or a model shape, out of sample, without the two-hour
back-test: fit on the older 70% of stored racing, score on the newer 30%.

    python scripts/feature_trial.py [--state VIC] [--history history] [--ridge 1.0]

Read-only, no Form King calls. Prints KL to Betfair SP for the opening market, the deployed
set, the deployed set plus HISTORY, HISTORY plus the market alone, and a gradient-boosted
tree model over the same columns when scikit-learn is installed, so a different SHAPE of
model is tried beside a different set of inputs. Everything is judged against the opening
average, which is a phantom price nobody can take: this says which inputs carry
information the price does not, never that a bet at that price would pay.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import load_settings  # noqa: E402
from fk import backtest as B  # noqa: E402
from fk.db import Db  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TRAIN_SHARE = 0.7


def split_by_date(races: list[B.Race], share: float = TRAIN_SHARE) -> tuple[list[B.Race], list[B.Race]]:
    ordered = sorted(races, key=lambda r: (r.date, r.race_id))
    cut = int(len(ordered) * share)
    # never split a day
    day = ordered[cut].date if cut < len(ordered) else None
    train = [r for r in ordered if r.date < day] if day else ordered
    test = [r for r in ordered if day and r.date >= day]
    return train, test


def logit_trial(train, test, features: list[str], ridge: float) -> float:
    beta = B.fit(train, features, ridge=ridge)
    return B.score([B.predict(beta, r.runners) for r in test], test).kl_to_bsp


def tree_trial(train, test, features: list[str]) -> float | None:
    """A gradient-boosted tree over the same within-race columns, fitted to the BSP-implied
    chance (each runner twice, as a 'win' weighted q and a 'lose' weighted 1 - q), then the
    predicted odds normalised within the race. None when scikit-learn is not installed."""
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier
    except ImportError:
        return None
    X, y, w = [], [], []
    for race in train:
        q = B.bsp_chances(race.runners)
        if not q:
            continue
        for r, qi in zip(race.runners, q):
            row = [r.x.get(f, 0.0) for f in features]
            X.append(row); y.append(1); w.append(qi)
            X.append(row); y.append(0); w.append(1.0 - qi)
    model = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=40,
                                           l2_regularization=1.0, random_state=7)
    model.fit(X, y, sample_weight=w)
    probs = []
    for race in test:
        p = model.predict_proba([[r.x.get(f, 0.0) for f in features] for r in race.runners])[:, 1]
        odds = [max(pi, 1e-6) / max(1 - pi, 1e-6) for pi in p]
        t = sum(odds)
        probs.append([o / t for o in odds])
    return B.score(probs, test).kl_to_bsp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--history", default=str(ROOT / "history"))
    ap.add_argument("--ridge", type=float, default=1.0)
    ap.add_argument("--trees", action="store_true", help="also fit the gradient-boosted trees (scored worse on 23 Sep; off by default)")
    a = ap.parse_args()
    from backtest import load_races
    races, _ = load_races(a.state, Path(a.history))
    races = [r for r in races if B.bsp_chances(r.runners)]
    train, test = split_by_date(races)
    print(f"{len(races)} races; fitted on the older {len(train)} ({train[0].date} to {train[-1].date}), "
          f"scored on the newer {len(test)} ({test[0].date} to {test[-1].date}); ridge {a.ridge:g}")
    mkt = B.score(B.market_probs(test), test).kl_to_bsp
    print(f"\nKL to Betfair SP on the newer races (lower is sharper). The opening market: {mkt:.4f}. "
          "The opening average is a phantom price, so this measures information, not an edge.\n")
    print("| model | features | KL to BSP | vs the opening market |")
    print("|---|---|---|---|")
    deployed = B.MODEL_SETS["market_kitchen_sink_exp"]
    rows = [("market only", [B.MARKET_FEATURE]), ("deployed (market_kitchen_sink_exp)", deployed),
            ("history + market", B.MODEL_SETS["history_plus_market"]), ("market + history (compact form)", B.MODEL_SETS["market_plus_history"]),
            ("deployed + history", B.MODEL_SETS["market_kitchen_sink_history"]),
            ("deployed + history + next-run collateral", B.MODEL_SETS["market_kitchen_sink_history"] + B.COLLATERAL_NEXT),
            ("deployed + history + intent", B.MODEL_SETS["market_kitchen_sink_history"] + B.INTENT),
            ("deployed + history + both", B.MODEL_SETS["market_kitchen_sink_intent"])]
    results = {}
    for name, feats in rows:
        kl = logit_trial(train, test, feats, a.ridge)
        results[name] = kl
        print(f"| logit: {name} | {len(feats)} | {kl:.4f} | {kl - mkt:+.4f} |")
    if "--trees" in sys.argv:
        for name, feats in (("deployed", deployed), ("deployed + history", B.MODEL_SETS["market_kitchen_sink_history"])):
            kl = tree_trial(train, test, feats)
            if kl is None:
                print("| trees | - | scikit-learn not installed | - |")
                break
            print(f"| trees: {name} | {len(feats)} | {kl:.4f} | {kl - mkt:+.4f} |")
    gain = results["deployed (market_kitchen_sink_exp)"] - results["deployed + history"]
    print(f"\nHISTORY on top of the deployed set: {gain:+.4f} KL ({'sharper' if gain > 0 else 'not sharper'}).")


if __name__ == "__main__":
    main()
