"""What wins races, on Form King's figures alone. Read-only, no Form King calls.

    python scripts/winner_study.py [--state VIC] [--history history]

Two questions the form price (config/form_price.json) does not answer by itself:

  1. Should it be fitted to WINNERS rather than to Betfair SP? Fitting to BSP asks the model
     to reproduce the market's closing price; fitting to the result asks it to be right.
  2. Should it carry the market's memory of the horse (its past-run BSPs) at all? Those five
     figures are not today's price, but they are still the market's opinion.

So four models are fitted on the older 70% of racing and judged once on the newer 30%:
pure form (no market figures of any kind) and the current set (with market memory), each
fitted to BSP and to winners. Judged on: log loss against the winners (lower is better),
how often the top pick won, KL to BSP, and the 20c value rule (rated under $50) backed at
the opening price and settled at the opening price, at BSP and at BSP less 8% commission.

Then, for the pure-form winner fit, which inputs matter: the fitted weight scaled by how
much the figure varies (so a big weight on a figure that barely moves counts for little),
how often the runner best on each figure wins its race against the 1-in-field base rate,
and what dropping each figure costs the fit out of sample.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fk import backtest as B  # noqa: E402
from fit_form_only import BARRED, EXPERIENCE_FORM, TRAIN_SHARE, split_by_date  # noqa: E402
from form_value_trial import bets_for, summary  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PURE_FORM = B.MODEL_SETS["kitchen_sink"] + EXPERIENCE_FORM + B.INTENT
WITH_MEMORY = PURE_FORM + B.MARKET_MEMORY
assert not BARRED & set(WITH_MEMORY)
RIDGES = {"bsp": [0.1, 1.0, 10.0], "winners": [1.0, 10.0, 30.0, 100.0]}
TARGETS = {"bsp": B.bsp_chances, "winners": B.winner_chances}


class Stack:
    def __init__(self, races, features, target):
        xs, qs, sizes = [], [], []
        for race in races:
            q = target(race.runners)
            if q is None:
                continue
            xs.extend([[0.0 if r.x.get(f) is None else r.x.get(f, 0.0) for f in features] for r in race.runners])
            qs.extend(q)
            sizes.append(len(race.runners))
        self.X = np.nan_to_num(np.asarray(xs, dtype=float).reshape(-1, len(features)))
        self.q = np.asarray(qs, dtype=float)
        self.starts = np.concatenate([[0], np.cumsum(sizes)[:-1]]).astype(int)
        self.idx = np.repeat(np.arange(len(sizes)), sizes)

    def probs(self, beta):
        s = self.X @ beta
        s = s - np.maximum.reduceat(s, self.starts)[self.idx]
        w = np.exp(s)
        return w / np.add.reduceat(w, self.starts)[self.idx]


def fit_np(races, features, ridge, target, iterations=60):
    st = Stack(races, features, target)
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


def log_loss(beta, races):
    tot, n = 0.0, 0
    for race in races:
        w = next((i for i, r in enumerate(race.runners) if r.finish == 1), None)
        if w is None:
            continue
        p = B.predict(beta, race.runners)
        tot += -math.log(max(p[w], 1e-9))
        n += 1
    return tot / n if n else float("nan")


def top_pick_rate(beta, races):
    hit, n = 0, 0
    for race in races:
        if not any(r.finish == 1 for r in race.runners):
            continue
        p = B.predict(beta, race.runners)
        hit += race.runners[max(range(len(p)), key=lambda i: p[i])].finish == 1
        n += 1
    return hit / n if n else float("nan")


def choose_ridge(train, features, target_name):
    inner, valid = split_by_date(train, 0.8)
    best = None
    for ridge in RIDGES[target_name]:
        beta = fit_np(inner, features, ridge, TARGETS[target_name])
        v = log_loss(beta, valid)
        if best is None or v < best[1]:
            best = (ridge, v)
    return best[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--history", default=str(ROOT / "history"))
    a = ap.parse_args()
    from backtest import load_races
    races, _ = load_races(a.state, Path(a.history))
    races = [r for r in races if B.winner_chances(r.runners) and B.bsp_chances(r.runners)]
    train, test = split_by_date(races, TRAIN_SHARE)
    print(f"{len(races)} races with a winner and a Betfair SP; fitted on the older {len(train)} ({train[0].date} to "
          f"{train[-1].date}), judged once on the newer {len(test)} ({test[0].date} to {test[-1].date}).\n")
    mkt_ll = log_loss({B.MARKET_FEATURE: 1.0}, test)
    mkt_top = top_pick_rate({B.MARKET_FEATURE: 1.0}, test)
    print(f"The opening market on the same races: log loss {mkt_ll:.4f}, top pick won {mkt_top:.1%}.\n")

    print("| inputs | fitted to | ridge | log loss vs winners | top pick won | KL to BSP |")
    print("|---|---|---|---|---|---|")
    fits = {}
    for name, feats in (("pure form (no market figures)", PURE_FORM), ("form + market memory (current)", WITH_MEMORY)):
        for tname in ("bsp", "winners"):
            ridge = choose_ridge(train, feats, tname)
            beta = fit_np(train, feats, ridge, TARGETS[tname])
            fits[(name, tname)] = beta
            kl = B.score([B.predict(beta, r.runners) for r in test], test).kl_to_bsp
            print(f"| {name} | {tname} | {ridge:g} | {log_loss(beta, test):.4f} | {top_pick_rate(beta, test):.1%} | {kl:.4f} |")

    print("\nThe 20c value rule, rated under $50, one unit at the opening price, on the newer races (± one standard error):\n")
    print("| inputs | fitted to | bets | winners | at the opening price | at Betfair SP | at BSP less 8% |")
    print("|---|---|---|---|---|---|---|")
    for (name, tname), beta in fits.items():
        print(f"| {name} | {tname} " + summary(bets_for(test, beta, 0.2, True)))

    beta = fits[("pure form (no market figures)", "winners")]
    feats = PURE_FORM
    print("\n## What wins, on pure form fitted to winners\n")
    print("Weight x spread: the fitted weight times how much the figure varies between rivals, so it reads as the "
          "figure's pull on the price. Best-in-race wins: how often the runner best on that figure alone wins, against "
          "the average 1-in-field base rate. Drop cost: how much worse the fit is out of sample without the figure "
          "(log loss, higher is worse).\n")
    st = Stack(train, feats, B.winner_chances)
    spread = st.X.std(axis=0)
    base = sum(1 / len(r.runners) for r in test) / len(test)
    rows = []
    full = log_loss(beta, test)
    for j, f in enumerate(feats):
        hit = 0
        for race in test:
            i = max(range(len(race.runners)), key=lambda k: race.runners[k].x.get(f, 0.0))
            hit += race.runners[i].finish == 1
        rate = hit / len(test)
        without = [g for g in feats if g != f]
        drop = log_loss(fit_np(train, without, RIDGES["winners"][1], B.winner_chances), test) - full
        rows.append((abs(beta[f] * spread[j]), beta[f], spread[j], rate, drop, f))
    rows.sort(reverse=True)
    print(f"| figure | weight | spread | weight x spread | best-in-race wins (base {base:.1%}) | drop cost |")
    print("|---|---|---|---|---|---|")
    for pull, w, sd, rate, drop, f in rows:
        print(f"| {f} | {w:+.3f} | {sd:.3f} | {pull:.3f} | {rate:.1%} | {drop:+.4f} |")


if __name__ == "__main__":
    main()
