"""Stint reconstruction and on-court ratings on hand-built games (no cache needed)."""
import numpy as np
import pandas as pd
import pytest

from nbl.model import onoff

H = ['h1', 'h2', 'h3', 'h4', 'h5']
A = ['a1', 'a2', 'a3', 'a4', 'a5']


def _ev(rows):
    cols = ['period', 'period_type', 'clock', 's1', 's2', 'team', 'action_type', 'sub_type', 'key']
    return pd.DataFrame(rows, columns=cols)


def test_a_substitution_splits_the_game_and_points_go_to_who_was_on():
    ev = _ev([
        (1, 'REGULAR', 9.0, 2, 0, 'H', '2pt', None, 'h1'),
        (1, 'REGULAR', 6.0, 2, 0, 'H', 'substitution', 'out', 'h1'),
        (1, 'REGULAR', 6.0, 2, 0, 'H', 'substitution', 'in', 'h6'),
        (1, 'REGULAR', 3.0, 2, 3, 'A', '3pt', None, 'a1'),
    ])
    rows, dropped = onoff.stints_for_game(ev, 'H', {'H': set(H), 'A': set(A)})
    assert dropped == 0 and len(rows) == 2
    first, second = rows
    assert first['minutes'] == pytest.approx(4.0) and first['home_pts'] == 2 and first['away_pts'] == 0
    assert 'h1' in first['home_on'] and 'h6' not in first['home_on']
    assert second['minutes'] == pytest.approx(6.0) and second['away_pts'] == 3 and 'h6' in second['home_on']


def test_s1_can_be_the_away_score():
    ev = _ev([(1, 'REGULAR', 5.0, 0, 2, 'H', '2pt', None, 'h1')])          # s2 moved but s1 is the away side
    rows, _ = onoff.stints_for_game(ev, 'H', {'H': set(H), 'A': set(A)}, s1_home=False)
    assert rows[0]['home_pts'] == 2 and rows[0]['away_pts'] == 0


def test_feed_order_is_normalised_to_oldest_first():
    old = pd.DataFrame({'period': [2, 1, 1], 'period_type': ['REGULAR'] * 3, 'clock': [9.0, 1.0, 8.0],
                        'action_number': [np.nan] * 3})                   # newest first, no event numbers
    assert list(onoff.in_time_order(old).clock) == [8.0, 1.0, 9.0]
    new = pd.DataFrame({'period': [1, 1], 'period_type': ['REGULAR'] * 2, 'clock': [5.0, 5.0], 'action_number': [12.0, 11.0]})
    assert list(onoff.in_time_order(new).action_number) == [11.0, 12.0]


def test_ratings_only_use_stints_before_the_date_and_find_the_better_player():
    rng = np.random.default_rng(0)
    rows = []
    for i in range(400):
        h = tuple(sorted(rng.choice(['p%d' % k for k in range(10)], 5, replace=False)))
        a = tuple(sorted(set('p%d' % k for k in range(10)) - set(h)))
        # p0 adds 10 points per 40 minutes to whichever side he is on
        m = 10.0 * (('p0' in h) - ('p0' in a)) + rng.normal(0, 5)
        rows.append(dict(home_on=h, away_on=a, minutes=4.0, home_pts=50 + m / 10, away_pts=50 - 0.0,
                         tip=pd.Timestamp('2025-01-01', tz='UTC') + pd.Timedelta(days=i % 50)))
    s = pd.DataFrame(rows)
    keys = ['p%d' % k for k in range(10)]
    r = onoff.fit_ratings(s, {}, pd.Timestamp('2025-03-01', tz='UTC'), keys, lam=50)
    assert r.idxmax() == 'p0'
    early = onoff.fit_ratings(s, {}, pd.Timestamp('2025-01-01', tz='UTC'), keys, lam=50)
    assert early.empty                                                     # nothing before the date: no ratings
