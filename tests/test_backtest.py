from fixtures import past_event, race_entry
from fk.backtest import (FORM_FEATURES, MARKET_FEATURE, Race, Runner, bsp_chances, calibration, fit, predict, race_features,
                         runner_from_entry, score)


def _race(rid, feats, bsps, winner):
    runners = [Runner(f"h{i}", f"H{i}", {}, b, None, 1 if i == winner else i + 2) for i, b in enumerate(bsps)]
    for r, f in zip(runners, feats):
        r.x = f
    return Race(rid, "2026-08-01", "T", runners)


def test_fit_reproduces_hand_calculated_beta():
    # one feature x = (1, 0), BSP 75% / 25%: p_a/p_b = exp(beta) = 3 -> beta = ln 3 = 1.0986
    race = _race("r1", [{"f": 1.0}, {"f": 0.0}], [1 / 0.75, 1 / 0.25], winner=0)
    beta = fit([race], ["f"])
    assert round(beta["f"], 3) == 1.099
    p = predict(beta, race.runners)
    assert round(p[0], 3) == 0.75 and round(p[1], 3) == 0.25
    s = score([p], [race])
    assert s.races == 1 and round(s.kl_to_bsp, 6) == 0.0 and round(s.log_loss, 4) == round(-__import__("math").log(0.75), 4)
    assert s.winner_top_rated == 1.0


def test_features_are_relative_within_race_and_missing_takes_the_mean():
    runners = [Runner("a", "A", {"neural": 20.0, "last": 90.0, "peak": 95.0, "peak12": 93.0, "open": 2.0}, None, None, None),
               Runner("b", "B", {"neural": 10.0, "last": None, "peak": 91.0, "peak12": 90.0, "open": 4.0}, None, None, None),
               Runner("c", "C", {"neural": 5.0, "last": 80.0, "peak": 85.0, "peak12": 85.0, "open": None}, None, None, None)]
    race_features(runners)
    assert [r.x["neural_rel"] for r in runners] == [1.0, 0.5, 0.25]
    assert runners[0].x["last_rel"] == 0.0 and runners[2].x["last_rel"] == -10.0
    assert runners[1].x["last_rel"] == -5.0             # the mean of 90 and 80 is 85, five below the best
    assert runners[0].x["peak_rel"] == 0.0 and runners[1].x["peak_rel"] == -4.0
    # opening market: 1/2 and 1/4 known, c takes their mean (0.375); normalised then logged
    tot = 0.5 + 0.25 + 0.375
    assert round(runners[0].x[MARKET_FEATURE], 6) == round(__import__("math").log(0.5 / tot), 6)
    assert bsp_chances(runners) is None
    runners[0].bsp, runners[1].bsp = 2.0, 4.0
    q = bsp_chances(runners)
    assert round(sum(q), 9) == 1.0 and q[0] > q[1]


def test_runner_from_entry_reads_result_and_last_rating():
    e = race_entry("H1", "Quagmire", 3, result=1)
    e["odds"]["avgOpen"] = 6.0
    r = runner_from_entry(e)
    assert r.finish == 1 and r.bsp == 5.8 and r.sp == 5.5 and r.raw["open"] == 6.0
    assert r.raw["neural"] == 63 and r.raw["peak"] == 95.0 and r.raw["last"] == 90.0   # newest benchmarked run's atWeights
    e["scratched"] = True
    assert runner_from_entry(e) is None


def test_calibration_buckets():
    race = _race("r1", [{"f": 1.0}, {"f": 0.0}], [1 / 0.75, 1 / 0.25], winner=0)
    rows = calibration([[0.75, 0.25]], [race])
    assert rows == [("20% to 30%", 1, 0.25, 0.0), ("50% to 100%", 1, 0.75, 1.0)]


def test_wfa_handicap_and_distance_features():
    from fk.backtest import DISTANCE, MODEL_SETS, RATINGS, _form_record
    assert _form_record("5: 2-1-0") == (5, 2) and _form_record("") is None and _form_record("x") is None
    e = race_entry("H1", "Quagmire", 3, result=2)
    e["benchmarkRating"] = 78
    e["form"] = {"distanceForm": "5: 2-1-0"}
    # fixture runs are all 1400m with wfaRat 91 on the benchmarked ones, atWeights 90
    r = runner_from_entry(e, race_distance=1400)
    assert r.raw["ohr"] == 78 and r.raw["wfa"] == 91.0 and r.raw["wfa_best"] == 91.0
    assert r.raw["dist"] == 90.0 and r.raw["dist_starts"] == 5 and r.raw["dist_wins"] == 2
    assert runner_from_entry(e, race_distance=2000).raw["dist"] is None       # nothing within 200m of the trip
    other = runner_from_entry(race_entry("H2", "Other", 4, result=1), race_distance=1400)
    other.raw.update(ohr=70, dist_starts=1, dist_wins=1, wfa=85.0, wfa_best=88.0)
    race_features([r, other])
    assert r.x["ohr_rel"] == 0.0 and other.x["ohr_rel"] == -8.0
    assert r.x["wfa_rel"] == 0.0 and other.x["wfa_rel"] == -6.0 and other.x["wfa_best_rel"] == -3.0
    # shrunk win rates: (2+1)/(5+5) = 0.30 and (1+1)/(1+5) = 0.333, centred on their mean
    assert round(r.x["dist_win"], 4) == round(0.30 - (0.30 + 1 / 3) / 2, 4)
    assert set(RATINGS) <= set(r.x) and set(DISTANCE) <= set(r.x)
    assert "ratings_only" in MODEL_SETS and "neural_rel" not in MODEL_SETS["ratings_only"]
