"""Turn the raw Champion Data season files (nrl/data/pull_cd.py) into three parquet tables.

  cd_player_games.parquet  one row per player listed for a game: ids, names, team, opponent, jersey,
                           position (blank in early seasons: Champion Data sent '-'), every count stat,
                           and `took_field` (any run, tackle, pass, kick or possession). Players listed
                           who never took the field are the named reserves (listed from 2015 or so).
  cd_scores.parquet        the score flow: every try, goal and field goal with its half and second,
                           so the first try scorer of each game is known
  cd_team_games.parquet    team totals per game (completion rate, run metres, time in halves, ...)

Usage: python nrl/data/parse_cd.py <dir with cd_raw_*.jsonl.gz> <out dir>
"""
import glob
import gzip
import json
import os
import re
import sys

import pandas as pd

INVOLVEMENT = ['runs', 'tackles', 'passes', 'possessions', 'kicksGeneralPlay', 'missedTackles', 'tries', 'errors']


def parse(path):
    season = int(re.search(r'(\d{4})', os.path.basename(path)).group(1))
    players, scores, teams = [], [], []
    for line in gzip.open(path, 'rt'):
        r = json.loads(line)
        f, ms = r['fixture'], r['match']['matchStats']
        mid = f['matchId']
        base = dict(cd_match_id=mid, season=season, comp=r['comp_name'], is_final='Finals' in r['comp_name'],
                    round_no=f.get('roundNumber'), utc_start=f.get('utcStartTime'), venue=f.get('venueName'),
                    home_id=f['homeSquadId'], away_id=f['awaySquadId'], home_score=f.get('homeSquadScore'),
                    away_score=f.get('awaySquadScore'))
        names = {t['squadId']: t['squadName'] for t in ms.get('teamInfo', {}).get('team', [])}
        names.setdefault(f['homeSquadId'], f['homeSquadName'])
        names.setdefault(f['awaySquadId'], f['awaySquadName'])
        info = {p['playerId']: p for p in ms.get('playerInfo', {}).get('player', [])}
        for p in ms.get('playerStats', {}).get('player', []):
            sid = p['squadId']
            opp = base['away_id'] if sid == base['home_id'] else base['home_id']
            who = info.get(p['playerId'], {})
            row = dict(base, squad_id=sid, team=names.get(sid), opp=names.get(opp), home=sid == base['home_id'],
                       firstname=who.get('firstname'), surname=who.get('surname'), display=who.get('displayName'))
            row.update({k: v for k, v in p.items() if k != 'squadId'})
            row['position'] = None if p.get('position') in (None, '-', '') else p['position']
            row['took_field'] = any((p.get(k) or 0) > 0 for k in INVOLVEMENT)
            players.append(row)
        for s in ms.get('scoreFlow', {}).get('score', []):
            scores.append(dict(cd_match_id=mid, season=season, **s))
        for t in ms.get('teamStats', {}).get('team', []):
            teams.append(dict(base, **t, team=names.get(t.get('squadId'))))
    return pd.DataFrame(players), pd.DataFrame(scores), pd.DataFrame(teams)


def main(src, out):
    os.makedirs(out, exist_ok=True)
    parts = [parse(p) for p in sorted(glob.glob(os.path.join(src, 'cd_raw_*.jsonl.gz')))]
    for k, name in enumerate(('cd_player_games', 'cd_scores', 'cd_team_games')):
        df = pd.concat([x[k] for x in parts], ignore_index=True)
        df.to_parquet(os.path.join(out, name + '.parquet'), index=False)
        print(f'{name}: {len(df):,} rows, seasons {sorted(df.season.unique())}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
