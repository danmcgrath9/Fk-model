"""End-to-end check of the odds parser and backtest on FAKE prices built from our own walk-forward predictions:
a book that prices every game at our own fair price (no margin) must give about zero ROI, CLV of exactly zero at the
close, and settle every bet correctly. No real odds are needed. Skipped without nrl/cache/team_wf.parquet."""
import json
import os

import numpy as np
import pandas as pd
import pytest

from nrl.lines import backtest, parse

CACHE = os.path.join(os.path.dirname(__file__), '..', 'cache')
pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(CACHE, 'team_wf.parquet')), reason='no walk-forward')


def fake_raw(wf, tmp, kind):
    wf = wf.drop_duplicates('match_id').head(150)
    events = []
    for r in wf.itertuples():
        ph = r.p_home_named
        ko = pd.Timestamp(r.kick_off).tz_localize('Australia/Sydney').tz_convert('UTC')
        events.append({'id': f'e{r.match_id}', 'commence_time': ko.strftime('%Y-%m-%dT%H:%M:%SZ'), 'home_team': r.team,
                       'away_team': r.opp, 'bookmakers': [{'key': 'fair', 'markets': [
                           {'key': 'h2h', 'outcomes': [{'name': r.team, 'price': 1 / ph}, {'name': r.opp, 'price': 1 / (1 - ph)}]}]}]})
    json.dump({'label': f'team-{kind}-test', 'body': {'timestamp': '2024-01-01T00:00:00Z', 'data': events}},
              open(os.path.join(tmp, f'team-{kind}-test.json'), 'w'))
    return wf


def test_a_fair_book_gives_no_edge(tmp_path):
    wf = pd.read_parquet(os.path.join(CACHE, 'team_wf.parquet'))
    shown = fake_raw(wf, str(tmp_path), 'close')
    odds = parse.parse(CACHE, str(tmp_path))
    assert odds.event_id.nunique() == len(shown)
    bets = backtest.add_clv(backtest.team_bets(odds, wf))
    assert len(bets) == 2 * len(shown)
    assert np.allclose(bets.p * bets.price, 1.0, atol=1e-9)     # priced at our own fair price
    assert np.allclose(bets.clv, 0.0, atol=1e-9)                # the bet IS the close
    m = shown.set_index('match_id')
    home = bets[bets.outcome == bets.match_id.map(m.team)]
    assert ((home.won == 1) == (home.match_id.map(m.margin) > 0)).all()
