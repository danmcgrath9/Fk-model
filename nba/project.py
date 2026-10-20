"""Step 1: projection = minutes x per-minute rate, for points, rebounds, assists, threes.

Time split, no tuning on the test seasons:
    train  2020/21 - 2023/24   (seasons 2020-2023 in nba_data's naming)
    test   2024/25 and 2025/26 (seasons 2024, 2025), each reported on its own

Two LightGBM models per stat: one for minutes, one for the per-minute rate (weighted by
minutes, so a 2-minute cameo does not count as much as a 36-minute night). The
projection is their product. It is scored against two baselines a punter would use:
the player's season average so far, and his last-10 average.

Scored only on "prop-able" players: averaging 20+ minutes coming in and at least five
games into the season. That is roughly who books post lines for.

    python nba/project.py         # writes nba/data/projections.parquet and prints the scorecard
"""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from features import DATA, FEATURES_MIN, FEATURES_RATE

TRAIN = [2020, 2021, 2022, 2023]
TEST = [2024, 2025]
TARGETS = ["pts", "reb", "ast", "fg3m"]
PARAMS = dict(objective="regression", learning_rate=0.03, num_leaves=31, min_child_samples=200,
              subsample=0.8, subsample_freq=1, colsample_bytree=0.8, n_estimators=600, verbose=-1)


def propable(df: pd.DataFrame) -> pd.Series:
    return (df.min_ewm5 >= 20) & (df.gp_season >= 5)


def fit_predict(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    out = test[["gameId", "date", "season", "personId", "teamId", "team", "min", *TARGETS]].copy()
    m_min = lgb.LGBMRegressor(**PARAMS, random_state=1).fit(train[FEATURES_MIN], train["min"])
    out["min_proj"] = np.clip(m_min.predict(test[FEATURES_MIN]), 0, 48)
    tr = train[train["min"] >= 1]
    for st in TARGETS:
        m = lgb.LGBMRegressor(**PARAMS, random_state=2).fit(
            tr[FEATURES_RATE], tr[st] / tr["min"], sample_weight=tr["min"])
        out[f"{st}_rate"] = np.clip(m.predict(test[FEATURES_RATE]), 0, None)
        out[f"{st}_proj"] = out.min_proj * out[f"{st}_rate"]
        out[f"{st}_base_season"] = test[f"{st}_season"]
        out[f"{st}_base_l10"] = test[f"{st}_l10"]
    out["min_base_season"] = test["min_season"]
    out["min_base_l10"] = test["min_ewm5"]
    return out


def scorecard(pred: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for season, p in pred.groupby("season"):
        for st in ["min", *TARGETS]:
            y = p[st]
            for name, col in [("model", f"{st}_proj"), ("season avg", f"{st}_base_season"),
                              ("last 10 / ewm", f"{st}_base_l10")]:
                e = p[col] - y
                rows.append(dict(season=f"{season}/{str(season + 1)[2:]}", stat=st, method=name,
                                 n=int(e.notna().sum()), mae=e.abs().mean(),
                                 rmse=np.sqrt((e ** 2).mean()), bias=e.mean()))
    return pd.DataFrame(rows)


def bootstrap_mae_gain(pred: pd.DataFrame, st: str, base: str, n: int = 1000, seed: int = 0):
    """95% interval for (baseline MAE - model MAE), resampling whole GAMES (rows in one
    game are not independent)."""
    rng = np.random.default_rng(seed)
    d = (pred[f"{st}_{base}"] - pred[st]).abs() - (pred[f"{st}_proj"] - pred[st]).abs()
    g = pd.DataFrame({"gameId": pred.gameId, "d": d}).dropna().groupby("gameId").d.agg(["sum", "size"])
    s, c = g["sum"].to_numpy(), g["size"].to_numpy()
    idx = rng.integers(0, len(g), size=(n, len(g)))
    gains = s[idx].sum(1) / c[idx].sum(1)
    return float(np.percentile(gains, 2.5)), float(np.percentile(gains, 97.5))


def main() -> None:
    df = pd.read_parquet(DATA / "features.parquet")
    df = df[df.game_ok]
    train = df[df.season.isin(TRAIN) & df.min_ewm5.notna()]
    preds = []
    for season in TEST:
        test = df[(df.season == season)]
        preds.append(fit_predict(train, test))
    pred = pd.concat(preds, ignore_index=True)
    pred.to_parquet(DATA / "projections.parquet", index=False)

    scored = pred.merge(df[["gameId", "personId", "min_ewm5", "gp_season"]], on=["gameId", "personId"])
    scored = scored[propable(scored)]
    for st in ["min", *TARGETS]:
        scored = scored[scored[f"{st}_base_season"].notna() if st != "min" else scored.min_base_season.notna()]
    card = scorecard(scored)
    pd.set_option("display.width", 140)
    print(card.round(3).to_string(index=False))
    gains = {}
    for season, p in scored.groupby("season"):
        for st in TARGETS:
            for base in ["base_season", "base_l10"]:
                lo, hi = bootstrap_mae_gain(p, st, base)
                gains[f"{season} {st} vs {base}"] = (round(lo, 3), round(hi, 3))
    print("\nMAE improvement over baseline, 95% bootstrap (by game):")
    for k, v in gains.items():
        print(f"  {k}: {v[0]} to {v[1]}")
    (DATA / "scorecard.json").write_text(json.dumps(
        {"card": card.round(4).to_dict("records"), "mae_gain_ci95": gains}, indent=1))


if __name__ == "__main__":
    main()
