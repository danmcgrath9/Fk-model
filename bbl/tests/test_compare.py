"""compare.py on a made-up snapshot in The Odds API v4 shape: mapping, edge, refusal of what it does not know."""
import json

import pandas as pd

from bbl.live import compare


def test_compare_prices_h2h_and_lists_unknown_markets(tmp_path):
    games = pd.DataFrame([dict(match_id='F000', start_date='2026-12-14', team1='Perth Scorchers', team2='Melbourne Stars',
                               venue='Perth Stadium', p_team1=0.60)])
    games.to_parquet(tmp_path / 'prices_games.parquet', index=False)
    snap = {'timestamp': '2026-12-13T08:00:00Z', 'data': [{
        'id': 'e1', 'commence_time': '2026-12-14T08:15:00Z', 'home_team': 'Perth Scorchers', 'away_team': 'Melbourne Stars',
        'bookmakers': [{'key': 'sportsbet', 'markets': [
            {'key': 'h2h', 'outcomes': [{'name': 'Perth Scorchers', 'price': 1.80}, {'name': 'Melbourne Stars', 'price': 2.05}]},
            {'key': 'player_runs_made_up', 'outcomes': [{'name': 'Over', 'description': 'MR Marsh', 'point': 24.5, 'price': 1.87}]}]}]},
        {'id': 'e2', 'commence_time': '2026-12-15T08:15:00Z', 'home_team': 'Sydney Sixers', 'away_team': 'Sydney Thunder',
         'bookmakers': []}]}
    path = tmp_path / 'snap.json'
    path.write_text(json.dumps(snap))
    o, paper, unmapped, unmatched = compare.compare(str(tmp_path), str(path))
    # 0.60 x 1.80 - 1 = +8%: on the list; 0.40 x 2.05 - 1 = -18%: not
    assert list(paper.name) == ['Perth Scorchers']
    assert abs(paper.edge.iloc[0] - 0.08) < 1e-9
    assert unmapped == ['player_runs_made_up']
    # e2 has no bookmakers, so no outcomes; nothing is invented for it
    assert len(o) == 2


def test_womens_tag_and_utc_to_sydney_date():
    assert compare.team_name('Sydney Sixers Women') == 'Sydney Sixers'
    o = pd.DataFrame([dict(commence_time='2026-12-13T14:30:00Z', home='A', away='B')])   # 1:30am 14 Dec in Sydney
    g = pd.DataFrame([dict(match_id='F', start_date='2026-12-14', team1='A', team2='B', p_team1=0.5)])
    assert compare.attach_games(o, g).match_id.iloc[0] == 'F'
