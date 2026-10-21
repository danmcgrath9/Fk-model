"""Link Champion Data to the Rugby League Project mirror, then extend RLP with the games it lacks.

  games    matched on the Sydney date of kick-off and the two teams (names normalised)
  players  matched by game, team and jersey number, which both sources record; a Champion Data
           player takes the RLP id he shares most games with (agreement is printed)

Champion Data games RLP does not hold yet (from round 18 2026) are written in RLP's shape, so every
model reads one history:
  matches_cd.parquet, player_matches_cd.parquet  appended by team_frame.load()
  cd_links.parquet                               cd player id -> RLP player id, with agreement
  cd_game_link.parquet                           cd game id -> RLP game id (negative: a game only Champion Data holds)
  named_reserves.parquet                         players listed by Champion Data who never took the field

Usage: python nrl/data/link_cd.py nrl/cache
"""
import sys

import numpy as np
import pandas as pd

POSITION = {'Fullback': 'FB', 'Wing': 'W', 'Centre': 'C', 'Five-Eighth': 'FE', 'Halfback': 'HB', 'Prop': 'FR',
            'Hooker': 'HK', 'Second Row': '2R', 'Lock': 'L', 'Interchange': 'B'}
ALIASES = {'new zealand warriors': 'warriors', 'the dolphins': 'dolphins', 'dolphins': 'dolphins'}


def norm(name):
    n = str(name).lower().replace('-', ' ').strip()
    return ALIASES.get(n, n)


def main(cache):
    m = pd.read_parquet(f'{cache}/matches.parquet')
    # an RLP game listed before its result is not held: Champion Data supplies it
    m = m.dropna(subset=['home_team_score', 'away_team_score'])
    pm = pd.read_parquet(f'{cache}/player_matches.parquet')
    pm = pm[pm.match_id.isin(m.match_id)]
    cp = pd.read_parquet(f'{cache}/cd_player_games.parquet')
    cp['date'] = pd.to_datetime(cp.utc_start, utc=True).dt.tz_convert('Australia/Sydney').dt.date.astype(str)
    g = cp.drop_duplicates('cd_match_id')
    home_name = dict(zip(g.cd_match_id, np.where(g.home, g.team, g.opp)))
    away_name = dict(zip(g.cd_match_id, np.where(g.home, g.opp, g.team)))
    cg = pd.DataFrame(dict(cd_match_id=g.cd_match_id, date=g.date, season=g.season,
                           h=g.cd_match_id.map(home_name).map(norm), a=g.cd_match_id.map(away_name).map(norm)))
    rm = m.assign(date=m.date.dt.strftime('%Y-%m-%d'), h=m.home_team.map(norm), a=m.away_team.map(norm))
    link = cg.merge(rm[['match_id', 'date', 'h', 'a']], on=['date', 'h', 'a'], how='left')
    # a game whose date differs by a day between sources (time zones, late kick-offs): match on teams within 1 day
    miss = link.match_id.isna()
    if miss.any():
        for d in (-1, 1):
            alt = cg[miss.to_numpy()].assign(date=(pd.to_datetime(cg[miss.to_numpy()].date) + pd.Timedelta(days=d)).dt.strftime('%Y-%m-%d'))
            hit = alt.merge(rm[['match_id', 'date', 'h', 'a']], on=['date', 'h', 'a'], how='inner')
            link.loc[link.cd_match_id.isin(hit.cd_match_id), 'match_id'] = link.cd_match_id.map(dict(zip(hit.cd_match_id, hit.match_id)))
            miss = link.match_id.isna()
    rlp_seasons = set(m.season)
    gl = link[['cd_match_id', 'match_id']].copy()
    gl['match_id'] = gl.match_id.fillna(-gl.cd_match_id).astype('int64')
    gl.to_parquet(f'{cache}/cd_game_link.parquet', index=False)
    print(f'games: {len(link):,} Champion Data games, {link.match_id.notna().sum():,} linked to RLP; '
          f'unlinked by season: {link[link.match_id.isna()].season.value_counts().sort_index().to_dict()}')

    # players: game + team + jersey
    cp = cp.merge(link[['cd_match_id', 'match_id']], on='cd_match_id', how='left')
    cp['tnorm'] = cp.team.map(norm)
    pmn = pm.assign(tnorm=pm.team.map(norm), jersey=pd.to_numeric(pm.number, errors='coerce'))
    j = cp[cp.match_id.notna() & cp.took_field].merge(
        pmn[['match_id', 'tnorm', 'jersey', 'player_id']], left_on=['match_id', 'tnorm', 'jumperNumber'],
        right_on=['match_id', 'tnorm', 'jersey'], how='inner')
    votes = j.groupby(['playerId', 'player_id']).size().rename('n').reset_index()
    tot = votes.groupby('playerId').n.transform('sum')
    votes['agree'] = votes.n / tot
    best = votes.sort_values('n', ascending=False).drop_duplicates('playerId')
    print(f'players: {cp.playerId.nunique():,} Champion Data players, {len(best):,} linked; '
          f'median agreement {best.agree.median():.0%}, below 80%: {(best.agree < 0.8).sum()}')
    best[['playerId', 'player_id', 'n', 'agree']].rename(columns={'playerId': 'cd_player_id'}) \
        .to_parquet(f'{cache}/cd_links.parquet', index=False)

    # extend RLP with the games it lacks
    to_rlp = dict(zip(best.playerId, best.player_id))
    new = cp[cp.match_id.isna()].copy()
    new['match_id'] = -new.cd_match_id
    canon = {norm(t): t for t in pd.concat([m.home_team, m.away_team]).unique()}
    ng = new.drop_duplicates('cd_match_id')
    rows = []
    for r in ng.itertuples():
        local = pd.Timestamp(r.utc_start).tz_convert('Australia/Sydney')
        rows.append(dict(competition='NRL', competition_year=f'NRL {r.season}',
                         round=('Final' if r.is_final else f'Round {r.round_no}'), special_round=None,
                         date=pd.Timestamp(local.date()), time=None, time_24hr=local.strftime('%H:%M:%S'),
                         match_id=-r.cd_match_id, venue_id=-1, crowd=np.nan,
                         home_team=canon.get(norm(home_name[r.cd_match_id]), home_name[r.cd_match_id]),
                         home_team_ht_score=np.nan, home_team_score=float(r.home_score), home_team_penalties=np.nan,
                         away_team=canon.get(norm(away_name[r.cd_match_id]), away_name[r.cd_match_id]),
                         away_team_ht_score=np.nan, away_team_score=float(r.away_score), away_team_penalties=np.nan,
                         season=r.season))
    nm = pd.DataFrame(rows)
    played = new[new.took_field]
    npm = pd.DataFrame(dict(player_id=played.playerId.map(to_rlp).fillna(-played.playerId).astype('int64'),
                            match_id=played.match_id.astype('int64'), team=played.team.map(norm).map(canon).fillna(played.team),
                            opposition_team=played.opp.map(norm).map(canon).fillna(played.opp),
                            number=played.jumperNumber.astype(float), position=played.position.map(POSITION),
                            captain=False, tries=played.tries, penalty_tries=0, goals=played.conversions + played.penaltyGoals,
                            goal_attempts=played.conversionAttempts + played.penaltyGoalAttempts,
                            field_goals=played.fieldGoals, field_goals2=0, sin_bins5=0, sin_bins=played.sinBins,
                            send_offs=played.sentOffs, points=played.points))
    if len(nm):
        nm = nm[nm.season.isin(rlp_seasons | {max(rlp_seasons) + 1})]
    for df in (nm, npm):
        for c in df.columns:
            if df[c].dtype == object:
                df[c] = df[c].astype('string')
    nm.to_parquet(f'{cache}/matches_cd.parquet', index=False)
    npm.to_parquet(f'{cache}/player_matches_cd.parquet', index=False)
    res = cp[~cp.took_field][['cd_match_id', 'match_id', 'season', 'team', 'playerId', 'jumperNumber', 'display']].copy()
    res['player_id'] = res.playerId.map(to_rlp)
    res.to_parquet(f'{cache}/named_reserves.parquet', index=False)
    print(f'extension: {len(nm)} games and {len(npm):,} player-games added from Champion Data; '
          f'{len(res):,} named reserves who did not take the field')


if __name__ == '__main__':
    main(sys.argv[1])
