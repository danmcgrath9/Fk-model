"""Round 60: the first-tip edge map (topaz_round60)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round42 as R42  # noqa: E402
import topaz_round60 as R60  # noqa: E402


def test_a_verdict_needs_two_standard_errors_from_the_base():
    base = dict(n=100, bsp=0.10, se=0.02)
    assert R60.verdict(dict(n=30, bsp=0.31, se=0.10), base) == "strong"
    assert R60.verdict(dict(n=30, bsp=-0.11, se=0.10), base) == "weak"
    assert R60.verdict(dict(n=30, bsp=0.29, se=0.10), base) == ""
    assert R60.verdict(dict(n=0), base) == "" and R60.verdict(dict(n=1, bsp=1.0, se=np.nan), base) == ""


def field():
    rng = np.random.default_rng(12)
    rows = []
    for r in range(1500):
        b = rng.dirichlet(np.full(6, 2.0))
        ours = b * rng.lognormal(0, 0.35, 6)
        ours /= ours.sum()
        w = rng.choice(6, p=b)
        for i in range(6):
            rows.append(dict(race_id=r, won=int(i == w), p_book=b[i], pb6=ours[i], price=0.85 / b[i], ded=0.0,
                             p_bsp=b[i], q_bsp=b[i], tip_rank=float(i == int(np.argmax(ours))), box=i + 1,
                             is_best_bet=float(i == 0), track="SAN" if r % 2 else "BEN", race_class=5.0, runs=10.0,
                             n_bet=6, tab_book=1 / 0.85, to_jump=8.0,
                             date=pd.Timestamp("2023-06-01") + pd.Timedelta(days=r)))
    return pd.DataFrame(rows)


def test_the_map_prints(capsys):
    t = field()
    m, e, paid = R42.candidates(t, "pb6")
    cand = m & (e >= 1.1) & (t.tip_rank.values == 1)
    R60.table(t, cand, cand & (e >= 1.3), paid, R60.slices(t))
    out = capsys.readouterr().out
    assert "| all first tips |" in out and "| GRV's best bet | best bet |" in out and "| track | SAN |" in out
