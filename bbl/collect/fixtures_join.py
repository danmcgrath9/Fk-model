"""Join the Wikipedia fixtures to Cricsheet by Cricinfo match id, and write the coming seasons' fixture lists.

Outputs
  match_context.parquet   one row per Cricsheet BBL/WBBL match: local start time, night game, the home side
                          where the page marks it "(H)", attendance; date_mismatch flags the 4 games whose
                          Wikipedia date differs from Cricsheet's (their start time is then not used)
  bbl/live/fixtures_<season>.csv   the pricer's input (date, team1, team2, venue, gender, comp) for every
                          fixture Cricsheet does not hold yet, home side first where marked

Usage: python -m bbl.collect.fixtures_join <wiki_fixtures.csv> <parquet dir> <live dir>
"""
import os
import sys

import pandas as pd


def main(fx_path, d, live):
    f = pd.read_csv(fx_path, dtype={'cricinfo_id': str})
    m = pd.read_parquet(os.path.join(d, 't20_matches.parquet'))
    m = m[m.competition.isin(['Big Bash League', "Women's Big Bash League"])]
    j = m[['match_id', 'start_date', 'competition', 'team1', 'team2']].merge(
        f.drop(columns=['competition', 'team1', 'team2']), left_on='match_id', right_on='cricinfo_id', how='left')
    j['date_mismatch'] = j.date.notna() & (j.date != j.start_date)
    j.loc[j.date_mismatch, 'local_time'] = None
    hour = pd.to_numeric(j.local_time.astype('string').str.split(':').str[0], errors='coerce')
    j['start_hour'] = hour
    ctx = j[['match_id', 'local_time', 'start_hour', 'night', 'home_team', 'attendance', 'date_mismatch', 'source_revid']]
    # fixtures from the current season's pages alone join no held match: then the held match_context is left
    # alone rather than overwritten with an empty one (the daily price run reads only those two pages)
    if j.cricinfo_id.notna().any():
        ctx.to_parquet(os.path.join(d, 'match_context.parquet'), index=False)
        print(f'match_context: {len(ctx)} matches, {ctx.local_time.notna().sum()} with a start time, '
              f'{ctx.home_team.notna().sum()} with a marked home side, {int(ctx.date_mismatch.sum())} date mismatches')
    else:
        print('these fixtures join no held match: match_context left as it is')

    # fixtures Cricsheet does not hold: the pricer's input, per season
    held = set(m.match_id)
    up = f[~f.cricinfo_id.isin(held) & f.date.notna() & f.team1.notna() & f.team2.notna()].copy()
    up = up[pd.to_datetime(up.date) >= pd.Timestamp.today().normalize() - pd.Timedelta(days=1)]
    # finals read "1st placed team" until they are decided, and a few venues read TBC: not priceable yet
    clubs = set(m.team1) | set(m.team2)
    dropped = up[~(up.team1.isin(clubs) & up.team2.isin(clubs)) | up.venue_full.fillna('TBC').str.match(r'TB[CD]')]
    up = up.drop(dropped.index)
    if len(dropped):
        print(f'{len(dropped)} fixtures not yet priceable (finals placeholders or venue TBC): '
              + '; '.join(f'{r.date} {r.team1} v {r.team2}' for r in dropped.itertuples()))
    if up.empty:
        print('no upcoming fixtures')
        return
    up['gender'] = up.competition.map(lambda c: 'female' if "Women's" in c else 'male')
    up['comp'] = up.competition.map(lambda c: 'WBBL' if "Women's" in c else 'BBL')
    first = up.home_team.notna() & (up.home_team == up.team2)
    up.loc[first, ['team1', 'team2']] = up.loc[first, ['team2', 'team1']].to_numpy()
    up['venue'] = up.venue_full
    for season, g in up.groupby('season'):
        out = os.path.join(live, f'fixtures_{season.replace("/", "_")}.csv')
        g.sort_values(['date', 'local_time'])[['date', 'team1', 'team2', 'venue', 'gender', 'comp', 'local_time', 'night',
                                                'cricinfo_id', 'round']].to_csv(out, index=False)
        print(f'{out}: {len(g)} fixtures ({", ".join(f"{k} {v}" for k, v in g.comp.value_counts().items())})')


if __name__ == '__main__':
    main(*sys.argv[1:])
