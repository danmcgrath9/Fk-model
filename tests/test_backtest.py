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


def test_class_trend_and_scope_features():
    e = race_entry("H1", "Quagmire", 3, result=1)
    e["form"] = {"careerForm": "8: 6-1-0"}
    r = runner_from_entry(e, race_distance=1400, lws=85.0)
    assert r.raw["last_vs_lws"] == 5.0 and r.raw["best_vs_lws"] == 5.0        # 90 rated against a standard of 85
    assert r.raw["starts"] == 8 and r.raw["trend_slope"] is not None
    assert runner_from_entry(e, race_distance=1400).raw["last_vs_lws"] is None
    o = runner_from_entry(race_entry("H2", "Other", 4, result=2), race_distance=1400, lws=85.0)
    o.raw.update(last_vs_lws=-3.0, best_vs_lws=0.0, starts=30, trend_slope=-1.0)
    race_features([r, o])
    assert r.x["last_vs_lws"] == 5.0 and o.x["last_vs_lws"] == -3.0          # kept as points against the standard
    import math
    assert round(r.x["starts_log"], 6) == round(math.log(9) - (math.log(9) + math.log(31)) / 2, 6)


def test_distance_aware_features_read_the_latest_and_best_run_at_the_trip():
    from fk.backtest import DISTANCE_AWARE, MODEL_SETS, NON_DEPLOYABLE, SHAPE
    e = race_entry("H1", "Sheza", 3, result=1)
    # fixture runs are 14 days apart, newest first in the list; make the two newest 1600m
    # runs rate 84 and 88 (adjToday), and the older 2000m runs rate 95, so the trip decides
    for i, p in enumerate(e["pastEvents"]):
        p["distance"] = 1600 if i < 2 else 2000
        p["adjustedForTodaysWeight"] = [84.0, 88.0][i] if i < 2 else 95.0
    r = runner_from_entry(e, race_distance=1600)
    assert r.raw["last_dist"] == 84.0 and r.raw["best_dist"] == 88.0     # only the 1600m runs count
    assert r.raw["dist_change"] == 0.0                                     # the newest run was at 1600m, same as today
    assert r.raw["exp"] == 58.0
    r2 = runner_from_entry(e, race_distance=2000)
    assert r2.raw["last_dist"] == 95.0 and r2.raw["best_dist"] == 95.0
    assert r2.raw["dist_change"] == 4.0                                    # 2000 - 1600, in hundreds of metres
    o = runner_from_entry(race_entry("H2", "Delius", 4, result=2), race_distance=1600)
    o.raw.update(last_dist=None, best_dist=None, dist_change=None, exp=70.0)
    race_features([r, o])
    assert r.x["last_dist_rel"] == 0.0 and o.x["last_dist_rel"] == 0.0     # a missing value takes the mean, so no gap
    assert r.x["exp_rel"] == -12.0 and o.x["exp_rel"] == 0.0
    assert r.x["early_pos"] == 0.0 and r.x["early_x_tempo"] == 0.0         # no speedmap yet
    assert set(DISTANCE_AWARE) <= set(r.x) and set(SHAPE) <= set(r.x)
    assert "distance_aware" in MODEL_SETS and "exp_rel" in NON_DEPLOYABLE
    assert "exp_rel" not in MODEL_SETS["distance_shape"] and "exp_rel" in MODEL_SETS["distance_shape_exp"]


def test_shape_features_place_the_leader_against_the_tempo():
    from fk.backtest import positions_from_speedmap, shape_features
    rs = [runner_from_entry(race_entry(f"H{i}", f"R{i}", i + 1, result=i + 1), race_distance=1400) for i in range(3)]
    race_features(rs)
    positions = positions_from_speedmap([{"horse_id": "H0", "predicted_position": 1}, {"horse_id": "H2", "predicted_position": 3},
                                         {"horse_id": "HX", "predicted_position": None}])
    assert positions == {"H0": 1, "H2": 3}
    shape_features(rs, positions, tempo=-1.0)                              # a slow lead
    # front 0, back 1, the unmapped H1 takes the mean 0.5; centred on 0.5: -0.5, 0, +0.5
    assert [round(r.x["early_pos"], 6) for r in rs] == [-0.5, 0.0, 0.5]
    assert [round(r.x["early_x_tempo"], 6) for r in rs] == [0.5, -0.0, -0.5]   # leader x slow tempo is positive
    shape_features(rs, {}, tempo=-1.0)                                     # no map: untouched
    assert rs[0].x["early_pos"] == -0.5


def test_plan_replay_prices_each_block_out_of_sample_and_settles_at_bsp():
    from fk.backtest import plan_replay
    from fixtures import race_entry
    # Ten one-feature races: runner A carries the higher Neural and the shorter BSP ($1.6),
    # so a fit to BSP on any four blocks makes A the top pick in the fifth; A wins eight of
    # the ten, opens at $2 and settles at its BSP.
    races = []
    for i in range(10):
        rs = []
        for hid, neural, won in (("A", 80, i % 5 != 0), ("B", 40, i % 5 == 0)):
            e = race_entry(hid, hid, 1 if hid == "A" else 2, result=1 if won else 2)
            r = runner_from_entry(e)
            r.raw["neural"] = neural; r.raw["open"] = 2.0 if hid == "A" else 2.5
            r.bsp = 1.6 if hid == "A" else 2.5; r.sp = r.bsp
            rs.append(r)
        race_features(rs)
        races.append(Race(f"R{i}", f"2026-08-{i + 1:02d}", "T", rs))
    out = plan_replay(races, ["neural_rel"], folds=5)
    top = out["at_open"]["top_pick"]
    assert out["races"] == 10 and top.bets == 10 and top.winners == 8            # A is top pick everywhere, wins 8
    assert round(top.returned, 2) == round(8 * 1.6, 2) and round(top.staked, 2) == 10.0   # settled at BSP, one unit each
    # the same bets on the other basis: paid the $2.00 they were struck at, not the $1.60 BSP
    struck = out["at_struck"]["top_pick"]
    assert struck.bets == top.bets and struck.winners == top.winners
    assert round(struck.returned, 2) == round(8 * 2.0, 2)


def test_recent_weighted_reads_newest_first_and_skips_the_runs_that_lack_it():
    from fk.backtest import recent_weighted
    runs = [{"speedRating": 10.0}, {"speedRating": 20.0}]                     # oldest first
    assert round(recent_weighted(runs, "speedRating"), 4) == round((20 + 10 * 0.8) / 1.8, 4)
    assert recent_weighted([{"speedRating": None}, {"speedRating": 5.0}], "speedRating") == 5.0
    assert recent_weighted([{"x": 1.0}], "speedRating") is None
    many = [{"v": float(i)} for i in range(10)]                               # only the last 4 count
    assert round(recent_weighted(many, "v", n=4), 4) == round(
        (9 + 8 * 0.8 + 7 * 0.64 + 6 * 0.512) / (1 + 0.8 + 0.64 + 0.512), 4)


def test_speed_and_sectional_features_reach_the_model():
    from fk.backtest import MODEL_SETS, SPEED
    e = race_entry("H1", "Fast", 3, result=1)
    r = runner_from_entry(e, race_distance=1400)
    # the fixture's benchmarked runs carry speedRating 101, finishingSpeed 102.3,
    # section 6-F vsClass +0.9 (the last 600) and S-6 vsClass -0.3 (the run to it)
    assert r.raw["speed"] == 101.0 and r.raw["speed_best"] == 101.0
    assert round(r.raw["finish_speed"], 1) == 102.3
    assert round(r.raw["last600"], 2) == 0.90 and round(r.raw["to600"], 2) == -0.30
    o = runner_from_entry(race_entry("H2", "Slow", 4, result=2), race_distance=1400)
    o.raw.update(speed=95.0, speed_best=97.0, finish_speed=99.0, last600=-1.1, to600=0.4)
    race_features([r, o])
    assert r.x["speed_rel"] == 0.0 and o.x["speed_rel"] == -6.0
    assert round(r.x["last600_rel"], 2) == 0.0 and round(o.x["last600_rel"], 2) == -2.0
    assert round(o.x["to600_rel"], 2) == 0.0 and round(r.x["to600_rel"], 2) == -0.7   # o's run to the 600 was better
    assert set(SPEED) <= set(r.x)
    assert "form_plus_speed" in MODEL_SETS and "everything" in MODEL_SETS


def test_position_shares_are_read_against_the_field_size():
    from fk.backtest import position_shares
    # 10 runners, settled 6th, 800m 5th, 400m 4th, finished 2nd
    run = {"runners": 10, "positions": [6, None, None, 5, None, 4, None, 2]}
    p = position_shares(run)
    assert round(p["settle_share"], 4) == round(5 / 9, 4)        # (6 - 1) / 9
    assert round(p["pos800_share"], 4) == round(4 / 9, 4)
    assert round(p["pos_gain"], 4) == round(4 / 9, 4)            # 6th to 2nd
    assert round(p["late_gain"], 4) == round(2 / 9, 4)           # 4th to 2nd
    # the same finishing position in a bigger field is a smaller share
    big = position_shares({"runners": 19, "positions": [6, None, None, 5, None, 4, None, 2]})
    assert big["settle_share"] < p["settle_share"]
    assert position_shares({"runners": 1, "positions": [1] * 8}) == {}       # no field to share
    assert position_shares({"runners": 10, "positions": []}) == {}


def test_running_style_meets_todays_tempo():
    from fk.backtest import POSITION, STYLE, positions_from_speedmap, shape_features
    rs = [runner_from_entry(race_entry(f"H{i}", f"R{i}", i + 1, result=i + 1), race_distance=1400) for i in range(3)]
    # H0 habitually leads, H2 habitually comes from last, H1 sits in between
    for r, share in zip(rs, (0.0, 0.5, 1.0)):
        r.raw.update(settle_share=share, pos800_share=share, pos_gain=0.0, late_gain=0.0)
    race_features(rs)
    assert set(POSITION) <= set(rs[0].x)
    assert [round(r.x["settle_share"], 4) for r in rs] == [-0.5, 0.0, 0.5]        # centred on the field
    shape_features(rs, positions_from_speedmap([{"horse_id": "H0", "predicted_position": 1},
                                                {"horse_id": "H2", "predicted_position": 3}]), tempo=-1.0)
    # a slow tempo (-1): the habitual leader reads positive, the habitual backmarker negative
    assert rs[0].x["style_x_tempo"] > 0 > rs[2].x["style_x_tempo"]
    assert set(STYLE) <= set(rs[0].x)
    # H0 is mapped to lead and habitually leads, so today asks nothing unusual of it
    assert round(rs[0].x["map_vs_habit"], 4) == 0.0


def test_fitting_to_winners_differs_from_fitting_to_the_market():
    """Fitting to BSP asks the model to be the market; fitting to winners asks it to be
    right. Where the two disagree the fitted weights must disagree too, or the choice of
    target would be decoration."""
    from fk.backtest import bsp_chances, fit, winner_chances
    races = []
    for i in range(12):
        rs = []
        # A is the market's favourite every time ($1.5 against $3), but B wins two in three.
        for hid, neural, bsp, won in (("A", 80, 1.5, i % 3 == 0), ("B", 40, 3.0, i % 3 != 0)):
            e = race_entry(hid, hid, 1 if hid == "A" else 2, result=1 if won else 2)
            r = runner_from_entry(e)
            r.raw["neural"] = neural
            r.bsp = bsp
            r.sp = bsp
            rs.append(r)
        race_features(rs)
        races.append(Race(f"R{i}", f"2026-08-{i + 1:02d}", "T", rs))
    to_market = fit(races, ["neural_rel"], target=bsp_chances)["neural_rel"]
    to_winners = fit(races, ["neural_rel"], target=winner_chances)["neural_rel"]
    # neural_rel is 1.0 for A and 0.5 for B, so a POSITIVE weight favours A
    assert to_market > 0                      # the market likes A, so fitting to BSP likes A
    assert to_winners < 0                     # B keeps winning, so fitting to winners turns against A
    assert winner_chances(races[0].runners) == [1.0, 0.0]
    assert winner_chances([races[0].runners[0]]) is None


def test_only_exp_is_barred_from_deployment_not_the_morning_market():
    """We bet into the morning price, so a model that uses it and lands closer to BSP than
    it does has beaten the market it is betting against. EXP stays barred: Form King derives
    it from the market without saying which one."""
    from fk.backtest import EXP, MARKET_FEATURE, MODEL_SETS, NON_DEPLOYABLE
    assert NON_DEPLOYABLE == set(EXP)
    assert MARKET_FEATURE not in NON_DEPLOYABLE
    assert not (set(MODEL_SETS["all_form_plus_open_market"]) & NON_DEPLOYABLE)
    assert set(MODEL_SETS["distance_shape_exp"]) & NON_DEPLOYABLE


def test_cross_validated_ridge_is_chosen_inside_the_training_races():
    """A stronger ridge must win when the features are noise, because a fit with no ridge
    memorises the noise and a cross-validated one will not."""
    import random
    from fk.backtest import RIDGES, fit_cv
    rng = random.Random(7)
    races = []
    for i in range(40):
        rs = []
        for hid in ("A", "B", "C"):
            e = race_entry(hid, hid, {"A": 1, "B": 2, "C": 3}[hid], result=1 if hid == "A" else 2)
            r = runner_from_entry(e)
            # the feature and the target are independent noise, so the true weight is zero
            r.raw["neural"] = rng.uniform(0, 100)
            r.bsp = r.sp = rng.uniform(1.5, 12.0)
            rs.append(r)
        race_features(rs)
        races.append(Race(f"R{i}", f"2026-08-{i % 28 + 1:02d}", "T", rs))
    beta, ridge = fit_cv(races, ["neural_rel"])
    assert ridge in RIDGES
    assert ridge > 1e-8                                  # noise must be shrunk, not fitted
    assert abs(beta["neural_rel"]) < 1.0                 # and the weight pulled towards zero
