"""Market pricing against hand-worked score matrices."""
import numpy as np
import pytest

from aleague.model.markets import (asian_handicap, asian_total, btts, draw_no_bet, fair_odds, h2h, price_all,
                                   score_matrix)


def toy():
    # P(home i, away j) for i, j in 0..2; rows home goals, columns away goals
    return np.array([[0.10, 0.05, 0.05],
                     [0.20, 0.10, 0.05],
                     [0.20, 0.15, 0.10]])


def test_h2h_and_btts():
    m = toy()
    r = h2h(m)
    # home wins: (1,0) .20 + (2,0) .20 + (2,1) .15 = .55; draws .10+.10+.10 = .30; away .05+.05+.05 = .15
    assert r['home'] == pytest.approx(0.55) and r['draw'] == pytest.approx(0.30) and r['away'] == pytest.approx(0.15)
    # both score: (1,1) .10 + (1,2) .05 + (2,1) .15 + (2,2) .10 = .40
    assert btts(m)['yes'] == pytest.approx(0.40)


def test_handicaps():
    m = toy()
    # home -0.5 is the home win: .55, fair 1/.55
    o = asian_handicap(m, -0.5)
    assert o['win'] == pytest.approx(0.55) and fair_odds(o) == pytest.approx(1 / 0.55)
    # draw no bet home: win .55, push .30, loss .15 -> fair 1 + .15/.55
    assert fair_odds(draw_no_bet(m)) == pytest.approx(1 + 0.15 / 0.55)
    # home -1: win by 2+ = (2,0) .20; push on win by 1 = (1,0) .20 + (2,1) .15 = .35; loss .45
    o = asian_handicap(m, -1.0)
    assert (o['win'], o['push'], o['loss']) == pytest.approx((0.20, 0.35, 0.45))
    # home -0.75 = half on -0.5, half on -1: win by 2 wins both (.20); win by 1 is half win (.35); rest loses
    o = asian_handicap(m, -0.75)
    assert (o['win'], o['half_win'], o['loss']) == pytest.approx((0.20, 0.35, 0.45))
    # fair price: (x-1)(.20 + .35/2) = .45 -> x = 1 + .45/.375 = 2.2
    assert fair_odds(o) == pytest.approx(2.2)
    # away +0.25 = half on 0, half on +0.5: away win (.15) wins; draw (.30) is half win; home win loses
    o = asian_handicap(m, 0.25, 'away')
    assert (o['win'], o['half_win'], o['loss']) == pytest.approx((0.15, 0.30, 0.55))


def test_totals():
    m = toy()
    # totals: 0 -> .10; 1 -> .25; 2 -> .35; 3 -> .20; 4 -> .10
    assert asian_total(m, 2.5)['win'] == pytest.approx(0.30)
    assert asian_total(m, 2.5, 'under')['win'] == pytest.approx(0.70)
    o = asian_total(m, 2.0)
    assert (o['win'], o['push'], o['loss']) == pytest.approx((0.30, 0.35, 0.35))
    # over 2.25 = half on 2, half on 2.5: 3+ wins both (.30); exactly 2 loses half (.35)
    o = asian_total(m, 2.25)
    assert (o['win'], o['half_loss'], o['loss']) == pytest.approx((0.30, 0.35, 0.35))


def test_score_matrix_sums_and_dixon_coles():
    m = score_matrix(1.5, 1.1)
    assert m.sum() == pytest.approx(1)
    plain, dc = score_matrix(1.4, 1.1), score_matrix(1.4, 1.1, rho=-0.1)
    assert dc[0, 0] > plain[0, 0] and dc[1, 1] > plain[1, 1] and dc[1, 0] < plain[1, 0]
    assert h2h(dc)['draw'] > h2h(plain)['draw']


def test_prices_are_consistent():
    p = price_all(score_matrix(1.6, 1.0, rho=-0.08))
    assert p['h2h_home'] + p['h2h_draw'] + p['h2h_away'] == pytest.approx(1)
    # over and under 2.5 are complements: 1/over + 1/under = 1 at fair prices
    assert 1 / p['over_2.5'] + 1 / p['under_2.5'] == pytest.approx(1)
    # home -0.5 is the home win
    assert p['ah_home_-0.5'] == pytest.approx(1 / p['h2h_home'])
