import pytest

from fk import fields as F
from fk.report.charts import RunnerRuns, SpeedmapRunner, position_worm, recency_weighted_mean, sectional_worm, speedmap_chart
from fk.report.html import RaceSection, SummaryRow, render_meeting, summary_table
from fk.report.probability import disagreement, market_implied, rating_implied


def test_market_implied_removes_overround():
    p = market_implied({"a": 2.0, "b": 4.0, "c": None})
    # 1/2 + 1/4 = 0.75; a = 0.5/0.75 = 0.6667, b = 0.3333
    assert p["c"] is None
    assert round(p["a"], 4) == 0.6667 and round(p["b"], 4) == 0.3333


def test_rating_implied_is_a_points_share():
    p = rating_implied({"a": 14.5, "b": 13.4, "c": 2.1, "d": None})
    assert p["d"] is None and abs(p["a"] + p["b"] + p["c"] - 1) < 1e-9
    # 14.5 / (14.5 + 13.4 + 2.1) = 0.4833
    assert round(p["a"], 4) == 0.4833
    # zero points gets a 1% floor of the top, never nothing
    q = rating_implied({"a": 40.0, "b": 0.0})
    assert round(q["b"], 4) == round(0.4 / 40.4, 4)


def test_disagreement_threshold():
    assert disagreement(0.20, 0.26) == "model_higher"
    assert disagreement(0.20, 0.14) == "market_higher"
    assert disagreement(0.20, 0.24) is None
    assert disagreement(None, 0.24) is None


def test_recency_weighted_mean_skips_missing_sections():
    # newest run weight 1, older 0.8: section 0 = (1*2 + 0.8*4)/1.8 = 5.2/1.8 = 2.8889; section 1 only in the older run = 6
    out = recency_weighted_mean([[2.0, None], [4.0, 6.0]], 2, decay=0.8)
    assert round(out[0], 4) == 2.8889 and round(out[1], 9) == 6.0


def test_charts_build():
    r = [RunnerRuns("h1", "One", ["800m", "600m", "400m", "Finish"], [[4, 4, 3, 1], [5, 5, 4, 2]], ["2026-09-01", "2026-08-15"]),
         RunnerRuns("h2", "Two", ["800m", "600m", "400m", "Finish"], [[1, 1, 1, 3]], ["2026-09-01"])]
    fig = position_worm(r, "t")
    assert len(fig.data) == 3 and fig.layout.yaxis.autorange == "reversed"
    fig2 = sectional_worm(r, "t")
    assert len(fig2.data) == 2
    fig3 = speedmap_chart([SpeedmapRunner("One", 3, 80), SpeedmapRunner("Two", 1, 95)], "t")
    assert list(fig3.data[0].y) == ["Leader", "Backmarker"]


def test_summary_table_sorts_by_neural_and_flags():
    rows = [SummaryRow("Low", 1, 54.0, "J", 14, 55.0, 50.0, 10.0, 12.0, 0.08, 0.05, None),
            SummaryRow("High", 2, 56.5, "K", 7, 70.0, 60.0, 3.0, 2.5, 0.30, 0.45, "model_higher")]
    html = summary_table(rows)
    assert html.index("High") < html.index("Low")
    assert "flag-model" in html and "Neural &gt; market" in html or "Neural > market" in html
    assert "drift" in html  # High: 3.0 from 2.5 opening
    page = render_meeting("T", "sub", [RaceSection("Race 1", "1200m", [], rows)], "note")
    assert "<table>" in page and "plotly" in page


def test_fields_fail_loudly_when_unmapped():
    with pytest.raises(F.FieldUnmapped) as e:
        F.horse_id({"runnerId": 1})
    assert "runnerId" in str(e.value) and "fk/fields.py" in str(e.value)
    assert F.pick({"a": {"b": 2}}, "x", ["a.b"]) == 2
    assert F.entry_barrier({"barrier": "7"}) == 7
    assert F.entry_barrier({}) is None


def test_pricing_helpers():
    from fk.report.probability import market_percentage, rated_price, settling_group, tempo_reading, value_points
    # 1/2 + 1/4 + 1/5 = 0.95 -> a 95% market (an exchange-like book); None when nothing priced
    assert round(market_percentage({"a": 2.0, "b": 4.0, "c": 5.0}), 1) == 95.0
    assert market_percentage({"a": None}) is None
    assert rated_price(0.25) == 4.0 and rated_price(None) is None
    # Betfair Hub's example: 20% rated against 12.5% market is +7.5 points
    assert round(value_points(0.125, 0.20), 1) == 7.5
    assert [settling_group(r, 10) for r in range(1, 11)] == [
        "Leader", "On pace", "On pace", "On pace", "Midfield", "Midfield", "Off pace", "Off pace", "Backmarker", "Backmarker"]
    assert tempo_reading(3).startswith("pressure") and tempo_reading(1).startswith("likely slow")


def test_lane_map_and_late_speed_and_ladders():
    from fk.report.charts import (LateSpeedRow, lane_assignments, late_speed_table, market_move_chart, speedmap_chart,
                                  value_ladder)
    sm = [SpeedmapRunner("Slow", 4.0, 60, 3), SpeedmapRunner("Lead", 1.0, 95, 7), SpeedmapRunner("Mid", 2.5, 80, 1),
          SpeedmapRunner("Unknown", None, None, 9)]
    placed = lane_assignments(sm)
    assert [(r.name, rank, lane) for r, rank, lane in placed] == [("Lead", 1, "Leader"), ("Mid", 2, "Midfield"), ("Slow", 3, "Backmarker")]
    fig = speedmap_chart(sm, "t")
    assert list(fig.data[0].text) == ["7", "1", "3"]        # barrier in the marker
    assert list(fig.data[0].x) == [3, 2, 1]                   # leader furthest right
    secs = ["1000m", "800m", "600m", "400m", "200m", "Finish"]
    rows = late_speed_table([RunnerRuns("a", "A", secs, [[0.0, 0.0, 0.0, 1.0, 1.0, 1.0]]),
                             RunnerRuns("b", "B", secs, [[2.0, 2.0, 2.0, -1.0, -1.0, -1.0]])])
    # last 600m = final three sections: A averages +1.00, B -1.00; to the 600: A 0.00, B +2.00
    assert [(r.name, r.to_600, r.last_600) for r in rows] == [("A", 0.0, 1.0), ("B", 2.0, -1.0)]
    v = value_ladder(["A", "B", "C"], [-3.0, 7.5, None], "t")
    assert list(v.data[0].y) == ["B", "A"]
    m = market_move_chart(["A", "B"], [4.0, 3.0], [3.0, 3.6], "t")
    assert [round(x, 1) for x in m.data[0].x] == [-25.0, 20.0]   # A firmed 25%, B drifted 20%


def test_probabilities_accept_decimals_from_postgres():
    from decimal import Decimal
    from fk.report.probability import market_implied, rating_implied
    assert round(market_implied({"a": Decimal("2.0"), "b": Decimal("4.0")})["a"], 4) == 0.6667
    assert round(rating_implied({"a": Decimal("70.0"), "b": Decimal("30.0")})["a"], 4) == 0.7


def test_drop_empty_columns():
    from build_report import drop_empty_columns
    r = [RunnerRuns("a", "A", ["Settle", "1200m", "800m", "Finish"], [[3, None, 2, 1], [4, None, 3, 2]]),
         RunnerRuns("b", "B", ["Settle", "1200m", "800m", "Finish"], [[5, None, None, 4]])]
    out = drop_empty_columns(r)
    assert out[0].sections == ["Settle", "800m", "Finish"] and out[0].runs[0] == [3, 2, 1] and out[1].runs[0] == [5, None, 4]


def test_run_ratings_and_profile_chart():
    from fixtures import past_event
    from fk.report.charts import RunnerProfile, ratings_profile_chart
    p = past_event("R1", 14)
    p["benchmark"]["sections"]["6-F"].update(raceRank=2, meetRatingRank=17)
    p.update(weightForAgeRating=91.5, numRunners=12)
    r = F.run_ratings(p)
    assert r["atWeights"] == 90.0 and r["wfa"] == 91.5 and r["speedRating"] == 101.0 and r["vsClass"] == 0.8
    assert r["ranks"] == {"section": "6-F", "raceRank": 2, "meetRank": None, "meetRatingRank": 17}
    assert r["finish"] == 3 and r["runners"] == 12 and r["trial"] is False
    profiles = [RunnerProfile("A", [r, dict(r, date="2026-08-01", trial=True)], 95.0, 93.0), RunnerProfile("B", [r], None, None)]
    fig = ratings_profile_chart(profiles, "t")
    assert len(fig.layout.updatemenus[0].buttons) == 2
    per = len(fig.data) // 2
    assert all(t.visible for t in fig.data[:per]) and not any(t.visible for t in fig.data[per:])
    assert fig.data[0].text[0] == "3/12 r2 m17"                       # finish, race rank, meeting rank beside the point
    assert fig.data[0].marker.symbol[1] == "circle-open"               # the trial is hollow
    assert F.entry_peak_ratings({"ratings": {"peak": 95.0, "peak12m": 93.0}}) == (95.0, 93.0)
