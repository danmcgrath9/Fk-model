"""Greyhound ratings engine (greyhound/ratings.py): hand-checked pieces, then a simulation where the true speed of every
dog is known, so the ratings can be scored against the truth before any real data exists."""
import numpy as np
import pandas as pd
import pytest

from greyhound import ratings as R


def run(race, meeting, day, dog, finish, margin=0.0, win_time=30.0, split=np.nan, track="T", dist=500, trial=False,
        time=np.nan):
    return dict(race_id=race, meeting_id=meeting, date=pd.Timestamp(day), track=track, distance=dist, grade="Gr5",
                dog=dog, box=1, finish=finish, margin=margin, time=time, win_time=win_time, split=split, is_trial=trial)


def test_dog_time_from_margin_and_one_length_is_point_07_seconds():
    df = pd.DataFrame([run(1, 1, "2025-01-01", "A", 1), run(1, 1, "2025-01-01", "B", 2, margin=2.0)])
    assert list(R.dog_time(df)) == [30.0, pytest.approx(30.14)]


def test_par_uses_earlier_days_only_and_needs_enough_winners():
    rows = [run(i, i, f"2025-01-{i:02d}", f"D{i}", 1, win_time=30.0 + 0.01 * i) for i in range(1, 6)]
    df = pd.DataFrame(rows)
    p = R.pars(df, min_n=3)
    # day 1-3: fewer than 3 earlier winners -> no par; day 4: median of days 1-3 = 30.02; day 5: median of 1-4 = 30.025
    assert p.par_time.isna().tolist()[:3] == [True, True, True]
    assert p.par_time.iloc[3] == pytest.approx(30.02)
    assert p.par_time.iloc[4] == pytest.approx(30.025)


def test_variant_is_the_meetings_winners_against_par_shrunk():
    df = pd.DataFrame([run(1, 7, "2025-02-01", "A", 1, win_time=30.3), run(2, 7, "2025-02-01", "B", 1, win_time=30.1)])
    par = pd.DataFrame({"par_time": [30.0, 30.0], "par_split": [np.nan, np.nan]}, index=df.index)
    v = R.meeting_variant(df, par, shrink=0.0)
    assert v.variant_time.tolist() == [pytest.approx(0.2)] * 2          # (0.3 + 0.1) / 2
    v2 = R.meeting_variant(df, par, shrink=2.0)
    assert v2.variant_time.iloc[0] == pytest.approx(0.1)                # 0.4 / (2 + 2)


def test_elo_records_the_rating_before_the_race_and_is_zero_sum():
    df = pd.DataFrame([run(1, 1, "2025-01-01", "A", 1), run(1, 1, "2025-01-01", "B", 2),
                       run(2, 2, "2025-01-02", "A", 2), run(2, 2, "2025-01-02", "B", 1)])
    e = R.elo(df, k=20)
    assert e.iloc[0] == e.iloc[1] == 1500                               # first race: everyone at the start
    assert e.iloc[2] == pytest.approx(1510) and e.iloc[3] == pytest.approx(1490)   # A beat B: +/- k x (1 - 0.5)
    assert e.iloc[2] + e.iloc[3] == pytest.approx(3000)


def test_elo_draw_between_equals_changes_nothing_and_a_non_finisher_loses():
    df = pd.DataFrame([run(1, 1, "2025-01-01", "A", 2), run(1, 1, "2025-01-01", "B", 2),
                       run(1, 1, "2025-01-01", "C", np.nan),
                       run(2, 2, "2025-01-02", "A", 1), run(2, 2, "2025-01-02", "B", 2),
                       run(2, 2, "2025-01-02", "C", 3)])
    e = R.elo(df, k=20)
    a, b, c = e.iloc[3], e.iloc[4], e.iloc[5]
    assert a == pytest.approx(b) and a > 1500 and c < 1500


def test_trials_are_not_races_for_elo_but_count_as_first_starter_form():
    df = pd.DataFrame([run(1, 1, "2025-01-01", "A", 1, split=5.0, trial=True),
                       run(2, 2, "2025-01-05", "A", 1, split=5.1)])
    e = R.elo(df)
    assert np.isnan(e.iloc[0]) and e.iloc[1] == 1500


def simulate(n_dogs=240, days=200, seed=0):
    """Dogs with a true speed (lengths better than average) and a true early speed; 2 tracks x 2 distances with their
    own pars; every meeting has a going offset; times are par + going - speed x 0.07 + noise."""
    rng = np.random.default_rng(seed)
    speed = rng.normal(0, 3, n_dogs)
    early = 0.6 * speed + rng.normal(0, 2, n_dogs)
    par = {("A", 400): 23.0, ("A", 500): 29.0, ("B", 400): 23.4, ("B", 500): 29.6}
    rows, race = [], 0
    for d in range(days):
        for track in ("A", "B"):
            meeting, going = f"{track}{d}", rng.normal(0, 0.15)
            for r in range(8):
                race += 1
                dist = 400 if r % 2 else 500
                idx = rng.choice(n_dogs, 8, replace=False)
                t = par[(track, dist)] + going - speed[idx] * R.SEC_PER_LENGTH + rng.normal(0, 0.12, 8)
                sp = 5.3 + going * 0.2 - early[idx] * R.SEC_PER_LENGTH + rng.normal(0, 0.04, 8)
                order = np.argsort(t)
                fin = np.empty(8); fin[order] = np.arange(1, 9)
                wt = t.min()
                for i in range(8):
                    rows.append(run(race, meeting, pd.Timestamp("2024-01-01") + pd.Timedelta(days=d), f"dog{idx[i]}",
                                    int(fin[i]), margin=(t[i] - wt) / R.SEC_PER_LENGTH, win_time=wt, split=sp[i],
                                    track=track, dist=dist))
    return pd.DataFrame(rows), speed, early


def test_simulation_ratings_recover_true_speed_and_the_variant_helps():
    df, speed, early = simulate()
    rated = R.run_ratings(df)
    df = df.join(rated)
    ok = df.time_rating.notna()
    true = df.dog.str[3:].astype(int).map(lambda i: speed[i])
    true_e = df.dog.str[3:].astype(int).map(lambda i: early[i])
    c_with = np.corrcoef(df.time_rating[ok], true[ok])[0, 1]
    no_var = (rated.par_time - R.dog_time(df)) / R.SEC_PER_LENGTH
    c_without = np.corrcoef(no_var[ok], true[ok])[0, 1]
    assert c_with > 0.85 and c_with > c_without + 0.02                 # the going variant earns its place
    oks = df.split_rating.notna()
    assert np.corrcoef(df.split_rating[oks], true_e[oks])[0, 1] > 0.85


def test_simulation_form_and_elo_rank_dogs_and_never_see_the_race_itself():
    df, speed, _ = simulate()
    rated = R.run_ratings(df)
    form = R.dog_form(df, rated)
    e = R.elo(df)
    true = df.dog.str[3:].astype(int).map(lambda i: speed[i])
    late = df.date >= df.date.quantile(0.5)
    for col in (form.time_rating_mean5, e):
        ok = late & col.notna()
        assert np.corrcoef(col[ok], true[ok])[0, 1] > 0.7
    # point in time: a dog's first race has no form, whatever it ran that day
    first = df.groupby("dog").date.transform("min") == df.date
    assert form.loc[first, "time_rating_last"].isna().all() and (e[first] == R.ELO_START).all()


def topaz_row(race, dog, box, place, time, margin, split=5.4, **kw):
    """One BulkRunOutput row with the fields the mapping reads (names from Topaz API 1.8.1's swagger.json)."""
    r = dict(raceId=race, meetingId=900 + race, meetingDate="2026-03-14T00:00:00.000Z", trackCode="MEP",
             trackName="The Meadows", distanceInMetres=525, incomingGrade="5", dogId=dog, dogName=f"DOG {dog}",
             boxNumber=box, place=place, resultTime=time, resultMargin=margin, firstSplitTime=split,
             scratched=False, abnormalResult=None, raceType="Grade 5", raceTypeCode="G5", startPrice=4.2,
             weightInKg=31.5)
    r.update(kw)
    return r


def test_topaz_mapping_from_the_published_fields():
    raw = pd.DataFrame([
        topaz_row(1, 11, 1, 1, 29.80, 0.25),                     # winner: Topaz gives its margin over second
        topaz_row(1, 12, 2, 2, 30.05, 0.25),                     # resultMargin is seconds: 0.25 s = 3.571 lengths
        topaz_row(1, 13, 3, None, None, None, abnormalResult="FELL"),
        topaz_row(1, 14, 4, None, None, None, scratched=True),   # never ran: dropped
        topaz_row(2, 11, 5, 2, 30.10, 0.5, raceType="Trial", raceTypeCode="TRL"),
    ])
    runs = R.topaz_to_runs(raw)
    assert len(runs) == 4 and "14" not in set(runs.dog)
    w = runs[(runs.race_id == 1) & (runs.dog == "11")].iloc[0]
    assert (w.finish, w.margin, w.time, w.win_time, w.split) == (1, 0.0, 29.80, 29.80, 5.4)
    assert w.date == pd.Timestamp("2026-03-14") and w.track == "MEP" and w.distance == 525 and w.box == 1
    assert w.start_price == 4.2 and w.dog_name == "DOG 11" and not w.is_trial
    second = runs[(runs.race_id == 1) & (runs.dog == "12")].iloc[0]
    assert second.margin == pytest.approx(0.25 / R.SEC_PER_LENGTH) and second.win_time == 29.80
    assert R.dog_time(runs).iloc[1] == pytest.approx(30.05)    # own time kept; margin agrees with it
    fell = runs[runs.dog == "13"].iloc[0]
    assert np.isnan(fell.finish) and np.isnan(fell.time) and fell.abnormal == "FELL"
    assert runs[runs.race_id == 2].is_trial.all()
    # the canonical table feeds the engine as is
    assert R.run_ratings(runs).shape[0] == 4 and R.elo(runs).notna().sum() == 3


def test_topaz_mapping_names_a_missing_field():
    with pytest.raises(ValueError, match="resultTime"):
        R.topaz_to_runs(pd.DataFrame([topaz_row(1, 11, 1, 1, 29.8, 0)]).drop(columns="resultTime"))


def test_load_topaz_reads_the_pulls_files(tmp_path):
    import gzip
    import json
    rows = [topaz_row(1, 11, 1, 1, 29.8, 0.2), topaz_row(1, 12, 2, 2, 30.0, 0.2)]
    with gzip.open(tmp_path / "runs_VIC_2026-03.json.gz", "wt", encoding="utf-8") as f:
        json.dump(rows, f)
    runs = R.load_topaz(tmp_path)
    assert list(runs.dog) == ["11", "12"] and runs.win_time.tolist() == [29.8, 29.8]


def test_shrunk_form_pulls_a_short_record_toward_the_grade_prior():
    # two Gr5 dogs: A ran +2 and +4 lengths on days 1 and 2, B +0 and +0; on day 3 the prior is the grade mean so far
    df = pd.DataFrame([run(1, 1, "2025-01-01", "A", 1, win_time=29.86), run(1, 1, "2025-01-01", "B", 2, margin=2.0, win_time=29.86),
                       run(2, 2, "2025-01-02", "A", 1, win_time=29.72), run(2, 2, "2025-01-02", "B", 2, margin=4.0, win_time=29.72),
                       run(3, 3, "2025-01-03", "A", 1), run(3, 3, "2025-01-03", "B", 2)])
    rated = pd.DataFrame({"time_rating": [2.0, 0.0, 4.0, 0.0, np.nan, np.nan]}, index=df.index)
    sf = R.shrunk_form(df, rated, k=3.0)
    # day 3: prior = mean of the four earlier ratings = 1.5; A's sum 6 over 2 runs -> (6 + 3 x 1.5) / (2 + 3) = 2.1
    assert sf.grade_prior.iloc[4] == pytest.approx(1.5)
    assert sf.time_rating_shrunk.iloc[4] == pytest.approx(2.1) and sf.rating_runs.iloc[4] == 2
    assert sf.time_rating_shrunk.iloc[5] == pytest.approx((0 + 4.5) / 5)
    assert sf.rating_runs.iloc[0] == 0 and sf.time_rating_shrunk.iloc[0] == 0.0     # first ever: the (empty) prior


def test_context_form_is_the_dogs_mean_in_the_same_band_and_track():
    df = pd.DataFrame([run(1, 1, "2025-01-01", "A", 1, track="T", dist=400), run(2, 2, "2025-01-02", "A", 1, track="U", dist=525),
                       run(3, 3, "2025-01-03", "A", 1, track="T", dist=390), run(4, 4, "2025-01-04", "A", 1, track="T", dist=600)])
    rated = pd.DataFrame({"time_rating": [1.0, 5.0, 3.0, np.nan]}, index=df.index)
    cf = R.context_form(df, rated)
    assert cf.time_rating_band.iloc[2] == pytest.approx(1.0) and cf.runs_band.iloc[2] == 1    # sprint: day 1 only
    assert cf.time_rating_track.iloc[2] == pytest.approx(1.0)                              # track T: day 1 only
    assert np.isnan(cf.time_rating_band.iloc[3]) and cf.runs_band.iloc[3] == 0              # never raced staying
    assert cf.time_rating_track.iloc[3] == pytest.approx(2.0) and cf.runs_track.iloc[3] == 2  # T: days 1 and 3


def test_margin_elo_gives_a_nose_defeat_nearly_half_and_a_rout_the_lot():
    df = pd.DataFrame([run(1, 1, "2025-01-01", "A", 1), run(1, 1, "2025-01-01", "B", 2, margin=3.0),
                       run(2, 2, "2025-01-02", "A", 1), run(2, 2, "2025-01-02", "B", 2, margin=0.1)])
    e = R.margin_elo(df, k=24, scale=3.0)
    gain = 24 * (0.5 + 0.5 * np.tanh(1.0) - 0.5)          # beaten by 3 lengths at scale 3: 0.88 of a win
    assert e.iloc[2] == pytest.approx(1500 + gain) and e.iloc[3] == pytest.approx(1500 - gain)
    assert e.iloc[2] + e.iloc[3] == pytest.approx(3000)
    df2 = pd.DataFrame([run(1, 1, "2025-01-01", "A", 1), run(1, 1, "2025-01-01", "B", 2, margin=0.1),
                        run(2, 2, "2025-01-02", "A", 1), run(2, 2, "2025-01-02", "B", 2)])
    e2 = R.margin_elo(df2, k=24, scale=3.0)
    assert 0 < e2.iloc[2] - 1500 < 1.0                      # a nose: almost nothing changes hands
