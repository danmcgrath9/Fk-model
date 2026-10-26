"""League scoring drifts season to season (and within one), and a model trained on earlier
seasons lags it: points overs landed 3 points more often than we said, in every game context.
Test: give the model the league's recent level, per minute, for each stat: all players'
totals over the previous 30 days (and the season so far), never including the day itself.

    python nba/league_level.py
"""
import numpy as np
import pandas as pd

import model_v2 as m2
import project as pr
from features import DATA, FEATURES_MIN, FEATURES_RATE

STATS = ["pts", "reb", "ast", "fg3m", "fga", "fta"]


def league_levels(df: pd.DataFrame) -> pd.DataFrame:
    day = df.groupby("date")[["min", *STATS]].sum().sort_index()
    roll = day.rolling("30D", closed="left").sum()
    out = pd.DataFrame(index=day.index)
    for st in STATS:
        out[f"lg_{st}_pm_30d"] = roll[st] / roll["min"]
    season = df.groupby("date").season.first()
    cum = day.groupby(season).cumsum() - day
    for st in STATS:
        out[f"lg_{st}_pm_season"] = cum[st] / cum["min"].replace(0, np.nan)
    return out.reset_index()


NEW = [f"lg_{s}_pm_30d" for s in STATS] + [f"lg_{s}_pm_season" for s in STATS]

if __name__ == "__main__":
    df = pd.read_parquet(DATA / "features.parquet")
    df = df[df.game_ok & df.min_ewm5.notna()]
    df = df.merge(league_levels(df), on="date", how="left")
    rng = np.random.default_rng(0)
    for season in pr.TEST:
        train = df[(df.season < season) & (df.season >= pr.TRAIN[0])]
        test = df[df.season == season]
        a = m2.predict(m2.fit(train, FEATURES_MIN, FEATURES_RATE), test, FEATURES_MIN, FEATURES_RATE)
        b = m2.predict(m2.fit(train, FEATURES_MIN, FEATURES_RATE + NEW), test, FEATURES_MIN, FEATURES_RATE + NEW)
        keep = pr.propable(test)
        parts = []
        for st in pr.TARGETS:
            c = f"{st}_proj"
            ea, eb = (a.loc[keep, c] - test.loc[keep, st]).abs(), (b.loc[keep, c] - test.loc[keep, st]).abs()
            bias_a, bias_b = (a.loc[keep, c] - test.loc[keep, st]).mean(), (b.loc[keep, c] - test.loc[keep, st]).mean()
            g = pd.DataFrame({"g": test.loc[keep, "gameId"], "d": ea - eb}).groupby("g").d.agg(["sum", "size"])
            s, n = g["sum"].to_numpy(), g["size"].to_numpy()
            i = rng.integers(0, len(g), (1000, len(g)))
            bt = s[i].sum(1) / n[i].sum(1)
            parts.append(f"{st} miss {ea.mean():.3f}->{eb.mean():.3f} [{np.percentile(bt, 2.5):+.3f},{np.percentile(bt, 97.5):+.3f}] "
                         f"bias {bias_a:+.2f}->{bias_b:+.2f}")
        print(season, " | ".join(parts))
