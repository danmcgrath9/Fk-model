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


def test_winners_target_fits_and_prefers_the_winning_figure():
    # Forty races where the runner with the higher "a" wins about 70% of the time: the
    # winners fit puts a positive weight on "a" and a near-zero one on the noise figure.
    races = _races(seed=9)
    for r in races:
        best = max(r.runners, key=lambda x: x.x["a"])
        for x in r.runners:
            x.finish = 1 if x is best else 2
    beta = F.fit_np(races, ["a", "b"], 1.0, target=F.TARGETS["winners"])
    assert beta["a"] > 0.5 and abs(beta["b"]) < 0.3
    assert set(F.TARGETS) == {"bsp", "winners"}


def test_gate_deploys_a_new_set_only_when_it_is_closer_to_bsp(monkeypatch):
    import fit_form_only as M
    scores = {"old": 0.1792, "new": 0.1814, "better": 0.1700}
    monkeypatch.setattr(M, "CANDIDATES", {k: [k] for k in scores})
    monkeypatch.setattr(M, "fit_np", lambda races, feats, ridge, target=None: feats[0])
    monkeypatch.setattr(M, "kl", lambda beta, races: scores[beta])
    assert M.gate(("new", 30.0), ("old", 30.0), [], [], None)[:2] == ("old", 30.0)      # worse: kept
    assert M.gate(("better", 30.0), ("old", 30.0), [], [], None)[:2] == ("better", 30.0)
    assert M.gate(("new", 30.0), None, [], [], None)[:2] == ("new", 30.0)              # nothing deployed yet
    assert M.gate(("new", 30.0), ("retired", 10.0), [], [], None)[:2] == ("new", 30.0)  # deployed set no longer a candidate
