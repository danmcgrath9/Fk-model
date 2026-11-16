"""Round 61: TAB's opening price, every input one at a time (topaz_round61)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round61 as R61  # noqa: E402


def test_cuts_skip_race_level_inputs_and_order_within_the_race():
    t = pd.DataFrame({"race_id": [1, 1, 1, 2, 2, 2, 3, 3, 3], "dist": [300] * 3 + [400] * 3 + [500] * 3,
                      "elo": [5.0, 7.0, np.nan, 1.0, 1.0, 3.0, 9.0, 8.0, 2.0], "flag": [0, 1, 0, 1, 0, 0, 1, 0, 0]})
    assert R61.cuts(t, "dist") == {}                                    # the same for every runner in a race
    c = R61.cuts(t, "elo")
    assert list(c["order in the race"]) == ["2nd", "highest in the race", "missing", "2nd", "2nd",
                                            "highest in the race", "highest in the race", "2nd", "3rd"]
    assert c["fifth of all runners"][2] == "missing" and c["fifth of all runners"][6] == "fifth 5"
    assert list(R61.cuts(t, "flag")["value"]) == ["0", "1", "0", "1", "0", "0", "1", "0", "0"]


def field(n=6000, seed=1):
    rng = np.random.default_rng(seed)
    rows = []
    for r in range(n):
        b = rng.dirichlet(np.full(6, 2.0))
        x = rng.normal(size=6)
        true = b * np.exp(0.25 * (x == x.max()))                        # the top-x dog wins more than the book says
        true /= true.sum()
        w = rng.choice(6, p=true)
        for i in range(6):
            rows.append(dict(race_id=r, won=int(i == w), x=x[i], noise=rng.normal(), sex="D" if i % 2 else "B",
                             p_tab_fl=b[i], h_p_x_bet=b[i], h_p_i_bet=true[i], q_bsp=true[i], tip_rank=float(i == 0),
                             date=pd.Timestamp("2023-06-01") + pd.Timedelta(days=r // 5)))
    return pd.DataFrame(rows)


def test_the_scan_finds_a_planted_lean_and_reports_it(capsys):
    t = field()
    labels = R61.labelled(t, ["x", "noise", "sex"])
    res = R61.scan(t, labels)
    hit = res[(res.input == "x") & (res.cut == "order in the race") & (res.value == "highest in the race")].iloc[0]
    assert hit["TAB after its favourite bias|pass"] == 1 and hit["the card's blend|pass"] == 1
    assert hit["blend with Isolynx|pass"] == 0 and hit["BSP corrected|pass"] == 0
    R61.report(res, R61.MODELS)
    out = capsys.readouterr().out
    assert "**Where both are wrong the same way**" in out and "| x | order in the race | highest in the race |" in out
    tip = R61.scan(t, labels, t.tip_rank.values == 1)
    sums = tip.groupby(["input", "cut"]).n.sum()                     # cut on the whole field, counted in the tips
    assert len(sums) == 5 and (sums == (t.tip_rank == 1).sum()).all()
    assert set(tip[tip.input == "x"].value) > {"highest in the race"}
