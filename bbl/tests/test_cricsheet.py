"""cricsheet.py against a hand-built match in Cricsheet's JSON shape, with every count worked by hand.

The match: Heat bat first. Over 0: a dot, a wide (1 extra), a four, a caught wicket, a retirement.
Over 1: a six off a no-ball (6 + 1). Strikers chase in a super over. A concussion substitute is
recorded on the second ball. Power Surge is a powerplay from over 10.
"""
import json
import os
import zipfile

import pandas as pd

from bbl.data import cricsheet, inventory


def ball(batter, bowler, rb=0, rx=0, extras=None, wickets=None, replacements=None):
    d = {'batter': batter, 'bowler': bowler, 'non_striker': 'NS', 'runs': {'batter': rb, 'extras': rx, 'total': rb + rx}}
    if extras:
        d['extras'] = extras
    if wickets:
        d['wickets'] = wickets
    if replacements:
        d['replacements'] = replacements
    return d


DOC = {
    'meta': {'data_version': '1.1.0', 'revision': 1},
    'info': {
        'balls_per_over': 6, 'city': 'Brisbane', 'dates': ['2024-12-15'],
        'event': {'name': 'Big Bash League', 'match_number': 1}, 'gender': 'male', 'match_type': 'T20',
        'outcome': {'winner': 'Adelaide Strikers', 'eliminator': 'Adelaide Strikers', 'result': None},
        'overs': 20, 'players': {'Brisbane Heat': ['A', 'B', 'C'], 'Adelaide Strikers': ['X', 'Y']},
        'registry': {'people': {'A': 'aaaa0001', 'B': 'aaaa0002', 'X': 'xxxx0001'}},
        'season': '2024/25', 'team_type': 'club', 'teams': ['Brisbane Heat', 'Adelaide Strikers'],
        'toss': {'decision': 'bat', 'winner': 'Brisbane Heat'}, 'venue': 'The Gabba, Brisbane',
    },
    'innings': [
        {'team': 'Brisbane Heat',
         'overs': [
             {'over': 0, 'deliveries': [
                 ball('A', 'X'),
                 ball('A', 'X', rx=1, extras={'wides': 1},
                      replacements={'match': [{'in': 'D', 'out': 'C', 'team': 'Brisbane Heat', 'reason': 'concussion_substitute'}]}),
                 ball('A', 'X', rb=4),
                 ball('A', 'X', wickets=[{'player_out': 'A', 'kind': 'caught', 'fielders': [{'name': 'Y'}]}]),
                 ball('B', 'X', wickets=[{'player_out': 'B', 'kind': 'retired hurt'}]),
             ]},
             {'over': 1, 'deliveries': [ball('C', 'Y', rb=6, rx=1, extras={'noballs': 1})]},
         ],
         'powerplays': [{'from': 0.1, 'to': 3.6, 'type': 'mandatory'}, {'from': 10.1, 'to': 11.6, 'type': 'power surge'}]},
        {'team': 'Adelaide Strikers', 'target': {'overs': 20, 'runs': 13},
         'overs': [{'over': 0, 'deliveries': [ball('X', 'A', rb=1)]}]},
        {'team': 'Adelaide Strikers', 'super_over': True, 'overs': [{'over': 0, 'deliveries': [ball('Y', 'B', rb=6)]}]},
    ],
}


def test_parse_match_counts():
    t = cricsheet.parse_match('9999', DOC)
    m = t['t20_matches'][0]
    assert m['competition'] == 'Big Bash League' and m['season'] == '2024/25' and m['start_date'] == '2024-12-15'
    assert m['bat_first'] == 'Brisbane Heat' and m['toss_decision'] == 'bat'
    assert m['winner'] == 'Adelaide Strikers' and m['result'] == 'win' and m['has_super_over']
    assert (m['n_players_team1'], m['n_players_team2']) == (3, 2)

    inn = {r['innings']: r for r in t['t20_innings']}
    # innings 1: 0 + 1 (wide) + 4 + 0 + 0 + 7 (six off a no-ball) = 12 runs
    assert inn[1]['runs'] == 12
    # the caught wicket counts, the retirement does not
    assert inn[1]['wickets'] == 1
    # six balls bowled, the wide and the no-ball are not legal: 4 legal balls
    assert inn[1]['legal_balls'] == 4
    assert inn[2]['target_runs'] == 13 and inn[3]['super_over']

    balls = t['t20_deliveries']
    assert len(balls) == 8
    assert balls[3]['player_out'] == 'A' and balls[3]['fielders'] == 'Y'
    assert balls[5]['noballs'] == 1 and balls[5]['runs_batter'] == 6 and not balls[5]['legal']

    players = {(r['team'], r['player']): r for r in t['t20_players']}
    assert players[('Brisbane Heat', 'A')]['player_id'] == 'aaaa0001'
    assert players[('Brisbane Heat', 'C')]['player_id'] is None  # not in the registry: kept, id missing

    assert [p['pp_type'] for p in t['t20_powerplays']] == ['mandatory', 'power surge']
    assert t['t20_replacements'][0]['reason'] == 'concussion_substitute' and t['t20_replacements'][0]['seq'] == 2


def test_zip_keeps_only_t20_and_counts_the_rest(tmp_path):
    odi = json.loads(json.dumps(DOC))
    odi['info']['match_type'] = 'ODI'
    zpath = tmp_path / 'all_json.zip'
    with zipfile.ZipFile(zpath, 'w') as z:
        z.writestr('9999.json', json.dumps(DOC))
        z.writestr('8888.json', json.dumps(odi))
        z.writestr('README.txt', 'not a match')
    out = tmp_path / 'out'
    cricsheet.main(str(zpath), str(out))
    m = pd.read_parquet(out / 't20_matches.parquet')
    assert list(m.match_id) == ['9999']
    types = pd.read_parquet(out / 'match_types.parquet').set_index('match_type').matches.to_dict()
    assert types == {'T20': 1, 'ODI': 1}

    inventory.main(str(out))
    text = (out / 'INVENTORY.md').read_text()
    assert '## Big Bash League, by season' in text and '| 2024/25 | 1 |' in text
    assert 'power surge' in text and 'concussion_substitute' in text
