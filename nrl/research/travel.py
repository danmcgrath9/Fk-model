"""Travel: does the distance each side flew change the margin? (UTS 2007-2019: about 1.1 points per 1,000 km.)

Each club's base is the town it plays most home games in; each game's distance per side is the great-circle
distance from that base to the venue's town (coordinates from the weather pull, towns.csv). Feature:
(away km - home km) / 1000, which also captures neutral and relocated games. Scored with the harness.
Usage: python -m nrl.research.travel nrl/cache
"""
import sys

import numpy as np
import pandas as pd

from nrl.model import team
from nrl.model.team_frame import FEATURES_NAMED
from nrl.research.harness import score_variant


def km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(lon2 - lon1)
    return 6371 * 2 * np.arcsin(np.sqrt(np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2))


def travel(cache):
    games = pd.read_csv('nrl/weather/games.csv')[['match_id', 'town', 'country']]
    towns = pd.read_csv(f'{cache}/weather/towns.csv')[['town', 'country', 'lat', 'lon']]
    games = games.merge(towns, on=['town', 'country'])
    g = team.games(pd.read_parquet(f'{cache}/team_frame.parquet')).merge(games, on='match_id', how='inner')
    base = pd.concat([g[['team', 'lat', 'lon']], g[['opp', 'lat', 'lon']].iloc[:0].rename(columns={'opp': 'team'})])
    base = base.groupby(['team', 'lat', 'lon']).size().rename('n').reset_index().sort_values('n').drop_duplicates('team', keep='last')
    b = base.set_index('team')
    g['home_km'] = km(g.team.map(b.lat), g.team.map(b.lon), g.lat, g.lon)
    g['away_km'] = km(g.opp.map(b.lat), g.opp.map(b.lon), g.lat, g.lon)
    g['travel_diff'] = (g.away_km - g.home_km) / 1000
    return g, base


def main(cache):
    g, base = travel(cache)
    print(base.to_string(index=False))
    print(f'{len(g):,} games; median away trip {g.away_km.median():.0f} km')
    out = []
    for name, feats in (('teams named', FEATURES_NAMED), ('+ travel', FEATURES_NAMED + ['travel_diff']),
                        ('ratings only', ['exp_margin']), ('ratings + travel', ['exp_margin', 'travel_diff'])):
        r, mm, _ = score_variant(g, feats, label=name)
        out.append(r)
        if 'travel' in name:
            print(name, 'travel coefficient (points per 1,000 km, home view):', round(mm.coef[-1], 2))
    print(pd.concat(out)[['variant', 'set', 'bits', 'logloss', 'mae_margin']].round(4).to_string(index=False))


if __name__ == '__main__':
    main(sys.argv[1])
