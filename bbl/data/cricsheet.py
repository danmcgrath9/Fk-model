"""Cricsheet ball-by-ball JSON into parquet tables: every T20 match, men's and women's, all leagues.

Cricsheet (cricsheet.org) publishes one JSON file per match. We take its single bulk zip
(all_json.zip) once, keep the zip on the bbl-history release, and parse only the T20 matches
(match_type T20 or IT20). BBL alone is about 44 games a season, so player history comes from
every T20 league in the file, not BBL only.

Tables (one parquet each):
  t20_matches      one row per match: competition, season, date, venue, teams, toss, result
  t20_players      one row per player per match: the XI as Cricsheet lists it, with registry id
  t20_innings      one row per innings: runs, wickets, legal balls, target
  t20_deliveries   one row per ball
  t20_powerplays   one row per powerplay (BBL's Power Surge shows here if Cricsheet records it)
  t20_replacements one row per substitution (concussion, X-factor and similar, if recorded)
  match_types      what else the zip holds, by match type, so nothing dropped is invisible

Usage: python bbl/data/cricsheet.py <all_json.zip> <out dir>
"""
import json
import os
import sys
import zipfile
from collections import Counter

import pandas as pd

T20_TYPES = {'T20', 'IT20'}
# a retirement is recorded as a wicket entry but does not count against the batting side
NOT_DISMISSALS = {'retired hurt', 'retired not out'}


def _outcome(info):
    o = info.get('outcome') or {}
    by = o.get('by') or {}
    if o.get('winner'):
        result = 'win'
    else:
        result = o.get('result', 'unknown')
    return dict(winner=o.get('winner'), win_by_runs=by.get('runs'), win_by_wickets=by.get('wickets'),
                win_by_innings=by.get('innings'), result=result, method=o.get('method'),
                eliminator=o.get('eliminator'), bowl_out=o.get('bowl_out'))


def parse_match(match_id, doc):
    """One Cricsheet match document into rows for each table. Pure: no I/O."""
    info = doc.get('info') or {}
    meta = doc.get('meta') or {}
    teams = info.get('teams') or [None, None]
    event = info.get('event') or {}
    toss = info.get('toss') or {}
    dates = info.get('dates') or []
    players = info.get('players') or {}
    registry = (info.get('registry') or {}).get('people') or {}
    innings = doc.get('innings') or []

    match = dict(
        match_id=match_id, competition=event.get('name'), season=str(info.get('season')) if info.get('season') is not None else None,
        start_date=dates[0] if dates else None, n_dates=len(dates), gender=info.get('gender'),
        match_type=info.get('match_type'), team_type=info.get('team_type'),
        balls_per_over=info.get('balls_per_over'), overs=info.get('overs'),
        city=info.get('city'), venue=info.get('venue'),
        team1=teams[0] if len(teams) > 0 else None, team2=teams[1] if len(teams) > 1 else None,
        toss_winner=toss.get('winner'), toss_decision=toss.get('decision'),
        bat_first=next((i.get('team') for i in innings if not i.get('super_over')), None),
        match_number=event.get('match_number'), stage=event.get('stage'), group=event.get('group'),
        n_players_team1=len(players.get(teams[0], [])) if teams and teams[0] else 0,
        n_players_team2=len(players.get(teams[1], [])) if len(teams) > 1 and teams[1] else 0,
        n_innings=len(innings), has_super_over=any(i.get('super_over') for i in innings),
        data_version=meta.get('data_version'), revision=meta.get('revision'),
        **_outcome(info))

    player_rows = [dict(match_id=match_id, team=team, list_order=k + 1, player=name, player_id=registry.get(name))
                   for team, names in players.items() for k, name in enumerate(names)]

    inn_rows, ball_rows, pp_rows, rep_rows = [], [], [], []
    for n, inn in enumerate(innings, start=1):
        team = inn.get('team')
        so = bool(inn.get('super_over'))
        runs = wkts = legal = 0
        for ov in inn.get('overs') or []:
            for seq, d in enumerate(ov.get('deliveries') or [], start=1):
                r = d.get('runs') or {}
                ex = d.get('extras') or {}
                w = d.get('wickets') or []
                is_legal = not ex.get('wides') and not ex.get('noballs')
                runs += r.get('total', 0)
                wkts += sum(1 for x in w if x.get('kind') not in NOT_DISMISSALS)
                legal += is_legal
                ball_rows.append(dict(
                    match_id=match_id, innings=n, team=team, super_over=so, over=ov.get('over'), seq=seq,
                    batter=d.get('batter'), non_striker=d.get('non_striker'), bowler=d.get('bowler'),
                    runs_batter=r.get('batter', 0), runs_extras=r.get('extras', 0), runs_total=r.get('total', 0),
                    non_boundary=bool(r.get('non_boundary', False)), legal=is_legal,
                    wides=ex.get('wides', 0), noballs=ex.get('noballs', 0), byes=ex.get('byes', 0),
                    legbyes=ex.get('legbyes', 0), penalty=ex.get('penalty', 0), n_wickets=len(w),
                    player_out=w[0].get('player_out') if w else None, wicket_kind=w[0].get('kind') if w else None,
                    fielders=';'.join(f.get('name', '') for f in (w[0].get('fielders') or [])) if w else None,
                    player_out_2=w[1].get('player_out') if len(w) > 1 else None,
                    wicket_kind_2=w[1].get('kind') if len(w) > 1 else None))
                for kind, reps in (d.get('replacements') or {}).items():
                    for rp in reps:
                        rep_rows.append(dict(match_id=match_id, innings=n, over=ov.get('over'), seq=seq, kind=kind,
                                             team=rp.get('team'), player_in=rp.get('in'), player_out=rp.get('out'),
                                             role=rp.get('role'), reason=rp.get('reason')))
        target = inn.get('target') or {}
        inn_rows.append(dict(match_id=match_id, innings=n, team=team, super_over=so, runs=runs, wickets=wkts,
                             legal_balls=legal, target_runs=target.get('runs'), target_overs=target.get('overs'),
                             penalty_runs_pre=(inn.get('penalty_runs') or {}).get('pre', 0),
                             penalty_runs_post=(inn.get('penalty_runs') or {}).get('post', 0),
                             n_absent_hurt=len(inn.get('absent_hurt') or [])))
        for pp in inn.get('powerplays') or []:
            pp_rows.append(dict(match_id=match_id, innings=n, team=team, pp_from=pp.get('from'), pp_to=pp.get('to'),
                                pp_type=pp.get('type')))
    return dict(t20_matches=[match], t20_players=player_rows, t20_innings=inn_rows, t20_deliveries=ball_rows,
                t20_powerplays=pp_rows, t20_replacements=rep_rows)


def _frame(rows):
    df = pd.DataFrame(rows)
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype('string')
    return df


def parse_zip(path):
    tables = {k: [] for k in ('t20_matches', 't20_players', 't20_innings', 't20_deliveries', 't20_powerplays',
                              't20_replacements')}
    types = Counter()
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.endswith('.json'):
                continue
            doc = json.loads(z.read(name))
            info = doc.get('info') or {}
            mt = info.get('match_type')
            types[(mt, info.get('gender'), info.get('team_type'))] += 1
            if mt not in T20_TYPES:
                continue
            for k, rows in parse_match(os.path.splitext(os.path.basename(name))[0], doc).items():
                tables[k].extend(rows)
    out = {k: _frame(v) for k, v in tables.items()}
    out['match_types'] = _frame([dict(match_type=t, gender=g, team_type=tt, matches=n)
                                 for (t, g, tt), n in sorted(types.items(), key=lambda x: -x[1])])
    return out


def main(zip_path, out):
    os.makedirs(out, exist_ok=True)
    tables = parse_zip(zip_path)
    for name, df in tables.items():
        dest = os.path.join(out, name + '.parquet')
        df.to_parquet(dest, index=False)
        print(f'{dest}: {len(df):,} rows, {df.shape[1]} columns')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
