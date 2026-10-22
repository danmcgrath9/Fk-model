"""The live paper-bet pipeline on hand-made responses in The Odds API's documented shape."""
import datetime as dt

import pandas as pd
import pytest

from afl.betting import ledger as L
from afl.lines import live

NOW = dt.datetime(2027, 3, 18, 9, 0, tzinfo=dt.timezone.utc)
EV = {'id': 'ev1', 'commence_time': '2027-03-20T08:30:00Z', 'home_team': 'Collingwood Magpies', 'away_team': 'Carlton Blues'}


def fake_fetch(over_price, under_price):
    def fetch(path, params, key):
        if path.endswith('/events'):
            return [EV, {**EV, 'id': 'ev2', 'commence_time': '2027-04-20T08:30:00Z'}], 0, '999'
        body = {**EV, 'bookmakers': [{'key': 'sportsbet', 'markets': [{'key': 'player_disposals', 'outcomes': [
            {'name': 'Over', 'description': 'Nick Daicos', 'price': over_price, 'point': 27.5},
            {'name': 'Under', 'description': 'Nick Daicos', 'price': under_price, 'point': 27.5}]}]}]}
        return body, 7, '990'
    return fetch


def sheet():
    return pd.DataFrame({'game': ['2027-03-20|Collingwood|Carlton'], 'player_id': [7], 'Player': ['Nick Daicos'],
                         'team': ['Collingwood'], 'season': [2027], 'Round': ['2'],
                         'mu_D': [31.0], 'a_D': [0.02], 'mu_M': [5.0], 'a_M': [0.06], 'mu_T': [3.0], 'a_T': [0.09],
                         'mu_G': [0.5], 'a_G': [0.08]})


def test_snapshot_bets_close(tmp_path):
    out, led, sh = str(tmp_path / 'live'), str(tmp_path / 'ledger.csv'), str(tmp_path / 'sheet.csv')
    sheet().to_csv(sh, index=False)
    # only the game inside the window is fetched, once per label
    assert live.snapshot('teams', 168, 'k', now=NOW, fetch=fake_fetch(1.90, 1.90), out=out) == 7
    assert live.snapshot('teams', 168, 'k', now=NOW, fetch=fake_fetch(1.90, 1.90), out=out) == 0
    b = live.bets(sh, 'teams', ledger=led, out=out)
    # our chance of 28+ at mu 31 is well above 1/1.90, so the over is a paper bet
    assert len(b) == 1 and b.side.iloc[0] == 'over' and b.line.iloc[0] == 27.5 and b.price.iloc[0] == 1.90
    assert b.stake.iloc[0] > 0
    assert live.bets(sh, 'teams', ledger=led, out=out).empty          # pricing the round again logs nothing twice
    # the close: the over firmed to 1.70 / 2.15. CLV = 1.90 x no-vig over - 1
    live.snapshot('close', 168, 'k', now=NOW, fetch=fake_fetch(1.70, 2.15), out=out)
    c = live.close(ledger=led, out=out).iloc[0]
    nv = (1 / 1.70) / (1 / 1.70 + 1 / 2.15)
    assert c.close_over == 1.70 and c.clv == pytest.approx(1.90 * nv - 1)
    assert L.load(led).bet_id.tolist() == [1]


def test_no_bet_without_edge(tmp_path):
    out, led, sh = str(tmp_path / 'live'), str(tmp_path / 'ledger.csv'), str(tmp_path / 'sheet.csv')
    s = sheet()
    s['mu_D'] = 27.6                                  # about even at 27.5: no edge at 1.90 either side
    s.to_csv(sh, index=False)
    live.snapshot('teams', 168, 'k', now=NOW, fetch=fake_fetch(1.90, 1.90), out=out)
    assert live.bets(sh, 'teams', ledger=led, out=out).empty
