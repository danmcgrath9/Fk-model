"""First starters and trial form: a horse without race form is marked as one, not dressed
as an average runner."""
import math

from fixtures import MS, ms, past_event, race_entry
from fk import backtest as B


def _trial(race_id, days_before, finish, margin):
    p = past_event(race_id, 0, with_benchmark=False, race=False)
    p["trial"] = True
    p["date"] = ms(2026, 9, 12) - days_before * MS
    p["finishPosition"], p["margin"] = finish, margin
    return p


def test_latest_trial_hand_values():
    evs = [_trial("T1", 30, 3, 1.5), _trial("T2", 200, 2, 0.2)]
    assert B.latest_trial(evs, "2026-09-12") == 1.5            # the 30-day trial, beaten 1.5 lengths
    assert B.latest_trial([_trial("T3", 10, 1, 0.0)], "2026-09-12") == 0.0   # won the trial
    assert B.latest_trial([_trial("T4", 200, 2, 0.2)], "2026-09-12") is None  # outside 120 days
    assert B.latest_trial(evs, None) is None                  # no race date, no window, no figure
    assert B.latest_trial([_trial("T5", 0, 1, 0.0)], "2026-09-12") is None    # race day itself never counts


def test_a_first_starter_is_marked_and_leans_on_the_market():
    raced = race_entry("H0", "Raced", 1, result=1)
    fresh = race_entry("H1", "Debut", 2, result=2, n_events=0)
    fresh["pastEvents"] = [_trial("TR", 20, 2, 0.8)]
    fresh["odds"]["avgOpen"] = 4.0
    raced["odds"]["avgOpen"] = 2.0
    rs = [B.runner_from_entry(e, 1400, 85.0, "2026-09-12") for e in (raced, fresh)]
    B.race_features(rs)
    a, b = rs
    assert (a.x["first_starter"], b.x["first_starter"]) == (0.0, 1.0)
    assert (a.x["unrated"], b.x["unrated"]) == (0.0, 1.0)
    assert (a.x["trialled_recently"], b.x["trialled_recently"]) == (0.0, 1.0)
    # the market chance, 1/4 of (1/2 + 1/4) = 1/3, logged, for the first starter only
    assert a.x["first_starter_x_market"] == 0.0
    assert round(b.x["first_starter_x_market"], 6) == round(math.log(1 / 3), 6)


def test_the_experience_sets_are_searched_and_read_the_market():
    for name in ("market_plus_experience", "market_kitchen_sink_exp"):
        assert B.MARKET_FEATURE in B.MODEL_SETS[name]
        assert all(f in B.MODEL_SETS[name] for f in B.EXPERIENCE)
