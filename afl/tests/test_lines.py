"""The lines pipeline on hand-made responses in The Odds API's documented shape: names, open/close, settling."""
import json
import os

import numpy as np
import pandas as pd
import pytest

from afl.lines import backtest, parse


def test_team_names():
    assert parse.team_name('Greater Western Sydney Giants') == 'GWS'
    assert parse.team_name('North Melbourne Kangaroos') == 'North Melbourne'
    assert parse.team_name('Melbourne Demons') == 'Melbourne'
    assert parse.team_name('Brisbane Lions') == 'Brisbane'
    assert parse.team_name('St Kilda Saints') == 'St Kilda'
    assert parse.team_name('Western Bulldogs') == 'Western Bulldogs'
    assert parse.team_name('West Coast Eagles') == 'West Coast'


def snapshot(ts, over_price, point=27.5):
    return {'timestamp': ts, 'data': {
        'id': 'ev1', 'commence_time': '2025-08-07T09:30:00Z', 'home_team': 'Collingwood Magpies', 'away_team': 'Carlton Blues',
        'bookmakers': [{'key': 'sportsbet', 'markets': [{'key': 'player_disposals', 'outcomes': [
            {'name': 'Over', 'description': 'Nick Daicos', 'price': over_price, 'point': point},
            {'name': 'Under', 'description': 'Nick Daicos', 'price': 1.85, 'point': point},
            {'name': 'Over', 'description': 'N. Unknown', 'price': 1.9, 'point': 10.5}]}]}]}}


@pytest.fixture
def raw(tmp_path):
    d = tmp_path / 'odds' / 'ev1'
    d.mkdir(parents=True)
    json.dump(snapshot('2025-08-04T09:30:00Z', 2.00), open(d / '72h.json', 'w'))     # open
    json.dump(snapshot('2025-08-07T09:15:00Z', 1.70), open(d / '0.25h.json', 'w'))   # close: the over firmed
    return str(tmp_path)


def test_flatten_match_open_close_settle(raw):
    lines = parse.flatten(raw)
    assert set(lines.home) == {'Collingwood'} and set(lines.away) == {'Carlton'}
    fx = pd.DataFrame({'game': ['g1'], 'season': [2025], 'date': ['2025-08-07'], 'home': ['Collingwood'], 'away': ['Carlton']})
    lines = parse.match_games(lines, fx)
    assert (lines.game == 'g1').all()
    wf = pd.DataFrame({'game': ['g1', 'g1'], 'player_id': [7, 8], 'Player': ['Nick Daicos', 'Patrick Cripps'], 'season': [2025] * 2,
                       'Round': ['21'] * 2, 'D': [31, 25], 'mu_D': [30.0, 24.0], 'a_D': [0.026, 0.026]})
    props = parse.match_players(lines, wf)
    assert props[props.player == 'Nick Daicos'].player_id.eq(7).all()
    assert props[props.player == 'N. Unknown'].player_id.isna().all()       # no such player: left unmatched, never guessed
    oc = backtest.open_close(props[props.player_id.notna()])
    over = oc[oc.side == 'Over'].iloc[0]
    assert over.price_open == 2.00 and over.price_close == 1.70
    ev = backtest.evaluate(oc, wf)
    o = ev[ev.side == 'Over'].iloc[0]
    assert bool(o.won) is True                                              # 31 > 27.5
    expected = 1 - __import__('scipy').stats.nbinom.cdf(27, 1 / 0.026, (1 / 0.026) / (1 / 0.026 + 30.0))
    assert o.p_side == pytest.approx(expected)
    # beating the close: took 2.00, closed 1.70 -> 1/1.70 - 1/2.00 = +8.8 points of chance
    assert (1 / o.price_close - 1 / o.price_open) == pytest.approx(0.0882, abs=1e-3)


def test_market_consensus_removes_margin_and_takes_the_median():
    rows = []
    for book, over, under in [('a', 1.80, 2.00), ('b', 1.90, 1.90), ('c', 2.10, 1.70)]:
        for side, price in [('Over', over), ('Under', under)]:
            rows.append(dict(game='g1', player_id=7, market_stat='player_disposals', point=27.5, book=book, side=side,
                             price_close=price, p_side=0.55 if side == 'Over' else 0.45, won=True, season=2025))
    mc = backtest.market_compare(pd.DataFrame(rows))
    # book a: (1/1.8) / (1/1.8 + 1/2.0) = 0.5263; b: 0.5; c: (1/2.1) / (1/2.1 + 1/1.7) = 0.4474. Median 0.5
    assert len(mc) == 1 and mc.books.iloc[0] == 3
    assert mc.p_mkt.iloc[0] == pytest.approx(0.5)
    assert mc.p_ours.iloc[0] == 0.55
