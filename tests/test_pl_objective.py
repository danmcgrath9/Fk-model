"""research/greyhound/topaz_round7.py: the Plackett-Luce objective's gradient and hessian against finite differences."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round7 as R7  # noqa: E402


class Data:
    def get_label(self):
        return None


def races():
    # race A: 5 dogs, one did not finish; race B: 3 dogs, all finished
    df = pd.DataFrame({"date": pd.Timestamp("2024-01-01"), "race_id": [1] * 5 + [2] * 3,
                       "box": [1, 2, 3, 4, 5, 1, 2, 3], "finish": [3, 1, np.nan, 2, 4, 2, 1, 3]})
    return R7.race_order(df)


def test_race_order_puts_finishers_first_in_order():
    d, pos, fin = races()
    assert d.box.tolist() == [2, 4, 1, 5, 3, 2, 1, 3]
    assert pos.tolist() == [1, 2, 3, 4, 5, 1, 2, 3] and fin.tolist() == [True] * 4 + [False] + [True] * 3


@pytest.mark.parametrize("depth,decay", [(1, 1.0), (3, 1.0), (3, 0.5), (12, 1.0)])
def test_gradient_and_hessian_match_finite_differences(depth, decay):
    d, pos, fin = races()
    groups = d.groupby("race_id", sort=False).size().values
    rng = np.random.default_rng(3)
    s = rng.normal(size=len(d))
    weight = np.array([0.7] * 5 + [1.0] * 3)
    grad, hess = R7.pl_objective(pos, fin, groups, weight, depth, decay)(s, Data())
    # the recency weight multiplies each race's rows alike, so the weighted loss is per-race weight times the race loss
    def wloss(x):
        total = 0.0
        for rid, w in ((1, 0.7), (2, 1.0)):
            m = (d.race_id == rid).values
            g = np.array([m.sum()])
            total += w * R7.pl_loss(x[m], pos[m], fin[m], g, depth, decay)
        return total
    eps = 1e-5
    for i in range(len(s)):
        up, dn = s.copy(), s.copy()
        up[i] += eps
        dn[i] -= eps
        assert abs((wloss(up) - wloss(dn)) / (2 * eps) - grad[i]) < 1e-6
        assert abs((wloss(up) - 2 * wloss(s) + wloss(dn)) / eps ** 2 - hess[i]) < 1e-3
    assert R7.pl_loss(s, pos, fin, groups, depth, decay) > 0


def test_depth_one_is_the_winner_softmax():
    d, pos, fin = races()
    groups = d.groupby("race_id", sort=False).size().values
    s = np.array([0.3, -0.2, 1.1, 0.0, 0.5, 0.2, 0.9, -0.4])
    grad, hess = R7.pl_objective(pos, fin, groups, np.ones(8), 1, 1.0)(s, Data())
    for m in ((d.race_id == 1).values, (d.race_id == 2).values):
        p = np.exp(s[m]) / np.exp(s[m]).sum()
        won = (pos[m] == 1).astype(float)
        assert np.allclose(grad[m], p - won) and np.allclose(hess[m], p * (1 - p))


def test_non_finisher_is_never_chosen_but_always_in_the_denominator():
    d, pos, fin = races()
    groups = d.groupby("race_id", sort=False).size().values
    s = np.zeros(8)
    grad, _ = R7.pl_objective(pos, fin, groups, np.ones(8), 12, 1.0)(s, Data())
    # race A, equal scores: the non-finisher (position 5) is in all four denominators (1/5 + 1/4 + 1/3 + 1/2) and
    # has no stage of its own; the fourth finisher's own stage is a 2-dog choice against it
    assert abs(grad[4] - (1 / 5 + 1 / 4 + 1 / 3 + 1 / 2)) < 1e-12
    assert abs(grad[3] - (1 / 5 + 1 / 4 + 1 / 3 + 1 / 2 - 1)) < 1e-12
