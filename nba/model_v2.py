"""Model v2: the angles that beat our model in real games, added as inputs.

New inputs (all from earlier games, built in angles.py / angles2.py):
  dvp_<stat>_pm     the opponent's defence against the player's role, per minute
  pace              both teams' recent possessions per 48
  min_jump          last-3-games minutes minus season average (a role change)
  games_with_team   games for his current team this season (new-team players start at 0)
  new_team_early    on a new team and under 10 games in
  last_excess3      threes made above his rate, last game
Same walk-forward split and LightGBM settings as project.py. Scored two ways:
  1. all prop-able player-games 2024/25 and 2025/26, against v1 (bootstrap by game);
  2. the 7pm injury-report version against the 6,625 DunkAPI lines, against v1 at 7pm.

    python nba/model_v2.py
"""
from __future__ import annotations

import lightgbm as lgb
import numpy as np
import pandas as pd

import angles2
import at_report as ar
import line_test as lt
import line_test_at_report as lta
import probability as pb
import project as pr
from features import DATA, FEATURES_MIN, FEATURES_RATE

NEW = ["pace", "min_jump", "games_with_team", "new_team_early", "last_excess3"]
V2_MIN = FEATURES_MIN + NEW
V2_RATE = FEATURES_RATE + NEW + [f"dvp_{s}_pm" for s in pr.TARGETS]


def features_v2() -> pd.DataFrame:
    df = pd.read_parquet(DATA / "features.parquet")
    df = df[df.game_ok & df.min_ewm5.notna()]
    df = angles2.build(df).sort_values(["personId", "date", "gameId"])
    df["min_jump"] = df.min_l3 - df.min_season
    df["games_with_team"] = df.groupby(["personId", "season", "team"]).cumcount()
    df["last_excess3"] = df.groupby("personId").excess3.shift(1)
    df["new_team_early"] = df.new_team_early.astype(float)
    return df.reset_index(drop=True)


def fit(train: pd.DataFrame, fmin, frate):
    m_min = lgb.LGBMRegressor(**pr.PARAMS, random_state=1).fit(train[fmin], train["min"])
    tr = train[train["min"] >= 1]
    rate = {st: lgb.LGBMRegressor(**pr.PARAMS, random_state=2).fit(tr[frate], tr[st] / tr["min"],
                                                                    sample_weight=tr["min"])
            for st in pr.TARGETS}
    return m_min, rate


def predict(models, x, fmin, frate) -> pd.DataFrame:
    m_min, rate = models
    out = pd.DataFrame({"min_proj": np.clip(m_min.predict(x[fmin]), 0, 48)}, index=x.index)
    for st in pr.TARGETS:
        out[f"{st}_proj"] = out.min_proj * np.clip(rate[st].predict(x[frate]), 0, None)
    return out


def main() -> None:
    df = features_v2()
    status = ar.report_status()
    rng = np.random.default_rng(0)
    rows, at7 = [], []
    for season in pr.TEST:
        train = df[(df.season < season) & (df.season >= pr.TRAIN[0])]
        test = df[df.season == season]
        v1, v2 = fit(train, FEATURES_MIN, FEATURES_RATE), fit(train, V2_MIN, V2_RATE)
        p1, p2 = predict(v1, test, FEATURES_MIN, FEATURES_RATE), predict(v2, test, V2_MIN, V2_RATE)
        keep = pr.propable(test)
        for st in ["min", *pr.TARGETS]:
            col = "min_proj" if st == "min" else f"{st}_proj"
            e1 = (p1.loc[keep, col] - test.loc[keep, st]).abs()
            e2 = (p2.loc[keep, col] - test.loc[keep, st]).abs()
            g = pd.DataFrame({"g": test.loc[keep, "gameId"], "d": e1 - e2}).groupby("g").d.agg(["sum", "size"])
            s, c = g["sum"].to_numpy(), g["size"].to_numpy()
            idx = rng.integers(0, len(g), (1000, len(g)))
            boot = s[idx].sum(1) / c[idx].sum(1)
            rows.append(dict(season=f"{season}/{str(season + 1)[2:]}", stat=st, n=int(keep.sum()),
                             v1=e1.mean(), v2=e2.mean(), gain=e1.mean() - e2.mean(),
                             lo=np.percentile(boot, 2.5), hi=np.percentile(boot, 97.5)))
        # 7pm injury-report version, both models
        av = ar.availability_at(test, status, "19:00", 0)
        x = test.drop(columns=ar.AVAIL).merge(av, on=["gameId", "teamId", "personId"], how="left")
        for name, models, fm, fr in [("v1", v1, FEATURES_MIN, FEATURES_RATE), ("v2", v2, V2_MIN, V2_RATE)]:
            p = predict(models, x, fm, fr)
            at7.append(pd.concat([x[["gameId", "date", "personId"]].reset_index(drop=True),
                                  p.reset_index(drop=True)], axis=1).assign(model=name))
    t = pd.DataFrame(rows)
    print("1. Average miss, all prop-able player-games (lower is better); gain = v1 minus v2")
    print(t.round(3).to_string(index=False))

    lines = lt.load_lines()
    lines = lines[lines.over_odds.notna() & lines.under_odds.notna() & lines.actual.notna()].copy()
    lines["dec_over"], lines["dec_under"] = lt.american_to_decimal(lines.over_odds), lt.american_to_decimal(lines.under_odds)
    var = pb.fit_alphas()
    a = pd.concat(at7)
    a["date"] = pd.to_datetime(a.date).dt.strftime("%Y-%m-%d")
    res = {}
    for name, g in a.groupby("model"):
        long = pd.concat([g[["date", "personId", f"{s}_proj"]].rename(columns={f"{s}_proj": "proj"}).assign(st=s)
                          for s in pr.TARGETS])
        j = lines.merge(long, on=["personId", "date", "st"])
        res[f"{name} at 7pm"] = lta.score(j, var)
    print("\n2. Against the DunkAPI lines, projections from the 7pm injury report")
    print(pd.DataFrame(res).T.to_string(float_format=lambda v: f"{v:.3f}"))


if __name__ == "__main__":
    main()
