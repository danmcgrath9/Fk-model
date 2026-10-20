"""Pre-game features for each player-game. Every feature uses ONLY games before this one.

The rule that keeps it honest: every rolling figure is computed on a player's (or a
team's) history and then shifted one game, so the game being predicted never sees its
own minutes, points or result. `tests/test_features.py` pins that.

Two inputs are "known before tip-off" rather than history, and are stated here because
they are the only places a leak could creep in:

* WHO IS PLAYING. `rot_present_min` and `vacated_min` use which rotation players
  (pre-game average >= 10 minutes) appear in this game. In real use that comes from the
  injury report and the inactive list ~30 minutes before tip. It slightly overstates
  what we know: a coach's-decision DNP or a player hurt in the first minute is visible
  here and would not be in real life. Deep-bench players are excluded on purpose,
  because a garbage-time appearance says the game was a blowout.
* HOME/AWAY and the schedule (rest days, back-to-backs): published in advance.

Game spread and total are NOT in yet (that needs The Odds API, paid). Until then
`exp_margin` and `exp_total` are stand-ins built from each team's prior scoring.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
STATS = ["pts", "reb", "ast", "fg3m", "fga", "fta", "tov"]
HALFLIFE_SHORT = 5      # games
HALFLIFE_LONG = 25
ROTATION_MIN = 10.0     # pre-game average minutes to count as a rotation player


def _prior_ewm(s: pd.Series, by: pd.Series, halflife: float) -> pd.Series:
    """EWM of each group's PREVIOUS values (this row excluded)."""
    return s.groupby(by).transform(lambda x: x.shift(1).ewm(halflife=halflife, min_periods=1).mean())


def _prior_roll(s: pd.Series, by: pd.Series, n: int) -> pd.Series:
    return s.groupby(by).transform(lambda x: x.shift(1).rolling(n, min_periods=1).mean())


def player_features(box: pd.DataFrame) -> pd.DataFrame:
    df = box.sort_values(["personId", "date", "gameId"]).reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"])
    pid = df.personId
    ps = df.personId.astype(str) + "_" + df.season.astype(str)

    df["min_ewm5"] = _prior_ewm(df["min"], pid, HALFLIFE_SHORT)
    df["min_ewm25"] = _prior_ewm(df["min"], pid, HALFLIFE_LONG)
    # The average AFTER this game: used only for later games (who is missing next time).
    df["min_ewm5_post"] = df.groupby(pid)["min"].transform(lambda x: x.ewm(halflife=HALFLIFE_SHORT).mean())
    df["min_l3"] = _prior_roll(df["min"], pid, 3)
    df["min_last"] = df.groupby(pid)["min"].shift(1)
    df["min_season"] = df.groupby(ps)["min"].transform(lambda x: x.shift(1).expanding().mean())
    df["min_sd10"] = df.groupby(pid)["min"].transform(lambda x: x.shift(1).rolling(10, min_periods=3).std())
    df["starter_rate5"] = _prior_ewm(df["starter"].astype(float), pid, HALFLIFE_SHORT)
    df["starter_last"] = df.groupby(pid)["starter"].shift(1).astype(float)
    df["gp_season"] = df.groupby(ps).cumcount()
    df["gp_career"] = df.groupby(pid).cumcount()
    df["days_rest"] = df.groupby(pid)["date"].diff().dt.days.clip(upper=10)
    df["b2b"] = (df["days_rest"] == 1).astype(float)

    # Per-minute rates, minute-weighted: EWM of stat over EWM of minutes.
    for st in STATS:
        for hl, tag in [(HALFLIFE_SHORT, "s"), (HALFLIFE_LONG, "l")]:
            num = _prior_ewm(df[st], pid, hl)
            den = _prior_ewm(df["min"], pid, hl)
            df[f"{st}_pm_{tag}"] = num / den.replace(0, np.nan)
        df[f"{st}_season"] = df.groupby(ps)[st].transform(lambda x: x.shift(1).expanding().mean())
        df[f"{st}_l10"] = _prior_roll(df[st], pid, 10)
    return df


def team_features(box: pd.DataFrame) -> pd.DataFrame:
    """One row per team-game: prior scoring, allowed, and the stand-in spread/total."""
    tg = (box.drop_duplicates(["gameId", "teamId"])
          [["gameId", "teamId", "opp_teamId", "date", "season", "home", "team_pts", "opp_pts", "game_minutes"]]
          .copy())
    tg["date"] = pd.to_datetime(tg["date"])
    tg = tg.sort_values(["teamId", "date", "gameId"]).reset_index(drop=True)
    scale = 48.0 / tg.game_minutes          # put overtime games on a 48-minute footing
    tg["off48"], tg["def48"] = tg.team_pts * scale, tg.opp_pts * scale
    tid = tg.teamId
    tg["off_ewm"] = _prior_ewm(tg.off48, tid, 15)
    tg["def_ewm"] = _prior_ewm(tg.def48, tid, 15)
    tg["team_days_rest"] = tg.groupby(tid)["date"].diff().dt.days.clip(upper=10)
    opp = tg[["gameId", "teamId", "off_ewm", "def_ewm", "team_days_rest"]].rename(columns={
        "teamId": "opp_teamId", "off_ewm": "opp_off_ewm", "def_ewm": "opp_def_ewm",
        "team_days_rest": "opp_days_rest"})
    tg = tg.merge(opp, on=["gameId", "opp_teamId"], how="left")
    home_edge = np.where(tg.home, 1.5, -1.5)
    tg["exp_team_pts"] = (tg.off_ewm + tg.opp_def_ewm) / 2 + home_edge
    tg["exp_opp_pts"] = (tg.opp_off_ewm + tg.def_ewm) / 2 - home_edge
    tg["exp_margin"] = tg.exp_team_pts - tg.exp_opp_pts
    tg["exp_total"] = tg.exp_team_pts + tg.exp_opp_pts
    tg["abs_exp_margin"] = tg.exp_margin.abs()
    return tg[["gameId", "teamId", "exp_team_pts", "exp_opp_pts", "exp_margin", "exp_total",
               "abs_exp_margin", "team_days_rest", "opp_days_rest", "opp_def_ewm"]]


def availability_features(df: pd.DataFrame) -> pd.DataFrame:
    """Who is in tonight's rotation, and how many minutes are free because someone is out.

    rot_present_min: sum of pre-game minutes averages of rotation players who play tonight.
    vacated_min: minutes averages of rotation players who played in one of the team's
    previous three games and are not playing tonight, each taken as it stood after that
    player's most recent appearance (so nothing from tonight is used).
    """
    rot = df[df.min_ewm5.fillna(0) >= ROTATION_MIN]
    present = rot.groupby(["gameId", "teamId"]).agg(
        rot_present_min=("min_ewm5", "sum"), rot_present_n=("min_ewm5", "size"))

    games = (df[["gameId", "teamId", "date"]].drop_duplicates()
             .sort_values(["teamId", "date", "gameId"]).reset_index(drop=True))
    games["k"] = games.groupby("teamId").cumcount()
    r = df[["gameId", "teamId", "personId", "min_ewm5_post"]].merge(
        games[["gameId", "teamId", "k"]], on=["gameId", "teamId"])
    rows = []
    for t, g in r.groupby("teamId"):
        by_k = {k: dict(zip(x.personId, x.min_ewm5_post)) for k, x in g.groupby("k")}
        for k in range(len(games[games.teamId == t])):
            tonight = by_k.get(k, {})
            last: dict[int, float] = {}
            for j in (k - 3, k - 2, k - 1):          # oldest first, so the latest wins
                last.update(by_k.get(j, {}))
            vac = sum(v for p, v in last.items() if p not in tonight and v >= ROTATION_MIN)
            rows.append((t, k, vac))
    vac = pd.DataFrame(rows, columns=["teamId", "k", "vacated_min"]).merge(games, on=["teamId", "k"])
    return present.reset_index().merge(vac[["gameId", "teamId", "vacated_min"]],
                                       on=["gameId", "teamId"], how="outer")


def build(box: pd.DataFrame) -> pd.DataFrame:
    df = player_features(box)
    df = df.merge(team_features(box), on=["gameId", "teamId"], how="left")
    df = df.merge(availability_features(df), on=["gameId", "teamId"], how="left")
    df["rot_present_min"] = df.rot_present_min.fillna(0)
    df["vacated_min"] = df.vacated_min.fillna(0)
    me_rot = (df.min_ewm5.fillna(0) >= ROTATION_MIN)
    others = df.rot_present_min - np.where(me_rot, df.min_ewm5.fillna(0), 0)
    df["others_present_min"] = others
    df["share_proj"] = df.min_ewm5 / (df.min_ewm5 + others).replace(0, np.nan) * 240
    return df


FEATURES_MIN = [
    "min_ewm5", "min_ewm25", "min_l3", "min_last", "min_season", "min_sd10",
    "starter_rate5", "starter_last", "gp_season", "gp_career", "days_rest", "b2b", "home",
    "exp_margin", "abs_exp_margin", "exp_total", "team_days_rest", "opp_days_rest",
    "rot_present_min", "rot_present_n", "vacated_min", "others_present_min", "share_proj",
]
FEATURES_RATE = FEATURES_MIN + [f"{s}_pm_{t}" for s in STATS for t in "sl"] + [
    "exp_team_pts", "exp_opp_pts", "opp_def_ewm"]


if __name__ == "__main__":
    box = pd.read_parquet(DATA / "box.parquet")
    feats = build(box)
    feats.to_parquet(DATA / "features.parquet", index=False)
    print(f"{len(feats):,} rows, {feats.shape[1]} columns -> {DATA / 'features.parquet'}")
