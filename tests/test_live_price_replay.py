import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import live_price_replay as L  # noqa: E402


def test_blend_is_the_market_at_a_1_b_0_and_sharpens_with_form():
    m = [0.5, 0.3, 0.2]
    assert [round(p, 9) for p in L.blend_probs([0, 0, 0], m, 1.0, 0.0)] == [0.5, 0.3, 0.2]
    p = L.blend_probs([1.0, 0.0, -1.0], m, 1.0, 1.0)
    assert p[0] > 0.5 and p[2] < 0.2 and round(sum(p), 9) == 1.0


def test_fit_blend_recovers_the_weights_that_made_the_close():
    from fk.backtest import Race, Runner
    import random
    rnd = random.Random(7)
    days = {}
    for i in range(60):
        m = [rnd.uniform(0.05, 0.4) for _ in range(6)]
        m = [v / sum(m) for v in m]
        sc = [rnd.gauss(0, 1) for _ in range(6)]
        close = L.blend_probs(sc, m, 0.9, 0.8)         # the close is 0.9 x market + 0.8 x form
        runners = [Runner(f"h{i}_{k}", "H", {"open": 1 / m[k]}, 1 / close[k], None, None) for k in range(6)]
        race = Race(f"r{i}", f"d{i % 5}", "T", runners)
        days.setdefault(race.date, []).append((sc, m, race))
    assert L.fit_blend(days) == (0.9, 0.8)
