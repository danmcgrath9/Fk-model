"""Two standard upgrades, chosen on 2023/24 only and judged on 2024/25 and 2025/26:
  1. LightGBM settings picked from a small grid on 2023/24 (trained on 2020/21-2022/23);
  2. a second model predicting each stat DIRECTLY, averaged with minutes x rate.

    python nba/tune_blend.py
"""
import itertools

import lightgbm as lgb
import numpy as np
import pandas as pd

import project as pr
from features import DATA, FEATURES_MIN, FEATURES_RATE

df = pd.read_parquet(DATA / "features.parquet")
df = df[df.game_ok & df.min_ewm5.notna()]


def fit_predict(train, test, params, direct=False):
    m = lgb.LGBMRegressor(**params, random_state=1).fit(train[FEATURES_MIN], train["min"])
    out = {"min": np.clip(m.predict(test[FEATURES_MIN]), 0, 48)}
    tr = train[train["min"] >= 1]
    for st in pr.TARGETS:
        r = lgb.LGBMRegressor(**params, random_state=2).fit(tr[FEATURES_RATE], tr[st] / tr["min"], sample_weight=tr["min"])
        out[st] = out["min"] * np.clip(r.predict(test[FEATURES_RATE]), 0, None)
        if direct:
            dm = lgb.LGBMRegressor(**params, random_state=3).fit(train[FEATURES_RATE], train[st])
            out[st + "_direct"] = np.clip(dm.predict(test[FEATURES_RATE]), 0, None)
    return out


def mae(test, pred, st):
    k = pr.propable(test).to_numpy()
    return np.abs(pred[k] - test[st].to_numpy()[k]).mean()


# 1. grid on 2023/24
train, val = df[df.season.isin([2020, 2021, 2022])], df[df.season == 2023]
grid = []
for lr, leaves, mcs, n in itertools.product([0.02, 0.05], [15, 31, 63], [100, 400], [400, 900]):
    p = dict(pr.PARAMS, learning_rate=lr, num_leaves=leaves, min_child_samples=mcs, n_estimators=n)
    pred = fit_predict(train, val, p)
    grid.append((sum(mae(val, pred[s], s) / mae(val, val[s + "_season"].fillna(val[s].mean()).to_numpy(), s)
                     for s in pr.TARGETS) + mae(val, pred["min"], "min") / 4.5, p))
    print(f"lr {lr} leaves {leaves} mcs {mcs} n {n}: score {grid[-1][0]:.4f}", flush=True)
best = min(grid, key=lambda g: g[0])[1]
print("chosen on 2023/24:", {k: best[k] for k in ["learning_rate", "num_leaves", "min_child_samples", "n_estimators"]})

# 2. judge on the two later seasons: default vs tuned vs tuned + direct blend
for season in pr.TEST:
    tr, te = df[(df.season < season) & (df.season >= 2020)], df[df.season == season]
    a = fit_predict(tr, te, pr.PARAMS)
    b = fit_predict(tr, te, best, direct=True)
    parts = []
    for st in ["min", *pr.TARGETS]:
        line = f"{st} {mae(te, a[st], st):.3f} -> tuned {mae(te, b[st], st):.3f}"
        if st != "min":
            line += f" -> +direct {mae(te, 0.5 * b[st] + 0.5 * b[st + '_direct'], st):.3f}"
        parts.append(line)
    print(season, " | ".join(parts), flush=True)
