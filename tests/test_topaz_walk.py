"""research/greyhound/topaz_walk.py: the refit cadence prices every month from a fit that saw nothing at or after it."""
import os
import sys
import time

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_walk as W  # noqa: E402


class Flat:
    """A stand-in booster: every runner the same score, so each race prices to 1/field."""
    def __init__(self, n_train):
        self.n_train = n_train

    def predict(self, X, raw_score=True):
        return np.zeros(len(X))


def frame(months):
    rows = []
    for m in range(months):
        for r in range(3):                      # three 4-dog races a month
            d = pd.Timestamp("2024-01-01") + pd.DateOffset(months=m, days=r)
            for b in range(1, 5):
                rows.append(dict(date=d, race_id=m * 10 + r, box=b, won=int(b == 1), p_mkt=0.25, f1=float(b),
                                 track="MEP", grade="5", sex="D"))
    return pd.DataFrame(rows)


def test_refit_cadence_prices_every_month_from_an_earlier_fit(monkeypatch):
    monkeypatch.setattr(W, "MIN_TRAIN_RACES", 1)
    calls = []

    def fit(X, y, race, weight, rounds):
        calls.append((len(X), rounds))
        return Flat(len(X))

    df, log = W.walk(frame(7), ["f1"], [], pd.Period("2024-02", "M"), time.monotonic(), every=2, fit=fit)
    # months 2024-02 .. 2024-07: refits on Feb, Apr, Jun (two boosters each), the other three priced by the last pair
    assert [m for m, s in log] == ["2024-02", "2024-03", "2024-04", "2024-05", "2024-06", "2024-07"]
    assert [("fit on" in s) for _, s in log] == [True, False, True, False, True, False]
    assert "priced by the 2024-02 fit" in log[1][1] and "priced by the 2024-06 fit" in log[5][1]
    assert len(calls) == 6 and calls[0] == (12, W.ROUNDS_A) and calls[1] == (12, W.ROUNDS_B)   # Feb: trained on Jan only
    assert calls[2][0] == 36                                                                      # Apr: Jan to Mar
    priced = df[df.date >= "2024-02-01"]
    assert priced.p_a.notna().all() and np.allclose(priced.p_a, 0.25) and df[df.date < "2024-02-01"].p_a.isna().all()


def test_every_month_refits_by_default(monkeypatch):
    monkeypatch.setattr(W, "MIN_TRAIN_RACES", 1)
    n = []
    df, log = W.walk(frame(4), ["f1"], [], pd.Period("2024-02", "M"), time.monotonic(),
                     fit=lambda X, y, r, w, k: (n.append(1), Flat(len(X)))[1])
    assert len(n) == 6 and all("fit on" in s for _, s in log)


def _rule_frame(seed=0):
    rng = np.random.default_rng(seed)
    n_races, field = 2400, 5
    race = np.repeat(np.arange(n_races), field)
    date = pd.to_datetime("2025-01-01") + pd.to_timedelta(np.repeat(np.arange(n_races) // 7, field), unit="D")
    raw = rng.normal(size=len(race))
    p = pd.Series(np.exp(raw)).groupby(race).transform(lambda s: s / s.sum()).values
    won = np.zeros(len(race))
    for r in range(n_races):
        i = np.flatnonzero(race == r)
        won[rng.choice(i, p=p[i])] = 1
    sp = pd.Series(p * np.exp(rng.normal(0, 0.4, len(race)))).groupby(race).transform(lambda s: s / s.sum()).values
    return pd.DataFrame({"race_id": race, "date": date, "won": won, "p_a": p, "p_sp": sp, "start_price": 1.0 / sp})


def test_horse_rule_on_the_ensemble_is_the_same_rule_when_the_ensemble_is_the_model(capsys):
    df = _rule_frame()
    df["p_ens"] = df.p_a
    first = pd.Period("2025-08", freq="M")
    W.horse_rule(df, first, "start_price", "p_sp", 0.0, "model")
    a = capsys.readouterr().out
    W.horse_rule(df, first, "start_price", "p_sp", 0.0, "model", sig="p_ens")
    b = capsys.readouterr().out
    assert "| no guard | all |" in a and a == b
