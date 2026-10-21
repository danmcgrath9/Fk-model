"""Coach and player tendencies as model inputs, then the same out-of-sample check as model_v2.

All from earlier games of the same team-season (a coach proxy: the team that season) or the
same player, so nothing sees the game it describes.
  coach_blowout_cut   the team's starters' minutes in earlier lopsided games (final margin 15+)
                      divided by their minutes in other games: how hard this coach pulls starters
  coach_close_tight   the same for close games (margin 5 or less): how much the starters ride
  boost_when_short    this player's points per minute in earlier games where the team was missing
                      30+ rotation minutes, divided by his rate in other games
  shot_streakiness    spread of his threes per minute over his last 20 games
Interactions the trees can use directly: coach_blowout_cut x expected margin size, and
boost_when_short x tonight's vacated minutes.

    python nba/tendencies.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import model_v2 as m2
import project as pr

NEW = ["coach_blowout_cut", "coach_close_tight", "blowout_x_margin", "boost_when_short", "boost_x_vacated",
       "shot_streakiness"]


def _prior_ratio(df, group, num_mask, val, min_n=3):
    """Per row: mean of `val` over EARLIER rows in `group` where num_mask is true, divided by the
    mean over earlier rows where it is false. NaN until both sides have min_n rows."""
    out = pd.Series(np.nan, index=df.index)
    for _, g in df.groupby(group, sort=False):
        on = num_mask.loc[g.index].to_numpy()
        v = g[val].to_numpy()
        s_on = np.cumsum(np.where(on, v, 0)) - np.where(on, v, 0)
        n_on = np.cumsum(on) - on
        s_off = np.cumsum(np.where(~on, v, 0)) - np.where(~on, v, 0)
        n_off = np.cumsum(~on) - (~on)
        ok = (n_on >= min_n) & (n_off >= min_n)
        with np.errstate(divide="ignore", invalid="ignore"):
            r = (s_on / n_on) / (s_off / n_off)
        out.loc[g.index] = np.where(ok, r, np.nan)
    return out


def build() -> pd.DataFrame:
    df = m2.features_v2().sort_values(["date", "gameId"]).reset_index(drop=True)
    margin = (df.team_pts - df.opp_pts).abs()
    starters = df.starter.astype(bool)
    team_season = df.teamId.astype(str) + "_" + df.season.astype(str)
    # one row per team-game (so no game sees its own or a same-game teammate's minutes):
    # the starters' average minutes, then the ratio over EARLIER team-games
    tg = (df[starters].assign(ts=team_season[starters], margin=margin[starters])
          .groupby(["ts", "gameId", "teamId", "date"]).agg(min=("min", "mean"), margin=("margin", "first"))
          .reset_index().sort_values(["date", "gameId"]).reset_index(drop=True))
    tg["coach_blowout_cut"] = _prior_ratio(tg, "ts", tg.margin >= 15, "min", min_n=4)
    tg["coach_close_tight"] = _prior_ratio(tg, "ts", tg.margin <= 5, "min", min_n=4)
    df = df.merge(tg[["gameId", "teamId", "coach_blowout_cut", "coach_close_tight"]], on=["gameId", "teamId"], how="left")
    df["blowout_x_margin"] = df.coach_blowout_cut * df.abs_exp_margin

    df = df.sort_values(["personId", "date", "gameId"]).reset_index(drop=True)
    df["pts_per_min"] = df.pts / df["min"].clip(lower=1)
    short = df.vacated_min >= 30
    df["boost_when_short"] = _prior_ratio(df, "personId", short, "pts_per_min", min_n=5)
    df["boost_x_vacated"] = df.boost_when_short * df.vacated_min
    df["shot_streakiness"] = (df.fg3m / df["min"].clip(lower=1)).groupby(df.personId).transform(
        lambda x: x.shift(1).rolling(20, min_periods=8).std())
    return df


def main() -> None:
    df = build()
    v3_min, v3_rate = m2.V2_MIN + NEW, m2.V2_RATE + NEW
    rng = np.random.default_rng(0)
    rows = []
    for season in pr.TEST:
        train = df[(df.season < season) & (df.season >= pr.TRAIN[0])]
        test = df[df.season == season]
        p2 = m2.predict(m2.fit(train, m2.V2_MIN, m2.V2_RATE), test, m2.V2_MIN, m2.V2_RATE)
        p3 = m2.predict(m2.fit(train, v3_min, v3_rate), test, v3_min, v3_rate)
        keep = pr.propable(test)
        for st in ["min", *pr.TARGETS]:
            col = "min_proj" if st == "min" else f"{st}_proj"
            e2 = (p2.loc[keep, col] - test.loc[keep, st]).abs()
            e3 = (p3.loc[keep, col] - test.loc[keep, st]).abs()
            g = pd.DataFrame({"g": test.loc[keep, "gameId"], "d": e2 - e3}).groupby("g").d.agg(["sum", "size"])
            s, c = g["sum"].to_numpy(), g["size"].to_numpy()
            idx = rng.integers(0, len(g), (1000, len(g)))
            boot = s[idx].sum(1) / c[idx].sum(1)
            rows.append(dict(season=f"{season}/{str(season + 1)[2:]}", stat=st, v2=e2.mean(), v3=e3.mean(),
                             gain=e2.mean() - e3.mean(), lo=np.percentile(boot, 2.5), hi=np.percentile(boot, 97.5)))
        # minutes in expected blowouts: the case the coach inputs are for
        blow = keep & (test.abs_exp_margin >= 7) & test.starter.astype(bool)
        e2b = (p2.loc[blow, "min_proj"] - test.loc[blow, "min"]).abs().mean()
        e3b = (p3.loc[blow, "min_proj"] - test.loc[blow, "min"]).abs().mean()
        rows.append(dict(season=f"{season}/{str(season + 1)[2:]}", stat="min, starters, expected blowout",
                         v2=e2b, v3=e3b, gain=e2b - e3b, lo=np.nan, hi=np.nan))
    print(pd.DataFrame(rows).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
