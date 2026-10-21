"""Listed positions (and height, weight) for every NBA player, from the NBA's own player index.

Source: stats.nba.com `playerindex`, read with the nba_api package (github.com/swar/nba_api).
One call per season, 2020-21 to 2025-26, so six requests in all. Runs in the
`nba positions pull` GitHub workflow (the cloud box cannot reach stats.nba.com) and writes
nba/players/positions.csv: personId, season, name, team, POSITION (G, F, C, G-F, F-C ...),
height, weight. A listed position is the team's label, not what a player does on the floor;
our own guard / wing / big groups (angles.py) are kept beside it, not replaced.

    python nba/pull_positions.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent / "players" / "positions.csv"
SEASONS = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]


def main() -> int:
    from nba_api.stats.endpoints import playerindex

    frames, failed = [], []
    for season in SEASONS:
        for attempt in range(3):
            try:
                df = playerindex.PlayerIndex(season=season, timeout=90).get_data_frames()[0]
                frames.append(df.assign(season=int(season[:4])))
                print(f"{season}: {len(df)} players")
                break
            except Exception as exc:          # stats.nba.com is slow and drops requests
                print(f"{season}: attempt {attempt + 1} failed ({type(exc).__name__})")
                time.sleep(10 * (attempt + 1))
        else:
            failed.append(season)
        time.sleep(3)
    if not frames:
        print("Nothing came back from stats.nba.com.")
        return 1
    out = pd.concat(frames, ignore_index=True)
    out = out.rename(columns={"PERSON_ID": "personId"})[
        ["personId", "season", "PLAYER_FIRST_NAME", "PLAYER_LAST_NAME", "TEAM_ABBREVIATION",
         "POSITION", "HEIGHT", "WEIGHT", "DRAFT_YEAR", "FROM_YEAR"]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"{len(out):,} rows -> {OUT}" + (f"; FAILED seasons: {failed}" if failed else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
