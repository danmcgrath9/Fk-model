"""Prop pricing against hand-worked values."""
import math

import pytest

from aleague.model.props import anytime_scorer, count_over, fair_price, shrunk_share


def test_anytime_scorer():
    # team expects 1.5 goals, player takes a quarter of them over 90 minutes: 0.375 goals,
    # P(at least one) = 1 - e^-0.375 = 0.3127
    assert anytime_scorer(1.5, 0.25) == pytest.approx(1 - math.exp(-0.375))
    assert anytime_scorer(1.5, 0.25) == pytest.approx(0.3127, abs=1e-4)
    # half the minutes, half the expected goals: 1 - e^-0.1875 = 0.1710
    assert anytime_scorer(1.5, 0.25, 45) == pytest.approx(0.1710, abs=1e-4)
    # extra time is not counted: bets settle on 90 minutes
    assert anytime_scorer(1.5, 0.25, 120) == anytime_scorer(1.5, 0.25, 90)


def test_count_over():
    # Poisson mean 2: P(X >= 2) = 1 - e^-2 (1 + 2) = 0.5940
    assert count_over(2.0, 1.5) == pytest.approx(1 - 3 * math.exp(-2))
    # negative binomial mean 2, k 2: p = 0.5, P(0) = 0.25, P(1) = 2 x 0.25 x 0.5 = 0.25, so over 1.5 = 0.5
    assert count_over(2.0, 1.5, k=2) == pytest.approx(0.5)
    # over 0.5 is "at least one"
    assert count_over(2.0, 0.5) == pytest.approx(1 - math.exp(-2))


def test_shrunk_share_and_price():
    # 3 of 10 team goals with a prior of 0.1 at strength 10: (3 + 1) / (10 + 10) = 0.2
    assert shrunk_share(3, 10, 0.1) == pytest.approx(0.2)
    assert fair_price(0.25) == pytest.approx(4.0)
