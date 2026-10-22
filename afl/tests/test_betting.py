import numpy as np
import pandas as pd
import pytest

from afl.betting import ledger as L
from afl.betting import staking as S


def bet(**k):
    d = dict(game='g1', team='A', player_id=1, stat='D', side='over', p=0.6, price=1.87)
    d.update(k)
    return d


def test_kelly_hand_calculated():
    # p 0.6 at 1.87: (0.6 x 1.87 - 1) / 0.87 = 0.122 / 0.87 = 0.14023
    assert S.kelly(np.array([0.6]), np.array([1.87]))[0] == pytest.approx(0.14023, abs=1e-5)
    assert S.kelly(np.array([0.5]), np.array([1.87]))[0] == 0.0     # no edge, no stake


def test_correlated_teammates_are_shrunk():
    five = pd.DataFrame([bet(player_id=i) for i in range(5)])
    b = S.stakes(five, bank=10_000, max_bet=1.0, max_round=1.0)
    # 1 / sqrt(1 + 4 x 0.031) = 0.9433
    assert b.shrink.iloc[0] == pytest.approx(1 / np.sqrt(1 + 4 * 0.031))
    # an under on a teammate offsets: its correlation is negative and is ignored, so no shrink from it
    mixed = pd.DataFrame([bet(player_id=1), bet(player_id=2, side='under')])
    assert S.stakes(mixed, 10_000).shrink.tolist() == [1.0, 1.0]
    # same player disposals and marks overs: correlation 0.503
    same = pd.DataFrame([bet(stat='D'), bet(stat='M')])
    assert S.stakes(same, 10_000).shrink.iloc[0] == pytest.approx(1 / np.sqrt(1.503))


def test_caps():
    many = pd.DataFrame([bet(game=f'g{i}', p=0.9) for i in range(20)])
    b = S.stakes(many, bank=1000)
    assert b.stake.max() <= 20 and b.stake.sum() <= 150


def test_ledger_round_trip(tmp_path):
    path = str(tmp_path / 'ledger.csv')
    bets = pd.DataFrame([dict(season=2027, round=1, game='g1', team='A', player='X', player_id=1, stat='D', side='over',
                              line=24.5, price=1.95, book='b1', p_model=0.58, mu=26.0, a=0.026, stake=10),
                         dict(season=2027, round=1, game='g1', team='A', player='Y', player_id=2, stat='D', side='under',
                              line=20.5, price=1.90, book='b1', p_model=0.57, mu=19.0, a=0.026, stake=10)])
    L.log_bets(bets, path)
    with pytest.raises(ValueError):
        L.log_bets(bets.iloc[:1], path)
    # close: X's line unchanged, over 1.80 / under 2.00 -> no-vig over = (1/1.8) / (1/1.8 + 1/2) = 0.5263; CLV = 1.95 x 0.5263 - 1
    closes = pd.DataFrame([dict(game='g1', player_id=1, stat='D', close_line=24.5, close_over=1.80, close_under=2.00)])
    led = L.record_close(closes, path)
    assert led.set_index('player_id').clv[1] == pytest.approx(1.95 * (0.5555556 / (0.5555556 + 0.5)) - 1, abs=1e-6)
    assert np.isnan(led.set_index('player_id').clv[2])
    led = L.settle(pd.DataFrame([dict(game='g1', player_id=1, stat='D', value=27), dict(game='g1', player_id=2, stat='D', value=21)]), path)
    x = led.set_index('player_id')
    assert x.outcome[1] == 'win' and x.pnl[1] == pytest.approx(9.5)
    assert x.outcome[2] == 'loss' and x.pnl[2] == -10
    s = L.summary(path).set_index('stat')
    assert s.loc['all', 'profit'] == pytest.approx(-0.5)


def test_clv_moves_to_our_line():
    # we took over 24.5; the close is 25.5 at evens (no-vig 0.5). Our line is easier, so the close's chance at 24.5 is
    # above 0.5 by exactly our model's P(25) at mu 26: P(over 24.5) - P(over 25.5)
    row = pd.Series(dict(line=24.5, close_line=25.5, close_over=2.0, close_under=2.0, mu=26.0, a=0.026, price=1.9, side='over'))
    shift = L.p_over(24.5, 26.0, 0.026) - L.p_over(25.5, 26.0, 0.026)
    assert shift > 0
    assert L.clv(row) == pytest.approx(1.9 * (0.5 + shift) - 1)
