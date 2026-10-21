"""Distance each side travelled to a game, for the team model (adopted 21 Oct 2026, nrl/docs/RESEARCH_LOG.md).

Each venue's town comes from the weather game list (2009 on) and, for older venues, from RLP's venue table;
coordinates from the weather pull (towns.csv, two hand-set). A club's base is the town of most of its home
games. travel_diff = (away km - home km) / 1000. A game whose town has no coordinates counts as 0.
"""
import numpy as np
import pandas as pd

from nrl.data.link_cd import norm


def km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(lon2 - lon1)
    return 6371 * 2 * np.arcsin(np.sqrt(np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2))


def travel_by_game(cache, m):
    """m: matches with match_id, venue_id, home_team, away_team. Returns match_id -> travel_diff."""
    try:
        towns = pd.read_csv(f'{cache}/weather/towns.csv')
        games = pd.read_csv('nrl/weather/games.csv')[['match_id', 'town']]
        venues = pd.read_parquet(f'{cache}/venues.parquet').drop_duplicates('venue_id')
    except FileNotFoundError:
        return pd.Series(0.0, index=m.match_id)
    from nrl.weather.build_games import TOWN
    where = {t: (la, lo) for t, la, lo in zip(towns.town, towns.lat, towns.lon)}
    vt = dict(zip(venues.venue_id, venues.venue_name.map(TOWN).fillna(venues.cities)))
    vt[18] = 'Wellington'
    town = m.match_id.map(dict(zip(games.match_id, games.town)))
    town = town.fillna(m.venue_id.map(vt))
    lat = town.map(lambda t: where.get(t, (np.nan, np.nan))[0])
    lon = town.map(lambda t: where.get(t, (np.nan, np.nan))[1])
    d = pd.DataFrame(dict(match_id=m.match_id, h=m.home_team.map(norm), a=m.away_team.map(norm), lat=lat, lon=lon))
    base = d.dropna(subset=['lat']).groupby(['h', 'lat', 'lon']).size().rename('n').reset_index() \
        .sort_values('n').drop_duplicates('h', keep='last').set_index('h')
    hk = km(d.h.map(base.lat), d.h.map(base.lon), d.lat, d.lon)
    ak = km(d.a.map(base.lat), d.a.map(base.lon), d.lat, d.lon)
    return pd.Series(((ak - hk) / 1000).fillna(0.0).to_numpy(), index=d.match_id.to_numpy())
