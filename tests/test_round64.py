"""Round 64: what takes TAB's opening price to BSP (topaz_round64)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round64 as R64  # noqa: E402


def test_the_move_history_sees_only_earlier_days():
    R = pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-02", "2024-01-03", "2024-01-03",
                                              "2024-01-04"]),
                      "dog": ["a", "a", "b", "a", "b", "a"], "trainer_id": [1, 1, 1, 1, 2, 1]})
    mv = np.array([0.2, -0.1, 0.5, np.nan, 0.3, 0.0])
    h = R64.move_history(R, mv, shrink=0)
    assert np.isnan(h.dog_mv_last[0]) and h.dog_mv_last[1] == 0.2 and h.dog_mv_last[3] == -0.1
    assert np.isclose(h.dog_mv_mean5[3], 0.05) and h.dog_mv_n[3] == 2 and np.isclose(h.dog_mv_mean5[5], 0.05)
    assert h.dog_mv_n[5] == 2 and np.isnan(h.dog_mv_last[5])       # its day-3 run had no move
    # the trainer: day 2 sees day 1 only; day 3 sees days 1 and 2 (the second dog's day-2 run included)
    assert np.isclose(h.trainer_mv[1], 0.2) and np.isclose(h.trainer_mv[2], 0.2) and h.trainer_mv_n[2] == 1
    assert np.isclose(h.trainer_mv[3], (0.2 - 0.1 + 0.5) / 3) and h.trainer_mv_n[3] == 3
    assert h.trainer_mv_n[4] == 0 and h.trainer_mv_n[5] == 3


def test_a_second_run_the_same_day_sees_nothing_of_the_first():
    R = pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-02"]), "dog": ["a", "a", "a"]})
    h = R64.move_history(R, np.array([0.4, 0.1, 0.2]))
    assert h.dog_mv_last[1] == 0.4 and np.isnan(h.dog_mv_last[2]) and np.isnan(h.dog_mv_n[2])
    assert h.trainer_mv.isna().all()


def test_moves_need_a_bsp_on_every_runner():
    R = pd.DataFrame({"race_id": [1, 1, 2, 2]})
    mv = R64.moves(R, np.array([0.6, 0.4, 0.0, 0.0]), np.array([True, True, False, False]),
                   np.array([0.5, 0.5, 0.5, 0.5]))
    assert np.allclose(mv[:2], np.log([1.2, 0.8])) and np.isnan(mv[2:]).all()


def test_every_input_is_in_one_data_set_and_tabs_book_and_the_scratchings_in_none():
    cols = ["lp_tab", "tab_book", "n_bet", "s_later", "lp_ours", "gap", "grv_rating", "tip_rank", "iso_v100_last",
            "chk_dip_last", "p_lead", "mkt_prev_lsp", "time_rating_last", "elo", "trainer_id_won_28D", "dam_id_won_91D",
            "dog_mv_mean5", "trainer_mv", "box", "track"]
    g = R64.group_columns(cols)
    flat = [c for v in g.values() for c in v]
    assert sorted(flat) == sorted(set(cols) - set(R64.BASE) - R64.NEVER) and len(flat) == len(set(flat))
    assert g[R64.NEW] == ["dog_mv_mean5", "trainer_mv"] and g[R64.OTHER] == ["box", "track"]
    assert g["our model's forecast"] == ["lp_ours", "gap"] and g["Isolynx tracking"] == ["iso_v100_last", "chk_dip_last"]


def test_the_distance_is_zero_at_bsp_and_grows_away_from_it():
    race = np.array([1, 1, 2, 2])
    q = np.array([0.7, 0.3, 0.5, 0.5])
    assert R64.distance(q, q, race) == 0
    assert R64.distance(np.array([0.5, 0.5, 0.5, 0.5]), q, race) > 0


def test_the_ranking_learns_where_tabs_book_is_wrong():
    rng = np.random.default_rng(5)
    n, k = 3000, 4
    race = np.repeat(np.arange(n), k)
    dates = (pd.Timestamp("2024-06-01") + pd.to_timedelta(np.arange(n) * 300 // n * 1, "D")).values
    d = np.repeat(dates, k).astype("datetime64[ns]")
    tab = np.concatenate([rng.dirichlet(np.full(k, 3.0)) for _ in range(n)])
    f = rng.integers(0, 2, len(race)).astype(float)                # backed dogs: BSP 30% shorter in odds terms
    q = pd.Series(tab * np.exp(0.4 * f)).groupby(race).transform(lambda s: s / s.sum()).values
    X = pd.DataFrame({"lp_tab": np.log(tab), "f": f})
    off = np.log(tab)
    use = np.ones(len(race), bool)
    test = d >= np.datetime64("2025-01-01")
    old = (R64.VAL_FROM, R64.SPLIT)
    R64.VAL_FROM, R64.SPLIT = "2024-11-01", "2025-01-01"
    try:
        rounds, p, _ = R64.rank_one(X, q, off, race, d, use, test, max_rounds=150, step=25)
    finally:
        R64.VAL_FROM, R64.SPLIT = old
    assert test.any() and rounds > 0
    assert R64.distance(p, q[test], race[test]) < 0.3 * R64.distance(tab[test], q[test], race[test])


def test_nothing_runs_without_both_named_walks(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BETWATCH_DIR", str(tmp_path))
    monkeypatch.delenv("WALK_ISO_USE", raising=False)
    assert R64.main(str(tmp_path), "t") == 1
    assert "Both saved walks must be named" in capsys.readouterr().out
