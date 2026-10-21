"""The list of games to fetch weather for: one row per game from 2009, with the place and kick-off in UTC.

Place: the venue's town (RLP's city, corrected where RLP files a ground under the wrong city), geocoded on the
runner. Kick-off: Champion Data's UTC start where the game is linked (2014 on), otherwise RLP's local time in
the venue's time zone. Roofed grounds are flagged: their weather is the outside weather and is not used.

Writes nrl/weather/games.csv (committed; no secrets). Usage: python nrl/weather/build_games.py nrl/cache
"""
import sys

import numpy as np
import pandas as pd

TOWN = {  # RLP venue name -> the town it is really in, where RLP's city is the wrong one
    'Sunshine Coast Stadium': 'Kawana Waters', 'Kayo Stadium': 'Redcliffe', 'Campbelltown Sports Stadium': 'Campbelltown',
    'BlueBet Stadium': 'Penrith', 'Ocean Protect Stadium': 'Cronulla', '4 Pines Park': 'Brookvale',
    'CommBank Stadium': 'Parramatta', 'Parramatta Stadium': 'Parramatta', 'Jubilee Stadium': 'Kogarah',
    'Accor Stadium': 'Sydney Olympic Park', 'Belmore Sports Ground': 'Belmore', 'Leichhardt Oval': 'Leichhardt',
    'Go Media Stadium': 'Auckland',
}
CD_VENUE = {  # Champion Data names for games only Champion Data holds (2026 from round 16)
    '4 Pines Park': 'Brookvale', 'AAMI Park': 'Melbourne', 'Accor Stadium': 'Sydney Olympic Park',
    'Allegiant Stadium': 'Las Vegas', 'Allianz Stadium': 'Sydney', 'Campbelltown Sports Stadium': 'Campbelltown',
    'Carrington Park': 'Bathurst', 'Cbus Super Stadium': 'Gold Coast', 'CommBank Stadium': 'Parramatta',
    'Eden Park': 'Auckland', 'GIO Stadium': 'Canberra', 'Glen Willow Oval': 'Mudgee', 'Go Media Stadium': 'Auckland',
    'HBF Park': 'Perth', 'Industree Group Stadium': 'Gosford', 'Kayo Stadium': 'Redcliffe', 'Leichhardt Oval': 'Leichhardt',
    'McDonald Jones Stadium': 'Newcastle', 'Netstrata Jubilee Stadium': 'Kogarah', 'Ocean Protect Stadium': 'Cronulla',
    'One NZ Stadium': 'Christchurch', 'Optus Stadium': 'Perth', 'Queensland Country Bank Stadium': 'Townsville',
    'Sky Stadium': 'Wellington', 'Suncorp Stadium': 'Brisbane', 'TIO Stadium': 'Darwin', 'WIN Stadium': 'Wollongong',
}
ROOF = {'Marvel Stadium', 'Allegiant Stadium', 'Forsyth Barr Stadium', 'One New Zealand Stadium', 'One NZ Stadium'}
TZ = {'Queensland': 'Australia/Brisbane', 'Northern Territory': 'Australia/Darwin', 'Western Australia': 'Australia/Perth',
      'South Australia': 'Australia/Adelaide', 'Nevada': 'America/Los_Angeles'}


def main(cache):
    m = pd.read_parquet(f'{cache}/matches.parquet').dropna(subset=['home_team_score'])
    m = m[m.season >= 2009]
    v = pd.read_parquet(f'{cache}/venues.parquet').drop_duplicates('venue_id')
    m = m.merge(v[['venue_id', 'venue_name', 'cities', 'states', 'country']], on='venue_id', how='left')
    # venue 18 has no row in RLP's venue table: Champion Data names it Westpac (now Sky) Stadium, Wellington
    w = m.venue_id == 18
    m.loc[w, ['venue_name', 'cities', 'states', 'country']] = ['Sky Stadium', 'Wellington', 'Wellington', 'New Zealand']
    gl = pd.read_parquet(f'{cache}/cd_game_link.parquet')
    cp = pd.read_parquet(f'{cache}/cd_player_games.parquet').drop_duplicates('cd_match_id')[['cd_match_id', 'utc_start', 'venue']]
    cdg = cp.merge(gl, on='cd_match_id')
    m = m.merge(cdg[['match_id', 'utc_start']], on='match_id', how='left')
    town = m.venue_name.map(TOWN).fillna(m.cities)
    tz = m.states.map(TZ).fillna(pd.Series(np.where(m.country == 'New Zealand', 'Pacific/Auckland', 'Australia/Sydney'), index=m.index))
    local = pd.to_datetime(m.date.dt.strftime('%Y-%m-%d') + ' ' + m.time_24hr.fillna('19:00:00'))
    ko = [pd.Timestamp(u) if isinstance(u, str) else l.tz_localize(z, ambiguous=True, nonexistent='shift_forward')
          for u, l, z in zip(m.utc_start, local, tz)]
    out = pd.DataFrame(dict(match_id=m.match_id, town=town, country=m.country, venue=m.venue_name,
                            kick_off_utc=[pd.Timestamp(k).tz_convert('UTC').strftime('%Y-%m-%dT%H:%M') for k in ko],
                            roof=m.venue_name.isin(ROOF)))
    ext = cdg[cdg.match_id < 0]
    out = pd.concat([out, pd.DataFrame(dict(
        match_id=ext.match_id, town=ext.venue.map(CD_VENUE), country=np.where(ext.venue.isin(
            ['Eden Park', 'Go Media Stadium', 'One NZ Stadium', 'Sky Stadium']), 'New Zealand',
            np.where(ext.venue == 'Allegiant Stadium', 'United States of America', 'Australia')),
        venue=ext.venue, kick_off_utc=pd.to_datetime(ext.utc_start, utc=True).dt.strftime('%Y-%m-%dT%H:%M'),
        roof=ext.venue.isin(ROOF)))], ignore_index=True)
    missing = out[out.town.isna()]
    if len(missing):
        sys.exit(f'no town for venues: {sorted(missing.venue.astype(str).unique())}')
    out.to_csv('nrl/weather/games.csv', index=False)
    print(f'{len(out):,} games, {out.town.nunique()} towns, {out.roof.sum()} under a roof; '
          f'seasons {out.kick_off_utc.str[:4].min()}-{out.kick_off_utc.str[:4].max()}')


if __name__ == '__main__':
    main(sys.argv[1])
