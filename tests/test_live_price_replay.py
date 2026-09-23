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


def _race(i, day, m, close):
    from fk.backtest import Race, Runner
    runners = [Runner(f"h{i}_{k}", "H", {"open": 1 / m[k]}, 1 / close[k], None, None) for k in range(len(m))]
    return Race(f"r{i}", day, "T", runners)


def test_day_blocks_never_split_a_day_and_cover_every_race():
    import random
    rnd = random.Random(3)
    races = []
    for i in range(40):
        m = [rnd.uniform(0.05, 0.4) for _ in range(5)]
        m = [v / sum(m) for v in m]
        races.append(_race(i, f"2026-09-{1 + i // 4:02d}", m, m))
    blocks = L.day_blocks(races, 5)
    seen = sorted(i for b in blocks for i in b)
    assert seen == list(range(40))
    for b in blocks:
        days_in = {races[i].date for i in b}
        for other in blocks:
            if other is not b:
                assert not days_in & {races[i].date for i in other}


def test_refit_on_real_prices_learns_the_market_scale():
    """The close is the market stretched to the power 1.2: a market coefficient refitted on
    the real price should land near 1.2 and beat the market as it stands."""
    import random
    from fk import backtest as B
    rnd = random.Random(11)
    races = []
    for i in range(60):
        m = [rnd.uniform(0.05, 0.4) for _ in range(6)]
        m = [v / sum(m) for v in m]
        close = L.blend_probs([0] * 6, m, 1.2, 0.0)
        race = _race(i, f"d{i % 10:02d}", m, close)
        for r, mi in zip(race.runners, m):
            r.x = {B.MARKET_FEATURE: __import__("math").log(mi)}
        races.append(race)
    rows = L.refit_on_real(races, [B.MARKET_FEATURE], ridges=[1e-6])
    (ridge, kl, probs), = rows
    assert all(probs)
    market_kl = sum(L.kl_to_bsp(B.market_probs([r])[0], r) for r in races) / len(races)
    assert kl < market_kl
    beta = B.fit(races, [B.MARKET_FEATURE], ridge=1e-6)
    assert abs(beta[B.MARKET_FEATURE] - 1.2) < 0.02


def test_cull_long_hands_the_chance_back_pro_rata_and_never_zeroes():
    out = L.cull_long([0.6, 0.38, 0.02], 50.0, 0.5)
    assert [round(p, 4) for p in out] == [0.6061, 0.3839, 0.01]
    assert round(sum(out), 9) == 1.0
    assert L.cull_long([0.6, 0.4], 50.0, 0.5) == [0.6, 0.4]      # nothing rated $50+: unchanged
    assert min(L.cull_long([0.9, 0.09, 0.01], 50.0, 0.1)) > 0
