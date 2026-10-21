"""One row per team per match, with only what was knowable before kick-off.

Built from aleague-history's matches.parquet. Every rolling figure is shifted one match, so a row
never contains its own match's goals (aleague/tests/test_team_games.py changes a result and checks).

Columns per row: match and team identity, home / away / neutral ground, the result (target columns,
prefixed y_), and features:
  gf_last5, ga_last5        goals for and against, mean of the previous five league matches
  gf_ewm, ga_ewm            exponentially weighted (span 10) goals for and against before this match
  rest_days                 days since the team's previous league match (None for its first)
  long_trip                 the team crossed to or from Perth or New Zealand for this match
  season_game               the team's match number within the season (1 = first)

Usage: python -m aleague.data.team_games <tables dir>   (writes team_games.parquet beside matches)
"""
import sys

import numpy as np
import pandas as pd

# clubs a long flight from the east-coast cluster (Adelaide sits between and is left out)
FAR = {'Perth Glory', 'Wellington Phoenix', 'Auckland FC'}


def long_trip(team, home, away, neutral):
    """True when the team travels to, or a far club travels from, a far base."""
    if team == home and not neutral:
        return False
    other = away if team == home else home
    venue_far = (not neutral) and other in FAR
    return bool(venue_far or (team in FAR))


def build(matches):
    m = matches[matches.home_goals_90.notna()].sort_values(['date', 'match_id'])
    rows = []
    for _, g in m.iterrows():
        for side, team, opp, gf, ga in (('home', g.home, g.away, g.home_goals_90, g.away_goals_90),
                                        ('away', g.away, g.home, g.away_goals_90, g.home_goals_90)):
            rows.append(dict(match_id=g.match_id, season=g.season, date=g.date, team=team, opponent=opp,
                             is_home=side == 'home', neutral=bool(g.neutral), stage=g.stage,
                             long_trip=long_trip(team, g.home, g.away, bool(g.neutral)),
                             y_gf=float(gf), y_ga=float(ga)))
    t = pd.DataFrame(rows).sort_values(['team', 'date', 'match_id']).reset_index(drop=True)
    grp = t.groupby('team', sort=False)
    t['gf_last5'] = grp.y_gf.transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    t['ga_last5'] = grp.y_ga.transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    t['gf_ewm'] = grp.y_gf.transform(lambda s: s.shift(1).ewm(span=10, min_periods=1).mean())
    t['ga_ewm'] = grp.y_ga.transform(lambda s: s.shift(1).ewm(span=10, min_periods=1).mean())
    prev = grp.date.shift(1)
    t['rest_days'] = [(d - p).days if isinstance(p, type(d)) else np.nan for d, p in zip(t.date, prev)]
    t['season_game'] = t.groupby(['team', 'season']).cumcount() + 1
    return t.sort_values(['date', 'match_id', 'is_home'], ascending=[True, True, False]).reset_index(drop=True)


if __name__ == '__main__':
    d = sys.argv[1]
    tg = build(pd.read_parquet(f'{d}/matches.parquet'))
    tg.to_parquet(f'{d}/team_games.parquet', index=False)
    print(f'team_games: {len(tg):,} rows, {tg.team.nunique()} teams, seasons {tg.season.min()}-{tg.season.max()}')
