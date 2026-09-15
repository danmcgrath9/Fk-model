"""The 'include all the data' pass: trend column and grid, form strip, runner context,
race facts, zero-as-absent ratings, the profile's run axis."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fixtures import past_event, race_entry, race_summary
from fk import fields as F
from fk.report.charts import RunnerProfile, TrendPanel, _tick_spec, ratings_profile_chart, short_date, trend_grid
from fk.report.html import ContextRow, FormStripRow, RaceSection, SummaryRow, context_html, form_strip_html, render_meeting, summary_table
from fk.trend import rating_series, trend


def test_zero_rating_is_absent_not_zero():
    p = past_event("R1", 14)
    p["weightForAgeRating"] = 0
    p["benchmark"]["atWeights"] = 0
    p["benchmark"]["speedRating"] = 0
    p["benchmark"]["vsClass"] = 0.0   # lengths vs class CAN be exactly par
    r = F.run_ratings(p)
    assert r["wfa"] is None and r["atWeights"] is None and r["speedRating"] is None
    assert r["vsClass"] == 0.0


def test_rating_series_prefers_todays_weight_and_skips_trials():
    runs = [dict(adjToday=88.0, atWeights=90.0, trial=False), dict(adjToday=None, atWeights=91.0, trial=False),
            dict(adjToday=99.0, trial=True), dict(wfaRat=85.0, trial=False), dict(trial=False)]
    assert rating_series(runs) == [88.0, 91.0, 85.0, None]
    assert rating_series(runs, races_only=False)[2] == 99.0


def test_summary_table_prints_trend_and_never_minus_zero():
    row = SummaryRow("A", 1, 55.0, "J", 14, 60.0, 58.0, 5.0, 6.0, 0.2, 0.25, None, trend="steady", slope=-0.01, last_rating=88.0, best_rating=92.0)
    out = summary_table([row])
    assert "steady +0.0" in out and "-0.0" not in out and "trend-steady" in out
    row2 = SummaryRow("B", 2, 55.0, "J", 14, 50.0, 58.0, 5.0, 6.0, 0.2, 0.25, None, trend="too few runs", slope=None)
    assert "too few runs" in summary_table([row2])


def test_form_strip_cell_and_padding():
    m = F.run_market(past_event("R1", 14))
    assert m["sp"] == 6.5 and m["finish"] == 3 and m["margin"] == 1.5
    m["runners"], m["going"], m["track"] = 12, "Good 4", "Flemington"
    out = form_strip_html([FormStripRow("A", [m])], n=3)
    assert "<b>3/12</b> 1.5L $6.50" in out and "Good 4 1400m Flemington 29 Aug 26" in out
    assert out.count("<td></td>") == 2   # two empty cells pad the strip to three runs
    t = dict(m, trial=True, margin=0.0, sp=0.0)
    cell = form_strip_html([FormStripRow("A", [t])], n=1)
    assert "class='l trial'" in cell and "<b>3/12</b> trial" in cell and "$0.00" not in cell and "0.0L" not in cell
    assert "$" not in form_strip_html([FormStripRow("A", [dict(m, sp=0.0)])], n=1).split("<b>")[1].split("<br>")[0]


def test_context_row_render():
    r = ContextRow("A", "12: 3-2-1", "3: 1-0-1", None, "1: 0-0-1", "4: 1-1-0", "2nd up: 3: 0-1-1", 140, 14.2, 18.5, "2: 1-0-0",
                   "Blinkers first time", 78.0, "+200", "4yo G", 245000.0)
    out = context_html([r])
    assert "14.2%" in out and "18.5%" in out and "245k" in out and "Blinkers first time" in out and "2nd up: 3: 0-1-1" in out
    assert context_html([]) == ""


def test_build_section_carries_facts_trend_strip_and_context():
    from build_report import build_section, context_row, race_facts_line
    summ = race_summary(n_runners=3)
    facts = race_facts_line(summ)
    assert facts[0] == "Going Good 4" and "BM78" in facts and "Prize $150,000" in facts and "LWS 92.0" in facts
    e = summ["entries"][0]
    e["raceInPrep"], e["form"] = 1, {"firstUpForm": "3: 1-0-0"}
    assert context_row({"name": "x", "raw": e}).prep == "1st up: 3: 1-0-0"
    entries = [dict(horse_id=x["breedingId"], name=x["horse"]["name"], barrier=x["barrier"], weight_kg=56.0, jockey="J", trainer="T",
                    scratched=False, neural_rating=x["ratings"]["neural"], exp_rating=58.0, days_since_last_run=14, raw=x) for x in summ["entries"]]
    events = {x["breedingId"]: [{"raw": p} for p in x["pastEvents"]] for x in summ["entries"]}
    runs = {x["breedingId"]: [{"run_id": f"{x['breedingId']}{i}", "event_date": "2026-08-01", "raw": p} for i, p in enumerate(x["pastEvents"])]
            for x in summ["entries"]}
    race = dict(race_number=3, race_name="Demo", distance_m=1400, raw=summ)
    sec = build_section(race, entries, runs, None, {}, events_by_horse=events)
    assert sec.facts[0] == "Going Good 4"
    assert len(sec.context) == 3 and len(sec.form_strip) == 3
    assert all(r.trend in ("steady", "rising", "falling") for r in sec.rows)   # five rated runs at 90.0: steady
    assert sec.rows[0].last_rating == 90.0 and sec.rows[0].best_rating == 90.0
    titles = [(f.layout.title.text or "") for f in sec.figures]
    assert any(t.startswith("Rating trend") for t in titles) and any(t.startswith("Ratings profile") for t in titles)
    html_out = render_meeting("t", "s", [sec], "note")
    assert "Form strip" in html_out and "Runner context" in html_out and "Going Good 4 &middot; BM78" in html_out


def test_trend_grid_and_profile_axes():
    panels = [TrendPanel("A", [80, 82, 84], ["2026-07-01", "2026-07-15", "2026-08-01"], "rising", 2.0, 90.0),
              TrendPanel("B", [88, 86], ["2026-07-01", "2026-08-01"], "too few runs", None, None)]
    fig = trend_grid(panels, "t")
    assert len(fig.data) == 3   # two lines and one peak
    assert fig.layout.yaxis.range == fig.layout.yaxis2.range == (78, 92)
    assert "A<br>rising +2.0/run" in [a.text for a in fig.layout.annotations]
    assert short_date("2025-11-14") == "14 Nov 25" and short_date("x") == "x"
    runs = [F.run_ratings(past_event(f"R{i}", 14 * (12 - i))) | {"date": f"2026-0{1 + i // 4}-{1 + i % 4:02d}"} for i in range(12)]
    prof = RunnerProfile("A", runs, 95.0, 93.0)
    vals, text = _tick_spec(prof)
    assert vals == [1, 4, 7, 12] and text[0] == "1 Jan 26"
    fig = ratings_profile_chart([prof], "p")
    assert fig.layout.showlegend is False and fig.layout.xaxis3.range == (0.3, 12.7)
    assert fig.data[0].x == tuple(range(1, 13))


def test_past_day_is_asked_for_by_date_and_filtered():
    from datetime import date
    from daily_pull import meetings_call, select_meetings
    from fixtures import meeting_lite
    from fk import ops

    class Client:
        def plan(self, op, **params):
            return (op, params)
    today = date(2026, 9, 12)
    assert meetings_call(Client(), date(2026, 4, 30), today, "VIC") == (ops.MEETINGS_BY_DATE, {"ddmmyy": "300426", "states": "VIC"})
    assert meetings_call(Client(), date(2026, 9, 13), today, "VIC") == (ops.UPCOMING_MEETINGS, {"states": "VIC"})
    assert meetings_call(Client(), today, today, "VIC")[0] == ops.UPCOMING_MEETINGS
    ms = [meeting_lite(mid="BALL", n_races=3), meeting_lite(mid="FLEM", n_races=2)]
    ms[0]["trackName"] = "Ballarat Synthetic"
    kept = select_meetings(ms, "ballarat", {1})
    assert [m["id"] for m in kept] == ["BALL"] and [r["number"] for r in kept[0]["races"]] == [1]
    assert len(ms[0]["races"]) == 3   # the caller's list is untouched
    assert select_meetings(ms, None, {9}) == []
    assert len(select_meetings(ms, None, None)) == 2


def test_summary_table_result_column_only_when_run():
    a = SummaryRow("A", 1, 55.0, "J", 14, 60.0, 58.0, 5.0, 6.0, 0.2, 0.25, None)
    assert "Result" not in summary_table([a])
    b = SummaryRow("B", 2, 55.0, "J", 14, 50.0, 58.0, 5.0, 6.0, 0.2, 0.25, None, finish=1, result_sp=4.6)
    c = SummaryRow("C", 3, 55.0, "J", 14, 40.0, 58.0, 5.0, 6.0, 0.2, 0.25, None, finish=12, result_sp=None)
    out = summary_table([a, b, c])
    assert "<th>Result</th>" in out and "1st $4.60" in out and "12th" in out


def test_fmt_never_prints_minus_zero():
    from fk.report.html import _fmt
    assert _fmt(-0.0, 1) == "0.0" and _fmt(-0.04, 1) == "0.0" and _fmt(-0.06, 1) == "-0.1" and _fmt(2.5, 1) == "2.5"


def test_report_uses_the_backtested_model_when_present(tmp_path):
    import json
    from build_report import build_section, load_rated_price_model, model_chances
    assert load_rated_price_model(tmp_path / "none.json") is None
    path = tmp_path / "rated_price.json"
    path.write_text(json.dumps({"beta": {"neural_rel": 8.0, "last_rel": 0.2, "peak_rel": 0.0, "peak12_rel": 0.0},
                                "features": ["neural_rel", "last_rel", "peak_rel", "peak12_rel"], "races": 120, "to": "2026-09-10"}))
    model = load_rated_price_model(path)
    summ = race_summary(n_runners=3)
    entries = [dict(horse_id=x["breedingId"], name=x["horse"]["name"], barrier=x["barrier"], weight_kg=56.0, jockey="J", trainer="T",
                    scratched=False, neural_rating=x["ratings"]["neural"], exp_rating=58.0, days_since_last_run=14, raw=x) for x in summ["entries"]]
    p = model_chances(model, entries)
    assert round(sum(p.values()), 9) == 1.0 and p["H2"] > p["H1"] > p["H0"]   # Neural 63 > 62 > 61, same ratings
    sec = build_section(dict(race_number=3, race_name="Demo", distance_m=1400, raw=summ), entries, {}, None, {}, rated_model=model)
    assert any(f.startswith("Rated by the back-tested model: fitted to Betfair SP over 120 races") for f in sec.facts)
    assert round(sum(r.model_prob for r in sec.rows), 9) == 1.0


def test_report_uses_the_projection_model_when_deployed():
    from build_report import build_section, load_rated_price_model
    from fk.projection import Params
    model = {"model": "projection_sim", "params": vars(Params()), "races": 209, "to": "2026-08-31", "features": None, "beta": None}
    summ = race_summary(n_runners=3)
    for i, x in enumerate(summ["entries"]):
        x["form"] = {"careerForm": f"{5 + i}: 1-0-0"}
    entries = [dict(horse_id=x["breedingId"], name=x["horse"]["name"], barrier=x["barrier"], weight_kg=56.0, jockey="J", trainer="T",
                    scratched=False, neural_rating=x["ratings"]["neural"], exp_rating=58.0, days_since_last_run=14, raw=x) for x in summ["entries"]]
    sm = [dict(horse_id="H0", predicted_position=1), dict(horse_id="H1", predicted_position=2), dict(horse_id="H2", predicted_position=3)]
    sec = build_section(dict(race_number=3, race_name="Demo", distance_m=1400, raw=summ), entries, {}, sm, {}, rated_model=model,
                        tempo_raw={"min": "-0.2", "max": "-0.1"})
    assert len(sec.projections) == 3 and sec.sim_runs == 20000
    assert round(sum(r.model_prob for r in sec.rows), 6) == 1.0
    assert any(f.startswith("Rated by the projection model") for f in sec.facts)
    out = render_meeting("t", "s", [sec], "note")
    assert "Projected figure and the sim" in out and "20,000 times" in out


def test_projection_table_shows_beside_a_logit_price():
    from build_report import build_section
    from fk.projection import Params
    model = {"model": "all_form", "beta": {"neural_rel": 8.0, "last_rel": 0.2, "peak_rel": 0.0, "peak12_rel": 0.0},
             "features": ["neural_rel", "last_rel", "peak_rel", "peak12_rel"], "races": 120, "to": "2026-09-10",
             "projection_params": vars(Params())}
    summ = race_summary(n_runners=3)
    entries = [dict(horse_id=x["breedingId"], name=x["horse"]["name"], barrier=x["barrier"], weight_kg=56.0, jockey="J", trainer="T",
                    scratched=False, neural_rating=x["ratings"]["neural"], exp_rating=58.0, days_since_last_run=14, raw=x) for x in summ["entries"]]
    sec = build_section(dict(race_number=3, race_name="Demo", distance_m=1400, raw=summ), entries, {}, None, {}, rated_model=model)
    assert len(sec.projections) == 3 and any(f.startswith("Rated by the back-tested model") for f in sec.facts)


def test_select_meetings_takes_several_tracks():
    from daily_pull import select_meetings
    from fixtures import meeting_lite
    ms = [meeting_lite(mid="A"), meeting_lite(mid="B"), meeting_lite(mid="C")]
    ms[0]["trackName"], ms[1]["trackName"], ms[2]["trackName"] = "Flemington", "Caulfield Heath", "Echuca"
    assert [m["id"] for m in select_meetings(ms, "flemington, caulfield", None)] == ["A", "B"]


def test_select_meetings_by_horse_name():
    from daily_pull import select_meetings
    from fixtures import meeting_lite
    ms = [meeting_lite(mid="A", n_races=3)]
    ms[0]["races"][1]["entries"][2]["horse"]["name"] = "Regal Ambition"
    kept = select_meetings(ms, None, None, "regal ambition")
    assert [r["number"] for r in kept[0]["races"]] == [2]
    assert select_meetings(ms, None, None, "Nobody") == []


def test_default_target_before_and_after_noon():
    from datetime import datetime, date
    from daily_pull import default_target
    # a run that GitHub started six hours late, 01:12 Tuesday: the pull is for Tuesday, not Wednesday
    assert default_target(datetime(2026, 9, 15, 1, 12)) == date(2026, 9, 15)
    assert default_target(datetime(2026, 9, 14, 18, 30)) == date(2026, 9, 15)
    assert default_target(datetime(2026, 9, 14, 12, 0)) == date(2026, 9, 15)
    assert default_target(datetime(2026, 9, 14, 11, 59)) == date(2026, 9, 14)


def test_result_column_falls_back_to_the_results_table():
    from build_report import build_section
    summ = race_summary(n_runners=3)
    entries = [dict(horse_id=x["breedingId"], name=x["horse"]["name"], barrier=x["barrier"], weight_kg=56.0, jockey="J", trainer="T",
                    scratched=False, neural_rating=x["ratings"]["neural"], exp_rating=58.0, days_since_last_run=14, raw=x) for x in summ["entries"]]
    sec = build_section(dict(race_number=3, race_name="Demo", distance_m=1400, raw=summ), entries, {}, None, {},
                        results={"H1": {"finish": 1, "sp": 4.6}, "H0": {"finish": 3, "sp": 9.0}})
    by = {r.name: r for r in sec.rows}
    assert by["Horse 1"].finish == 1 and by["Horse 1"].result_sp == 4.6 and by["Horse 0"].finish == 3 and by["Horse 2"].finish is None
