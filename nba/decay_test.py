"""DARKO-style test: does a very slow decay on per-minute rates (half-life 70 games, roughly a
season) help on top of our 5- and 25-game rates? Same walk-forward split and scoring as
model_v2.py.

    python nba/decay_test.py
"""
import numpy as np
import pandas as pd

import model_v2 as m2
import project as pr
from features import DATA, FEATURES_MIN, FEATURES_RATE, STATS, _prior_ewm

df = pd.read_parquet(DATA / "features.parquet")
df = df[df.game_ok & df.min_ewm5.notna()].sort_values(["personId", "date", "gameId"]).reset_index(drop=True)
for st in STATS:
    df[f"{st}_pm_vl"] = _prior_ewm(df[st], df.personId, 70) / _prior_ewm(df["min"], df.personId, 70).replace(0, np.nan)
df["min_ewm70"] = _prior_ewm(df["min"], df.personId, 70)
NEW = [f"{s}_pm_vl" for s in STATS] + ["min_ewm70"]
rng = np.random.default_rng(0)
for season in pr.TEST:
    train = df[(df.season < season) & (df.season >= pr.TRAIN[0])]
    test = df[df.season == season]
    a = m2.predict(m2.fit(train, FEATURES_MIN, FEATURES_RATE), test, FEATURES_MIN, FEATURES_RATE)
    b = m2.predict(m2.fit(train, FEATURES_MIN + NEW, FEATURES_RATE + NEW), test, FEATURES_MIN + NEW, FEATURES_RATE + NEW)
    keep = pr.propable(test)
    out = []
    for st in ["min", *pr.TARGETS]:
        c = "min_proj" if st == "min" else f"{st}_proj"
        ea, eb = (a.loc[keep, c] - test.loc[keep, st]).abs(), (b.loc[keep, c] - test.loc[keep, st]).abs()
        g = pd.DataFrame({"g": test.loc[keep, "gameId"], "d": ea - eb}).groupby("g").d.agg(["sum", "size"])
        s, n = g["sum"].to_numpy(), g["size"].to_numpy()
        i = rng.integers(0, len(g), (1000, len(g)))
        bt = s[i].sum(1) / n[i].sum(1)
        out.append(f"{st} {ea.mean():.3f}->{eb.mean():.3f} [{np.percentile(bt, 2.5):+.3f},{np.percentile(bt, 97.5):+.3f}]")
    print(season, " | ".join(out))
