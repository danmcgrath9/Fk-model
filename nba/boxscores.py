"""Play-by-play (cdn.nba.com format) -> one row per player per game.

nba_data ships play-by-play, not box scores, so the box score is rebuilt here:

* counting stats (points, rebounds, assists, threes, attempts) are counted from events
  and cross-checked against the running totals cdn.nba.com stamps on each event
  (pointsTotal, reboundTotal, assistTotal);
* minutes come from substitutions: who started each period, then every SUB in/out.
  A player who plays a whole period without touching the ball and without a sub is
  invisible to the events, so a period that starts with fewer than five known players
  is filled from the five who finished the previous period.

Every team-game is checked: minutes must sum to 5 x game length and points must equal
the final score. Rows from games that fail are kept but flagged (`game_ok` False), so
the model can drop them and the drop rate is a number, not a guess.

    python nba/boxscores.py            # all seasons in nba/data/raw -> nba/data/box.parquet
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
COLS = [
    "gameId", "orderNumber", "period", "clock", "timeActual", "actionType", "subType",
    "personId", "teamId", "teamTricode", "shotResult", "assistPersonId",
    "pointsTotal", "reboundTotal", "assistTotal", "scoreHome", "scoreAway",
]
# Actions that prove a player was on the floor. Technical fouls and ejections are left
# out: a bench player can be given a technical.
ON_COURT_ACTIONS = {"2pt", "3pt", "freethrow", "rebound", "turnover", "steal", "block",
                    "jumpball", "violation", "foul"}
_CLOCK = re.compile(r"PT(\d+)M([\d.]+)S")


def clock_seconds(clock: str) -> float:
    """'PT11M43.00S' -> 703.0 seconds left in the period."""
    m = _CLOCK.fullmatch(clock)
    if not m:
        raise ValueError(f"unreadable clock {clock!r}")
    return int(m.group(1)) * 60 + float(m.group(2))


def period_length(period: int) -> float:
    return 720.0 if period <= 4 else 300.0


def _is_on_court_evidence(row) -> bool:
    if row.actionType not in ON_COURT_ACTIONS:
        return False
    if row.actionType == "foul" and row.subType == "technical":
        return False
    return row.personId > 0


def minutes_for_game(g: pd.DataFrame) -> tuple[dict, dict, list[str]]:
    """Seconds played and started-flag per (teamId, personId) for one game.

    `g` must be one game's events sorted by orderNumber. Returns (seconds, starters,
    problems); problems names any period whose starting five could not be resolved.
    """
    seconds: dict[tuple[int, int], float] = {}
    starters: dict[tuple[int, int], bool] = {}
    problems: list[str] = []
    teams = [int(t) for t in g.teamId.dropna().unique() if t > 0]
    prev_end: dict[int, set[int]] = {t: set() for t in teams}

    for period, p in g.groupby("period", sort=True):
        plen = period_length(int(period))
        status: dict[tuple[int, int], str] = {}
        for row in p.itertuples(index=False):
            if not (row.personId > 0 and row.teamId > 0):
                continue
            key = (int(row.teamId), int(row.personId))
            if key in status:
                continue
            if row.actionType == "substitution":
                status[key] = "on" if row.subType == "out" else "off"
            elif _is_on_court_evidence(row):
                status[key] = "on"
        on: dict[int, set[int]] = {t: {pid for (tt, pid), s in status.items() if tt == t and s == "on"}
                                   for t in teams}
        for t in teams:
            if len(on[t]) < 5:
                fill = [pid for pid in prev_end[t] if (t, pid) not in status]
                on[t] |= set(fill[: 5 - len(on[t])])
            if len(on[t]) != 5:
                problems.append(f"period {period} team {t}: {len(on[t])} on court at start")
            if period == 1:
                for pid in on[t]:
                    starters[(t, pid)] = True

        since = {(t, pid): plen for t in teams for pid in on[t]}
        for row in p[p.actionType == "substitution"].itertuples(index=False):
            key = (int(row.teamId), int(row.personId))
            now = clock_seconds(row.clock)
            if row.subType == "out":
                if key in since:
                    seconds[key] = seconds.get(key, 0.0) + since.pop(key) - now
                    on[key[0]].discard(key[1])
            else:
                if key not in since:
                    since[key] = now
                    on[key[0]].add(key[1])
        for key, start in since.items():
            seconds[key] = seconds.get(key, 0.0) + start
        prev_end = {t: set(on[t]) for t in teams}
    return seconds, starters, problems


def _home_team(g: pd.DataFrame) -> int | None:
    made = g[g.shotResult.eq("Made")].copy()
    prev_home = g.scoreHome.shift(1).fillna(0)
    up = (g.scoreHome - prev_home).loc[made.index]
    homes = made.loc[up > 0, "teamId"]
    return int(homes.mode().iloc[0]) if len(homes) else None


def box_for_game(g: pd.DataFrame) -> pd.DataFrame:
    g = g.sort_values("orderNumber")
    gid = int(g.gameId.iloc[0])
    seconds, starters, problems = minutes_for_game(g)

    made = g.shotResult.eq("Made")
    pts = np.select([g.actionType.eq("3pt") & made, g.actionType.eq("2pt") & made,
                     g.actionType.eq("freethrow") & made], [3, 2, 1], 0)
    ev = pd.DataFrame({
        "teamId": g.teamId, "personId": g.personId, "pts": pts,
        "fg3m": (g.actionType.eq("3pt") & made).astype(int),
        "fga": g.actionType.isin(["2pt", "3pt"]).astype(int),
        "fg3a": g.actionType.eq("3pt").astype(int),
        "fta": g.actionType.eq("freethrow").astype(int),
        "reb": g.actionType.eq("rebound").astype(int),
        "tov": g.actionType.eq("turnover").astype(int),
        "stl": g.actionType.eq("steal").astype(int),
        "blk": g.actionType.eq("block").astype(int),
    })
    ev = ev[(ev.personId > 0) & (ev.teamId > 0)]
    box = ev.groupby(["teamId", "personId"]).sum()
    ast = g[made & g.assistPersonId.gt(0)].groupby(["teamId", "assistPersonId"]).size()
    ast.index = ast.index.set_names(["teamId", "personId"])

    # cdn.nba.com's own running totals: the last value per player is their box score.
    run = g[(g.personId > 0) & (g.teamId > 0)].groupby(["teamId", "personId"])[
        ["pointsTotal", "reboundTotal"]].max()
    run_ast = g[g.assistPersonId.gt(0)].groupby(["teamId", "assistPersonId"]).assistTotal.max()
    run_ast.index = run_ast.index.set_names(["teamId", "personId"])

    keys = sorted(set(box.index) | set(seconds) | set(ast.index))
    out = pd.DataFrame(index=pd.MultiIndex.from_tuples(keys, names=["teamId", "personId"]))
    out = out.join(box).join(ast.rename("ast")).fillna(0)
    out["min"] = [seconds.get(k, 0.0) / 60 for k in keys]
    out["starter"] = [starters.get(k, False) for k in keys]
    out = out.join(run).join(run_ast.rename("assistTotal")).reset_index()
    out["pts_check"] = out.pts.eq(out.pointsTotal.fillna(0))
    out["reb_check"] = out.reb.eq(out.reboundTotal.fillna(0))
    out["ast_check"] = out.ast.eq(out.assistTotal.fillna(0))

    home = _home_team(g)
    final_home, final_away = int(g.scoreHome.iloc[-1]), int(g.scoreAway.iloc[-1])
    n_ot = max(0, int(g.period.max()) - 4)
    game_minutes = 48 + 5 * n_ot
    team_min = out.groupby("teamId")["min"].sum()
    team_pts = out.groupby("teamId")["pts"].sum()
    minutes_ok = bool((team_min.sub(5 * game_minutes).abs() < 0.5).all() and len(team_min) == 2)
    points_ok = home is not None and len(team_pts) == 2 and \
        team_pts.get(home, -1) == final_home and team_pts.drop(home).iloc[0] == final_away

    out["gameId"] = gid
    out["date"] = (pd.to_datetime(g.timeActual.iloc[0], utc=True)
                   .tz_convert("America/New_York").date().isoformat())
    out["home"] = out.teamId.eq(home)
    out["team_pts"] = out.teamId.map(team_pts)
    out["opp_pts"] = out.teamId.map(lambda t: team_pts.drop(t).sum())
    out["game_minutes"] = game_minutes
    out["minutes_ok"] = minutes_ok
    out["points_ok"] = bool(points_ok)
    out["game_ok"] = minutes_ok and bool(points_ok) and not problems
    out["problems"] = "; ".join(problems)
    tri = g.dropna(subset=["teamTricode"]).groupby("teamId").teamTricode.first()
    out["team"] = out.teamId.map(tri)
    out["opp_teamId"] = out.teamId.map(lambda t: [x for x in team_min.index if x != t][0]
                                       if len(team_min) == 2 else np.nan)
    return out.drop(columns=["pointsTotal", "reboundTotal", "assistTotal"])


def build_season(csv: Path) -> pd.DataFrame:
    df = pd.read_csv(csv, usecols=COLS, low_memory=False)
    for c in ["personId", "teamId", "assistPersonId", "pointsTotal", "reboundTotal", "assistTotal"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    # Regular season only (game id 2YY...). Playoffs are a different rotation game.
    df = df[df.gameId.astype(str).str.zfill(10).str[2] == "2"]
    parts = [box_for_game(g) for _, g in df.groupby("gameId", sort=True)]
    box = pd.concat(parts, ignore_index=True)
    box["season"] = int(re.search(r"(\d{4})", csv.name).group(1))
    return box


def main(argv: list[str]) -> None:
    files = sorted((DATA / "raw").glob("cdnnba_*.csv"))
    files = [f for f in files if re.fullmatch(r"cdnnba_\d{4}\.csv", f.name)]
    seasons = [build_season(f) for f in files]
    box = pd.concat(seasons, ignore_index=True)
    box = box[box["min"] > 0].copy()          # appeared on the floor
    box.to_parquet(DATA / "box.parquet", index=False)
    games = box.drop_duplicates("gameId")
    print(f"{len(box):,} player-games from {len(games):,} games, seasons {sorted(box.season.unique())}")
    for col in ["minutes_ok", "points_ok", "game_ok"]:
        print(f"  {col}: {games[col].mean():.2%} of games")
    for col in ["pts_check", "reb_check", "ast_check"]:
        print(f"  {col}: {box[col].mean():.2%} of player-games match cdn.nba.com running totals")


if __name__ == "__main__":
    main(sys.argv[1:])
