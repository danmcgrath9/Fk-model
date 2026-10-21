"""Daily paper projections for today's NBA games, made BEFORE tip-off and saved with a timestamp.

Data, all free and published (no scraping by us):
  * box scores and the season schedule: SportsDataVerse's public release files on GitHub
    (github.com/sportsdataverse/sportsdataverse-data, from ESPN, refreshed through the season).
    Checked against the official NBA data on 2025/26: 99.9% of player-games matched; points,
    rebounds, assists and threes identical in 99.7-99.9%, minutes within 1 in 99.8%.
  * who is out: the NBA's official injury report (nbainjuries), the latest one filed.
Model: the same features and LightGBM settings as project.py, trained on every finished game
from 2021/22 to yesterday; "who plays tonight" from the injury report exactly as at_report.py
does it (Out/Doubtful missing, Questionable half). Spread of outcomes: live/variance.json,
fitted on 2023/24 out-of-sample misses (probability.py).

Writes nba/live/projections/<date>_<HHMM>ET.csv, and scores earlier days against what
happened in nba/live/scorecard.csv. Paper only: nothing is bet. (Needs lightgbm with scikit-learn, nbainjuries with Java.)

    python nba/live/daily.py            # today, US Eastern
    python nba/live/daily.py 2026-10-22
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import lightgbm as lgb
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import at_report as ar  # noqa: E402
import features as F  # noqa: E402
import injuries_check as ic  # noqa: E402
import project as pr  # noqa: E402

ET = ZoneInfo("America/New_York")
SDV = "https://github.com/sportsdataverse/sportsdataverse-data/releases/download"
CACHE = HERE.parent / "data" / "sdv"
FIRST_SEASON = 2022                      # SportsDataVerse names a season by its end year
ESPN_TO_NBA = {"GS": "GSW", "NY": "NYK", "NO": "NOP", "SA": "SAS", "UTAH": "UTA", "WSH": "WAS"}


def fetch(path: str, refresh: bool) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / path.split("/")[-1]
    if refresh or not out.exists():
        urllib.request.urlretrieve(f"{SDV}/{path}", out)
    return out


def load(current: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    boxes = [pd.read_parquet(fetch(f"espn_nba_player_boxscores/player_box_{s}.parquet", s == current))
             for s in range(FIRST_SEASON, current + 1)]
    sched = pd.read_parquet(fetch(f"espn_nba_schedules/nba_schedule_{current}.parquet", True))
    return pd.concat(boxes, ignore_index=True), sched


def to_box(e: pd.DataFrame) -> pd.DataFrame:
    """ESPN rows -> the box-score shape features.py expects (regular season, played only)."""
    e = e[(e.season_type == 2) & (e.did_not_play != True) & (e.minutes.fillna(0) > 0)].copy()  # noqa: E712
    b = pd.DataFrame({
        "gameId": e.game_id.astype(int), "personId": e.athlete_id.astype(int), "teamId": e.team_id.astype(int),
        "opp_teamId": e.opponent_team_id.astype(int), "date": pd.to_datetime(e.game_date).dt.strftime("%Y-%m-%d"),
        "season": e.season.astype(int) - 1, "home": e.home_away.eq("home"),
        "team": e.team_abbreviation.replace(ESPN_TO_NBA), "name": e.athlete_display_name,
        "min": e.minutes.astype(float), "starter": e.starter.astype(float),
        "pts": e.points, "reb": e.rebounds, "ast": e.assists, "fg3m": e.three_point_field_goals_made,
        "fg3a": e.three_point_field_goals_attempted, "fga": e.field_goals_attempted,
        "fta": e.free_throws_attempted, "tov": e.turnovers, "stl": e.steals, "blk": e.blocks,
        "team_pts": e.team_score.astype(float), "opp_pts": e.opponent_team_score.astype(float)})
    team_min = b.groupby(["gameId", "teamId"])["min"].transform("sum")
    b["game_minutes"] = 48 + 5 * ((team_min / 5 - 48) / 5).round().clip(lower=0)
    b["game_ok"] = True
    return b


def slate(sched: pd.DataFrame, day: str) -> pd.DataFrame:
    s = sched[(pd.to_datetime(sched.game_date).dt.strftime("%Y-%m-%d") == day) & (sched.type_id == 1)]
    return s[["game_id", "start_date", "home_id", "away_id", "home_abbreviation", "away_abbreviation"]]


def placeholders(box: pd.DataFrame, games: pd.DataFrame, day: str) -> pd.DataFrame:
    """Tonight's rows, one per player whose latest appearance was for that team within the
    last 200 days. Their stats are blank; every feature comes from earlier games."""
    last = box.sort_values("date").groupby("personId").tail(1)
    recent = last[pd.to_datetime(last.date) >= pd.to_datetime(day) - timedelta(days=200)]
    rows = []
    for g in games.itertuples():
        for team, opp, home in [(g.home_id, g.away_id, True), (g.away_id, g.home_id, False)]:
            for p in recent[recent.teamId == int(team)].itertuples():
                rows.append({"gameId": int(g.game_id), "personId": p.personId, "teamId": int(team),
                             "opp_teamId": int(opp), "date": day, "home": home, "team": p.team, "name": p.name,
                             "season": int(box.season.max()), "game_ok": True, "game_minutes": 48,
                             "starter": np.nan, "tip": g.start_date})
    return pd.DataFrame(rows)


def latest_report(now_et: datetime):
    """The newest official injury report filed by now (15-minute files since Dec 2025)."""
    from nbainjuries import injury
    t = now_et.replace(second=0, microsecond=0, tzinfo=None)
    t -= timedelta(minutes=t.minute % 15)
    for _ in range(12):
        try:
            return t, injury.get_reportdata(t, return_df=True)
        except Exception:
            t -= timedelta(minutes=15)
    return None, None


def report_status(rep: pd.DataFrame, tonight: pd.DataFrame, day: str, label: str) -> pd.DataFrame:
    """Report rows -> (date, personId, report_time, Current Status), by team + full name, or
    team + last name and first initial when the full name differs (Jr., accents)."""
    if rep is None or rep.empty:
        return pd.DataFrame({"date": pd.Series(dtype=str), "personId": pd.Series(dtype=int),
                             "report_time": pd.Series(dtype=str), "Current Status": pd.Series(dtype=str)})
    rep = rep.dropna(subset=["Player Name", "Current Status"]).copy()
    rep["team"] = rep["Team"].map(ic.TEAMS)
    parts = rep["Player Name"].str.split(",", n=1, expand=True)
    rep["full"] = (parts[1].fillna("") + parts[0]).map(ic.norm)
    rep["key"] = [ic.name_key(last, first) for last, first in zip(parts[0], parts[1].fillna(""))]
    t = tonight[["personId", "team", "name"]].drop_duplicates("personId").copy()
    np_ = t.name.str.split(" ", n=1, expand=True)
    t["full"] = t.name.map(ic.norm)
    t["key"] = [ic.name_key(last, first) for first, last in zip(np_[0], np_[1].fillna(""))]
    a = rep.merge(t[["team", "full", "personId"]], on=["team", "full"], how="inner")
    b = rep[~rep.full.isin(a.full)].merge(t[["team", "key", "personId"]], on=["team", "key"], how="inner")
    s = pd.concat([a, b]).drop_duplicates("personId")
    return pd.DataFrame({"date": day, "personId": s.personId.astype(int), "report_time": f"{day} {label}",
                         "Current Status": s["Current Status"].astype(str)}).astype({"date": str, "report_time": str})


def score_past(box: pd.DataFrame) -> None:
    files = sorted((HERE / "projections").glob("*.csv"))
    if not files:
        return
    rows = []
    for f in files:
        p = pd.read_csv(f)
        a = p.merge(box[["date", "personId", "min", "pts", "reb", "ast", "fg3m"]], on=["date", "personId"])
        if a.empty:
            continue
        rows.append({"file": f.name, "players": len(a), **{f"miss_{s}": (a[f"{s}_proj"] - a[s]).abs().mean()
                                                            for s in ["min", "pts", "reb", "ast", "fg3m"]}})
    if rows:
        pd.DataFrame(rows).round(3).to_csv(HERE / "scorecard.csv", index=False)


def main(argv: list[str]) -> int:
    now = datetime.now(ET)
    day = argv[0] if argv else now.strftime("%Y-%m-%d")
    current = int(day[:4]) + (1 if int(day[5:7]) >= 8 else 0)
    raw, sched = load(current)
    box = to_box(raw)
    score_past(box)
    games = slate(sched, day)
    if games.empty:
        print(f"{day}: no NBA games scheduled.")
        return 0
    box = box[box.date < day]
    tonight = placeholders(box, games, day)
    df = F.build(pd.concat([box, tonight.drop(columns=["tip"])], ignore_index=True))
    when, rep = latest_report(now) if not argv else (None, None)
    label = when.strftime("%H:%M") if when else "none"
    status = report_status(rep, tonight, day, label)
    train = df[(df.date < pd.Timestamp(day)) & df.min_ewm5.notna() & df["min"].notna()]
    test = df[df.date == pd.Timestamp(day)].copy()
    av = ar.availability_at(test, status, label, 0)
    x = test.drop(columns=ar.AVAIL).merge(av, on=["gameId", "teamId", "personId"], how="left")
    m_min = lgb.LGBMRegressor(**pr.PARAMS, random_state=1).fit(train[F.FEATURES_MIN], train["min"])
    tr = train[train["min"] >= 1]
    x["min_proj"] = np.clip(m_min.predict(x[F.FEATURES_MIN]), 0, 48)
    for st in pr.TARGETS:
        m = lgb.LGBMRegressor(**pr.PARAMS, random_state=2).fit(tr[F.FEATURES_RATE], tr[st] / tr["min"],
                                                                sample_weight=tr["min"])
        x[f"{st}_proj"] = x.min_proj * np.clip(m.predict(x[F.FEATURES_RATE]), 0, None)
    x = x.merge(tonight[["gameId", "personId", "tip"]], on=["gameId", "personId"])
    out = x[(x.min_ewm5 >= 10) & ~x.own_status.isin(["Out", "Doubtful"])]
    cols = ["date", "tip", "gameId", "team", "personId", "name", "own_status", "min_ewm5", "min_proj",
            *[f"{s}_proj" for s in pr.TARGETS]]
    out = out[cols].sort_values(["tip", "gameId", "team", "min_proj"], ascending=[True, True, True, False])
    dest = HERE / "projections" / f"{day}_{label.replace(':', '')}ET.csv"
    dest.parent.mkdir(exist_ok=True)
    out.round(2).to_csv(dest, index=False)
    print(f"{day}: {len(games)} games, {len(out)} players projected, injury report {label} ET "
          f"({len(status)} players matched to it) -> {dest.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
