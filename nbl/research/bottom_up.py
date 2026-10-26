"""Experiment (Ewing-lite): a bottom-up team total. Each squad's expected points = sum over the players who dressed
of (per-minute scoring rate x his share of the team's 200 minutes), scaled by the game's expected pace against the
league; the game's bottom-up total = both squads. Added to the total model; scored rolling 2018-19 to 2022-23, then
2023-24 and 2024-25. Usage: python -m nbl.research.bottom_up nbl/cache"""
import sys

import pandas as pd

from nbl.model import team
from nbl.research.team_experiments import cv


def main(cache):
    p = pd.read_parquet(f'{cache}/players.parquet')
    p = p[p.played.notna()]
    p['bu'] = p.r_pts * p.min_scaled.fillna(0)
    sq = p.groupby(['game', 'team'], as_index=False).agg(bu_pts=('bu', 'sum'), pace=('pace_rel', 'first'))
    sq['bu_pts_pace'] = sq.bu_pts * sq.pace.fillna(1.0)
    tg = team.with_rapm(pd.read_parquet(f'{cache}/teams.parquet'), cache).merge(sq, on=['game', 'team'], how='left')
    g = team.games_table(tg)
    h = tg[tg.is_home == 1][['game', 'bu_pts', 'bu_pts_pace']]; a = tg[tg.is_home == 0][['game', 'bu_pts', 'bu_pts_pace']]
    g = g.merge(h.merge(a, on='game', suffixes=('_h', '_a')), on='game')
    g['bu_total'] = g.bu_pts_h + g.bu_pts_a
    g['bu_total_pace'] = g.bu_pts_pace_h + g.bu_pts_pace_a
    g['bu_margin'] = g.bu_pts_pace_h - g.bu_pts_pace_a
    g = g[(g.games_prior_h >= 1) & (g.games_prior_a >= 1) & g.season.between(2016, 2024)]
    print(g[['bu_total_pace', 'exp_total', 'total']].corr().round(3).to_string())
    rows = []
    for name, cols, tgt in (('total: current', team.TOTAL['named'], 'total'),
                            ('total: + bottom-up', team.TOTAL['named'] + ['bu_total_pace'], 'total'),
                            ('total: bottom-up instead of team-level', [c for c in team.TOTAL['named'] if c != 'exp_total'] + ['bu_total_pace'], 'total'),
                            ('margin: current', team.MARGIN['named'], 'home_margin'),
                            ('margin: + bottom-up', team.MARGIN['named'] + ['bu_margin'], 'home_margin')):
        x = cv(g, cols, tgt); x['name'] = name; rows.append(x)
    print(pd.DataFrame(rows)[['name', 'lam', 'cv_mae', 'conf_mae', 'cv_ll', 'conf_ll']].round(4).to_string(index=False))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'nbl/cache')
