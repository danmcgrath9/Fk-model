"""The form-only price: never reads today's market, and its fast fit is the back-test's fit."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fit_form_only as F  # noqa: E402
from fk import backtest as B  # noqa: E402


def _races(n=40, seed=3):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        size = rng.randint(4, 9)
        xs = [{"a": rng.gauss(0, 1), "b": rng.gauss(0, 1)} for _ in range(size)]
        w = [2.718 ** (0.8 * x["a"] - 0.3 * x["b"] + rng.gauss(0, 0.3)) for x in xs]
        t = sum(w)
        runners = [B.Runner(f"r{i}_{j}", "", {}, round(t / wj, 2), None, j + 1, x) for j, (x, wj) in enumerate(zip(xs, w))]
        out.append(B.Race(f"r{i}", f"2026-01-{i % 28 + 1:02d}", "T", runners))
    return out


def test_vectorised_fit_matches_the_backtest_fit():
    races = _races()
    for ridge in (0.1, 5.0):
        slow = B.fit(races, ["a", "b"], ridge=ridge)
        fast = F.fit_np(races, ["a", "b"], ridge)
        for k in slow:
            assert abs(slow[k] - fast[k]) < 1e-6, (k, slow[k], fast[k])


def test_hand_calculated_two_runner_race():
    # One race, x = (1, 0), BSP 75% / 25%: beta = ln 3 = 1.0986 (fk.backtest.fit's own check).
    race = B.Race("x", "2026-01-01", "T", [B.Runner("a", "", {}, 1 / 0.75, None, 1, {"f": 1.0}),
                                          B.Runner("b", "", {}, 4.0, None, 2, {"f": 0.0})])
    assert abs(F.fit_np([race], ["f"], 1e-8)["f"] - 1.0986) < 1e-3


def test_no_candidate_reads_todays_market_or_a_quarantined_figure():
    for name, feats in F.CANDIDATES.items():
        assert B.MARKET_FEATURE not in feats and "market_prob" not in feats and "market_x_neural" not in feats, name
        assert "first_starter_x_market" not in feats, name
        assert not set(B.NON_DEPLOYABLE) & set(feats), name
