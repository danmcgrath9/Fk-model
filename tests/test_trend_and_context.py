from fixtures import past_event, race_entry, race_summary
from fk import fields as F
from fk.trend import linear_slope, trend


def test_slope_and_trend_reading():
    # hand-calculated: y = 80, 82, 84, 86 -> slope 2.0 per run
    assert linear_slope([80, 82, 84, 86]) == 2.0
    # hand-calculated over all five: x mean 2, y mean 80.4;
    # sum((x-2)(y-80.4)) = 20.8 + 0.4 + 0 + 3.6 + 11.2 = 36; sxx = 10 -> slope 3.6
    t = trend([70, 80, 82, 84, 86])
    assert round(t.slope, 6) == 3.6 and t.reading == "rising" and t.last == 86 and t.best == 86 and t.n == 5
    assert round(t.recent_mean, 2) == 84.0 and t.longer_mean == 80.4
    assert trend([90, 89.5, 90.2]).reading == "steady"
    assert trend([95, 92, 89]).reading == "falling"
    assert trend([88, None, 91]).reading == "too few runs" and trend([88, None, 91]).slope is None
    assert trend([]).last is None


def test_context_extractors_on_spec_shapes():
    e = race_entry("H1", "Quagmire", 4)
    e.update(form={"careerForm": "12: 3-2-1", "todaysGoingForm": "3: 1-0-1-1", "lengthsBeatenLastThree": 4.5, "wonWithTodaysWeightOrHigher": True},
             jockeyForm={"lastTwelveMonthRides": 812, "lastTwelveMonthWinPercentage": 14.2, "lastTwelveMonthPlacePercentage": 38.0,
                         "horseComboForm": "2: 1-0-0", "horseComboWinPercentage": 50.0, "trackComboForm": "40: 6-5-4", "trackComboWinPercentage": 15.0},
             trainerForm={"lastTwelveMonthWinPercentage": 18.5, "lastTwelveMonthForm": "300: 55-40-38", "horseComboForm": "", "jockeyComboForm": "9: 3-1-0",
                          "jockeyComboWinPercentage": 33.3, "trackComboForm": "50: 9-8-4", "trackComboWinPercentage": 18.0},
             gear=[{"gear": "Blinkers", "on": True, "change": "first time"}, {"gear": "Tongue Tie", "on": True, "change": ""}],
             raceInPrep=2, firstStarter=False, daysSinceLastWin=140, distanceChange="+200", benchmarkRating=78, totalPrizeMoney=245000)
    fr = F.entry_form_record(e)
    assert fr["careerForm"] == "12: 3-2-1" and fr["todaysGoingForm"] == "3: 1-0-1-1" and fr["lengthsBeatenLastThree"] == 4.5
    j = F.entry_jockey_form(e)
    assert j["rides12m"] == 812 and j["win12m"] == 14.2 and j["horseCombo"] == "2: 1-0-0"
    assert F.entry_trainer_form(e)["win12m"] == 18.5
    assert F.entry_gear(e) == (["Blinkers", "Tongue Tie"], ["Blinkers first time"])
    c = F.entry_context(e)
    assert c["runInPrep"] == 2 and c["ohr"] == 78 and c["distanceChange"] == "+200" and c["daysSinceLastWin"] == 140
    rf = F.race_facts(race_summary())
    assert rf["going"] == "Good" and rf["lws"] == 92.0 and rf["grade"] == "MSAT" and rf["prizemoney"] == 150000
    m = F.run_market(past_event("R1", 14))
    assert m["sp"] == 6.5 and m["finish"] == 3 and m["margin"] == 1.5 and m["distance"] == 1400
