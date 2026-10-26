"""Experiment: how fast team pace and efficiency forget old games (TEAM_DECAY, 0.90 a game, never tuned).
For each value, rebuild the team features and score the team model the usual way (rolling 2018-19 to
2022-23, then 2023-24 and 2024-25) on margin log loss and total miss.
Usage: python -m nbl.research.team_memory nbl/cache"""
import sys

import pandas as pd

from nbl.model import frame, team
from nbl.research.team_experiments import cv


def main(cache):
    results = pd.read_parquet(f'{cache}/results.parquet')
    box = pd.read_parquet(f'{cache}/box_player.parquet')
    games = frame.base_games(results)
    players = frame.base_players(box, games)
    p_cached = pd.read_parquet(f'{cache}/players.parquet')
    lv = frame.lineup_values(p_cached, frame.league_rates(players))
    rows = []
    for dec in (0.80, 0.85, 0.90, 0.94, 0.97):
        frame.TEAM_DECAY = dec
        tg = frame.team_features(frame.team_box(players, games), games).merge(lv, on=['game', 'team'], how='left')
        g = team.games_table(team.with_rapm(tg, cache))
        g = g[(g.games_prior_h >= 1) & (g.games_prior_a >= 1) & g.season.between(2016, 2024)]
        m = cv(g, team.MARGIN['named'], 'home_margin')
        t = cv(g, team.TOTAL['named'], 'total')
        rows.append(dict(decay=dec, margin_cv_ll=m['cv_ll'], margin_conf_ll=m['conf_ll'], total_cv_mae=t['cv_mae'],
                         total_conf_mae=t['conf_mae']))
        print(rows[-1], flush=True)
    print(pd.DataFrame(rows).round(4).to_string(index=False))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'nbl/cache')
