"""Theory exercises: the same inputs, different ideas about how they should count, each
judged out of sample the same way (fit on the older 70% of stored racing, KL to Betfair
SP on the newer 30%; the opening average is a phantom price, so this is information, not
an edge).

    python scripts/theory_trial.py [--state VIC] [--history history] [--ridge 1.0]

  1. recency: races count less the older they are (half-lives of 90, 180, 365 days)
  2. race type: the same figure means different things in different races, so the form
     features are crossed with the race's class (lws), distance band and field size
  3. the whole finishing order: fit to who ran first, second AND third (exploded logit),
     which learns from the placings and is not capped at copying the close
  4. two targets blended: the copy-the-close model and the be-right model, combined in
     log space with the weight chosen on the last fifth of the training races
"""
from __future__ import annotations

import argparse
import math
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fk import backtest as B  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEPLOYED = "market_kitchen_sink_exp"


def kl(model_probs, races) -> float:
    return B.score(model_probs, races).kl_to_bsp


def predict_all(beta, races):
    return [B.predict(beta, r.runners) for r in races]


def recency_weight(latest: str, half_life_days: float):
    end = date.fromisoformat(latest[:10])
    def w(race):
        age = (end - date.fromisoformat(race.date[:10])).days
        return 0.5 ** (age / half_life_days)
    return w


def add_type_interactions(races, features: list[str]) -> list[str]:
    """Cross each form feature with three race-type indicators, centred so the main effect
    keeps its meaning: strong race (lws in the top third), staying trip (1800m+), big field
    (12+). Returns the new feature names; mutates runner.x in place."""
    lws = sorted(r.lws for r in races if getattr(r, "lws", None) is not None)
    strong_cut = lws[2 * len(lws) // 3] if lws else None
    new = []
    inds = {"strong": lambda r: 1.0 if strong_cut is not None and getattr(r, "lws", None) is not None and r.lws >= strong_cut else 0.0,
            "staying": lambda r: 1.0 if (getattr(r, "distance_m", None) or 0) >= 1800 else 0.0,
            "bigfield": lambda r: 1.0 if len(r.runners) >= 12 else 0.0}
    for name, ind in inds.items():
        for f in features:
            new.append(f"{f}_x_{name}")
    for race in races:
        flags = {name: ind(race) for name, ind in inds.items()}
        for r in race.runners:
            for name, v in flags.items():
                for f in features:
                    r.x[f"{f}_x_{name}"] = r.x.get(f, 0.0) * v
    return new


def blend(p_a, p_b, a: float):
    out = []
    for pa, pb in zip(p_a, p_b):
        z = [a * math.log(max(x, 1e-12)) + (1 - a) * math.log(max(y, 1e-12)) for x, y in zip(pa, pb)]
        out.append(B.softmax(z))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--history", default=str(ROOT / "history"))
    ap.add_argument("--ridge", type=float, default=1.0)
    a = ap.parse_args()
    from backtest import load_races
    from feature_trial import split_by_date
    races, _ = load_races(a.state, Path(a.history))
    races = [r for r in races if B.bsp_chances(r.runners)]
    train, test = split_by_date(races)
    feats = B.MODEL_SETS[DEPLOYED]
    mkt = kl(B.market_probs(test), test)
    print(f"{len(races)} races; fitted on the older {len(train)}, scored on the newer {len(test)} ({test[0].date} to {test[-1].date}); ridge {a.ridge:g}")
    print(f"\nKL to Betfair SP on the newer races (lower is sharper). Opening market: {mkt:.4f}.\n")
    print("| exercise | KL to BSP | vs the market | vs the deployed fit |")
    print("|---|---|---|---|")
    base_beta = B.fit(train, feats, ridge=a.ridge)
    base = kl(predict_all(base_beta, test), test)
    def row(name, v):
        print(f"| {name} | {v:.4f} | {v - mkt:+.4f} | {v - base:+.4f} |")
    row("deployed fit, as it is", base)

    # 1. recency
    for hl in (90, 180, 365):
        beta = B.fit(train, feats, ridge=a.ridge, weights=recency_weight(train[-1].date, hl))
        row(f"1. recency, half-life {hl} days", kl(predict_all(beta, test), test))

    # 2. race type interactions (the form block only, to keep the count sane)
    form_block = [f for f in feats if f not in (B.MARKET_FEATURE, "market_prob", "market_x_neural")]
    extra = add_type_interactions(races, form_block)
    for scale, label in ((a.ridge, "same ridge"), (a.ridge * 10, "ridge x10 on the extra terms")):
        beta = B.fit(train, feats + extra, ridge=scale)
        row(f"2. race type x form ({len(extra)} extra terms, {label})", kl(predict_all(beta, test), test))

    # 3. exploded logit to the finishing order
    for depth in (2, 3):
        ex = B.exploded(train, depth=depth)
        beta = B.fit(ex, feats, ridge=a.ridge, target=B.winner_chances)
        row(f"3. finishing order to {depth} places ({len(ex)} choices)", kl(predict_all(beta, test), test))

    # 4. two targets blended, weight chosen on the last fifth of the training races
    cut = int(len(train) * 0.8)
    inner_train, inner_val = train[:cut], train[cut:]
    b_close = B.fit(inner_train, feats, ridge=a.ridge)
    b_right = B.fit(B.exploded(inner_train, 3), feats, ridge=a.ridge, target=B.winner_chances)
    pc, pr = predict_all(b_close, inner_val), predict_all(b_right, inner_val)
    best_a = min((0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0), key=lambda w: kl(blend(pc, pr, w), inner_val))
    b_close = B.fit(train, feats, ridge=a.ridge)
    b_right = B.fit(B.exploded(train, 3), feats, ridge=a.ridge, target=B.winner_chances)
    v = kl(blend(predict_all(b_close, test), predict_all(b_right, test), best_a), test)
    row(f"4. close model x{best_a:.1f} + order model x{1 - best_a:.1f} (weight chosen inside training)", v)
    print("\nvs the deployed fit: negative is sharper than the model as fitted today.")


if __name__ == "__main__":
    main()
