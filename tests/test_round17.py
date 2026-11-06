"""research/greyhound/topaz_round17.py: the A/E rows, by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
pytest.importorskip("scipy")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round17 as R17  # noqa: E402


def test_ae_rows_favourite_and_price_bands_by_hand():
    # 400 two-dog races: the SP favourite (A's chance 0.6, $1.67) wins 300, the other (0.4, $2.50) wins 100
    n = 400
    t = pd.DataFrame({"race_id": np.repeat(np.arange(n), 2), "start_price": np.tile([1.8, 2.2], n),
                      "won": np.ravel([[1, 0] if i < 300 else [0, 1] for i in range(n)]),
                      "p_a": np.tile([0.6, 0.4], n), "p_b": np.tile([0.75, 0.25], n)})
    rows = {name: (runners, wins, ae) for name, runners, wins, ae in R17.ae_rows(t, ["p_a", "p_b"])}
    # favourite: 300 wins against 400 x 0.6 = 240 (A/E 1.25) and 400 x 0.75 = 300 (1.00)
    assert rows["SP favourite"][:2] == (400, 300) and np.allclose(rows["SP favourite"][2], [1.25, 1.0])
    # A's $1-$2 band is the favourite; the $2-$3 band the other dog: 100 wins against 160 and 100
    assert np.allclose(rows["A's price $1-$2"][2], [1.25, 1.0])
    assert rows["A's price $2-$3"][:2] == (400, 100) and np.allclose(rows["A's price $2-$3"][2], [100 / 160, 1.0])
    assert "A's price $3-$5" not in rows                     # fewer than 300 runners: left out
