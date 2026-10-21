"""Join the official injury reports to our players, and check them against what happened.

The report names players "Last, First" and teams by full name, so a row is matched to our
box scores by (game date, team, last name, first initial), the same name form cdn.nba.com's
play-by-play carries ("J. Brunson"). Rows that match no one, or more than one player, are
counted and left out, never guessed.

The check: a player the LAST report before the game listed as Out should not have played.
If the reports and the join are right, that is close to 100%.

    python nba/injuries_check.py
"""
from __future__ import annotations

import glob
import re
import unicodedata
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
TEAMS = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN", "Charlotte Hornets": "CHA",
    "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE", "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET", "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "LA Clippers": "LAC", "Los Angeles Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN", "New Orleans Pelicans": "NOP",
    "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC", "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHX", "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS",
}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


def name_key(last: str, first_initial: str) -> str:
    # Suffixes sit on the last name in both sources ("Smith Jr."), so drop them in both.
    last = re.sub(r"\b(jr|sr|ii|iii|iv)\.?$", "", str(last).strip(), flags=re.I)
    return norm(last) + "_" + norm(first_initial)[:1]


def load_reports() -> pd.DataFrame:
    files = [f for f in glob.glob(str(HERE / "injuries/raw/*.csv")) if not f.endswith("_log.csv")]
    rep = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    rep = rep.dropna(subset=["Player Name", "Current Status"])
    rep["date"] = pd.to_datetime(rep["Game Date"], format="%m/%d/%Y").dt.strftime("%Y-%m-%d")
    rep["team"] = rep["Team"].map(TEAMS)
    parts = rep["Player Name"].str.split(",", n=1, expand=True)
    rep["key"] = [name_key(l, f) for l, f in zip(parts[0], parts[1].fillna(""))]
    return rep


def player_names() -> pd.DataFrame:
    """personId -> name key, from the play-by-play's 'J. Brunson' / 'Brunson' fields."""
    rows = []
    for f in sorted(glob.glob(str(DATA / "raw/cdnnba_*.csv"))):
        if not re.fullmatch(r"cdnnba_\d{4}\.csv", Path(f).name):
            continue
        p = pd.read_csv(f, usecols=["personId", "playerName", "playerNameI"], low_memory=False).dropna()
        rows.append(p.drop_duplicates("personId"))
    p = pd.concat(rows).drop_duplicates("personId", keep="last")
    p["key"] = [name_key(last, ni.split(".")[0]) for last, ni in zip(p.playerName, p.playerNameI)]
    p["personId"] = p.personId.astype(int)
    return p[["personId", "key"]]


def joined() -> pd.DataFrame:
    rep = load_reports()
    box = pd.read_parquet(DATA / "box.parquet")[["gameId", "date", "season", "team", "personId", "min"]]
    names = player_names()
    # Candidates: anyone who played for that team that season, by name key. (A player out
    # all season never appears in a box score, so cannot be matched: counted as "none".)
    d = pd.to_datetime(rep.date)
    rep["season"] = d.dt.year - (d.dt.month < 8).astype(int)
    season_rosters = box.merge(names, on="personId")[["season", "team", "personId", "key"]].drop_duplicates()
    m = rep.merge(season_rosters, on=["season", "team", "key"], how="left")
    hits = m.groupby(["report_time", "date", "team", "key"]).personId.transform("nunique")
    m["match"] = pd.Series(pd.NA, index=m.index, dtype="object")
    m.loc[hits == 1, "match"] = "one"
    m.loc[hits > 1, "match"] = "several"
    m.loc[m.personId.isna(), "match"] = "none"
    return m, box


def main() -> None:
    m, box = joined()
    print(f"{m.report_time.nunique()} reports, {len(m.drop_duplicates(['report_time', 'Player Name'])):,} rows")
    u = m.drop_duplicates(["report_time", "date", "team", "key"])
    print("name join:", u.match.value_counts(normalize=True).round(4).to_dict())
    one = m[m.match == "one"].copy()
    one["report_dt"] = pd.to_datetime(one.report_time)
    one["game_dt"] = pd.to_datetime(one.date)
    # last report that was filed before 7pm on game day (the latest snapshot we fetch)
    one = one[one.report_dt <= one.game_dt + pd.Timedelta(hours=19)]
    last = one.sort_values("report_dt").groupby(["date", "personId"]).tail(1)
    played = box.groupby(["date", "personId"])["min"].sum().rename("min_played").reset_index()
    last = last.merge(played, on=["date", "personId"], how="left")
    last["played"] = last.min_played.fillna(0) > 0
    print("\nLast report before tip-off, by status: share who then played")
    print(last.groupby("Current Status").played.agg(["size", "mean"]).round(3).to_string())
    last.to_parquet(DATA / "injuries_last.parquet", index=False)


if __name__ == "__main__":
    main()
