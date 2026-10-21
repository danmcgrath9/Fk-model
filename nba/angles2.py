"""Our own angles: things a line might be slow or lazy about. Directions fixed BEFORE testing.

  1 ref_crew_hi / _lo  the three officials' free throws per 48 in their earlier games
                       (crews are named on game morning, before most props post)  -> pts over / under
  2 star_back          a teammate averaging 25+ minutes returns after missing 2+ games -> pts, ast under
  3 opp_big_out        the opponent is missing a big who averages 20+ minutes -> reb over, for bigs
  4 minutes_jump       last 3 games average 5+ minutes above his season average -> pts, reb, ast over
  5 hot_threes_last    made 2.5+ more threes than his rate predicted, last game -> fg3m, pts under
  6 tired              third game in four nights, or fourth+ straight road game -> pts under
  7 tank_bench / _starters   after 1 March, team winning under 35%: bench players -> pts over,
                       regular starters -> pts under
  8 new_team_early     first 10 games of a season for a player on a new team -> no direction set; shown
  9 fav_star_blowout   one of the team's two biggest-minutes players, team expected to win by 7+ -> pts under

Test A (all prop-able player-games 2024/25-2025/26): actual minus our model when the angle is on,
against when it is off, with a 95% bootstrap range by game. If our model already has it, ~0.
Test B (DunkAPI lines, 12 players): the angle's own side at the recorded price, each season.
Few lines will carry a rare angle; small samples are labelled, not trusted.

    python nba/angles2.py
"""
from __future__ import annotations

import glob
import re

import numpy as np
import pandas as pd

import angles as a1
import line_test as lt
import project as pr
from features import DATA

RULES = {  # angle -> [(stat, side)]
    "ref_crew_hi": [("pts", "over")], "ref_crew_lo": [("pts", "under")],
    "star_back": [("pts", "under"), ("ast", "under")],
    "opp_big_out": [("reb", "over")],
    "minutes_jump": [("pts", "over"), ("reb", "over"), ("ast", "over")],
    "hot_threes_last": [("fg3m", "under"), ("pts", "under")],
    "tired": [("pts", "under")],
    "tank_bench": [("pts", "over")], "tank_starters": [("pts", "under")],
    "new_team_early": [("pts", "?")],
    "fav_star_blowout": [("pts", "under")],
}


def referee_crews(box_games: pd.DataFrame) -> pd.DataFrame:
    """Per game: the mean, over its officials, of their free throws per 48 in EARLIER games."""
    rows = []
    for f in sorted(glob.glob(str(DATA / "raw/cdnnba_*.csv"))):
        if re.fullmatch(r"cdnnba_\d{4}\.csv", f.split("/")[-1]):
            d = pd.read_csv(f, usecols=["gameId", "officialId"], low_memory=False)
            rows.append(d[d.officialId.fillna(0) > 0].drop_duplicates())
    offs = pd.concat(rows).astype({"officialId": int})
    g = offs.merge(box_games, on="gameId").sort_values(["date", "gameId"])
    g["ref_prior"] = g.groupby("officialId").fta48.transform(
        lambda x: x.shift(1).ewm(halflife=15, min_periods=10).mean())
    return g.groupby("gameId").ref_prior.mean().rename("crew_fta48").reset_index()


def build(df: pd.DataFrame) -> pd.DataFrame:
    df = a1.add_angles(df)
    # game-level free throws per 48, both teams
    gm = df.groupby(["gameId", "date", "game_minutes"]).fta.sum().reset_index()
    gm["fta48"] = gm.fta * 48 / gm.game_minutes
    df = df.merge(referee_crews(gm[["gameId", "date", "fta48"]]), on="gameId", how="left")
    q = df.groupby("season").crew_fta48.transform(lambda s: s.rank(pct=True))
    df["ref_crew_hi"], df["ref_crew_lo"] = q >= 2 / 3, q <= 1 / 3

    # team-game index, for absences and returns
    tg = (df[["gameId", "teamId", "date"]].drop_duplicates().sort_values(["teamId", "date", "gameId"]))
    tg["k"] = tg.groupby("teamId").cumcount()
    df = df.merge(tg[["gameId", "teamId", "k"]], on=["gameId", "teamId"])
    df = df.sort_values(["teamId", "personId", "k"])
    gap = df.groupby(["teamId", "personId"]).k.diff()
    df["returner"] = (gap >= 3) & (df.min_ewm5 >= 25)
    back = df[df.returner].groupby(["gameId", "teamId"]).personId.apply(set).rename("returners")
    df = df.merge(back, on=["gameId", "teamId"], how="left")
    df["star_back"] = df.returners.apply(lambda s: isinstance(s, set)) & ~df.returner

    # bigs missing: a big (role big, 20+ minutes) who played in one of the team's last 3 games, not tonight
    bigs = df[(df.role == "big")][["teamId", "k", "personId", "min_ewm5_post"]]
    tonight = df.groupby(["teamId", "k"]).personId.apply(set)
    out = []
    for t, g in bigs.groupby("teamId"):
        by_k = {k: dict(zip(x.personId, x.min_ewm5_post)) for k, x in g.groupby("k")}
        for k in sorted(set(tonight.loc[t].index)):
            last = {}
            for j in (k - 3, k - 2, k - 1):
                last.update(by_k.get(j, {}))
            miss = sum(v for p, v in last.items() if v >= 20 and p not in tonight.loc[(t, k)])
            out.append((t, k, miss))
    bo = pd.DataFrame(out, columns=["teamId", "k", "big_out_min"])
    bo = bo.merge(tg[["gameId", "teamId", "k"]], on=["teamId", "k"])[["gameId", "teamId", "big_out_min"]]
    opp = bo.rename(columns={"teamId": "opp_teamId", "big_out_min": "opp_big_out_min"})
    df = df.merge(opp, on=["gameId", "opp_teamId"], how="left")
    df["opp_big_out"] = (df.opp_big_out_min >= 20) & (df.role == "big")

    df["minutes_jump"] = ((df.min_l3 - df.min_season) >= 5) & (df.gp_season >= 10)

    df = df.sort_values(["personId", "date", "gameId"])
    df["excess3"] = df.fg3m - df.fg3m_pm_l * df["min"]
    df["hot_threes_last"] = df.groupby("personId").excess3.shift(1) >= 2.5

    # fatigue: own 3rd game in 4 nights; 4th+ straight road game for the team
    two_back = df.groupby("personId").date.shift(2)
    df["three_in_four"] = (df.date - two_back).dt.days <= 3
    road = (tg.merge(df[["gameId", "teamId", "home"]].drop_duplicates(), on=["gameId", "teamId"])
            .sort_values(["teamId", "k"]))
    road["away"] = ~road.home
    road["streak"] = road.groupby((road.away != road.away.shift()).cumsum()).cumcount() + 1
    road["road_streak"] = np.where(road.away, road.streak, 0)
    df = df.merge(road[["gameId", "teamId", "road_streak"]], on=["gameId", "teamId"], how="left")
    df["tired"] = df.three_in_four | (df.road_streak >= 4)

    # tank: team win share in earlier games this season
    tw = (df.drop_duplicates(["gameId", "teamId"])[["gameId", "teamId", "season", "date", "team_pts", "opp_pts"]]
          .sort_values(["teamId", "date"]))
    tw["win"] = (tw.team_pts > tw.opp_pts).astype(float)
    tw["win_pct"] = tw.groupby(["teamId", "season"]).win.transform(lambda x: x.shift(1).expanding().mean())
    df = df.merge(tw[["gameId", "teamId", "win_pct"]], on=["gameId", "teamId"], how="left")
    late = df.date.dt.month.isin([3, 4]) & (df.win_pct < 0.35)
    df["tank_bench"] = late & (df.starter_rate5 < 0.5)
    df["tank_starters"] = late & (df.starter_rate5 >= 0.8)

    last_team = (df.groupby(["personId", "season"]).team.last().reset_index()
                 .assign(season=lambda x: x.season + 1).rename(columns={"team": "team_last_season"}))
    df = df.merge(last_team, on=["personId", "season"], how="left")
    df["new_team_early"] = df.team_last_season.notna() & (df.team != df.team_last_season) & (df.gp_season < 10)

    rank = df.groupby(["gameId", "teamId"]).min_ewm5.rank(ascending=False)
    df["fav_star_blowout"] = (rank <= 2) & (df.exp_margin >= 7)
    return df


def boot_diff(on, off, games_on, rng, n=1000):
    g = pd.DataFrame({"g": games_on, "r": on})
    s = g.groupby("g").r.agg(["sum", "size"])
    a, c = s["sum"].to_numpy(), s["size"].to_numpy()
    idx = rng.integers(0, len(s), (n, len(s)))
    boot = a[idx].sum(1) / c[idx].sum(1) - off.mean()
    return np.percentile(boot, 2.5), np.percentile(boot, 97.5)


def main() -> None:
    df = pd.read_parquet(DATA / "features.parquet")
    df = df[df.game_ok & df.min_ewm5.notna()]
    df = build(df)
    proj = pd.read_parquet(DATA / "projections.parquet")
    g = df.merge(proj[["gameId", "personId", *[f"{s}_proj" for s in a1.STATS]]], on=["gameId", "personId"])
    g = g[pr.propable(g)]
    rng = np.random.default_rng(0)

    L = lt.load_lines()
    L = L[L.actual.notna() & L.over_odds.notna()].copy()
    L["dec_over"], L["dec_under"] = lt.american_to_decimal(L.over_odds), lt.american_to_decimal(L.under_odds)
    d = df.assign(date=df.date.dt.strftime("%Y-%m-%d"))

    print("Angle               stat side  | Test A: games on, actual minus model (on - off), 95% | "
          "Test B: lines, side's ROI 24/25 (n) / 25/26 (n)")
    for angle, rules in RULES.items():
        for st, side in rules:
            on = g[g[angle]]
            off = g[~g[angle]]
            r_on = on[st] - on[f"{st}_proj"]
            r_off = off[st] - off[f"{st}_proj"]
            lo, hi = boot_diff(r_on.to_numpy(), r_off, on.gameId.to_numpy(), rng) if len(on) > 50 else (np.nan, np.nan)
            x = L[L.st == st].merge(d[["personId", "date", angle]], on=["personId", "date"])
            x = x[x[angle]]
            res = []
            for season, h in [("24/25", x[x.date < "2025-07-01"]), ("25/26", x[x.date >= "2025-07-01"])]:
                if side == "?":
                    res.append(f"over rate {(h.result == 'over').mean():.0%} ({len(h)})" if len(h) else "none")
                    continue
                dec = h.dec_over if side == "over" else h.dec_under
                pnl = np.where(h.result == "push", 0, np.where(h.result == side, dec - 1, -1))
                res.append(f"{pnl.mean():+.1%} ({len(h)})" if len(h) else "none")
            print(f"{angle:<19} {st:<4} {side:<5} | {len(on):>5} on: {r_on.mean() - r_off.mean():+.2f} "
                  f"[{lo:+.2f}, {hi:+.2f}] | {res[0]:>16} / {res[1]:>16}")


if __name__ == "__main__":
    main()
