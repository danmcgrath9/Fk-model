from fixtures import meeting_lite, ms, past_event, race_entry, race_summary, speedmap
from fk import fields as F
from fk import ops
from fk.cache import decide_profile_fetch, merge_runs
from fk.client import FormKingClient
from fk.config import TEST_API_KEY
from fk.credits import build_cost_table
from fk.estimate import estimate
from fk.ledger import Ledger
from fk.spec import Spec
from conftest import ROOT


def test_meeting_fields_and_melbourne_date():
    m = meeting_lite()
    assert F.meeting_id(m) == "FLEM_120926" and F.meeting_state(m) == "VIC" and F.meeting_track(m) == "Flemington"
    assert F.meeting_date(m) == "2026-09-12"
    # 15:00 UTC on the 11th is 01:00 on the 12th in Melbourne (AEST, +10): the Melbourne date wins
    assert F.epoch_ms_to_melbourne_date(ms(2026, 9, 11) + 12 * 3600 * 1000) == "2026-09-12"
    races = F.meeting_races(m)
    assert F.race_id(races[0]) == "FLEM_120926_1" and F.race_runner_count(races[0]) == 3   # one of four scratched


def test_entry_fields():
    e = race_entry("H7", "Quagmire", 7, result=1)
    assert F.horse_id(e) == "H7" and F.horse_name(e) == "Quagmire" and F.entry_number(e) == 7
    assert F.entry_weight(e) == 55.5 and F.entry_neural_rating(e) == 67 and F.entry_exp_rating(e) == 58.0
    o = F.entry_odds(e)
    assert F.odds_current_price(o) == 5.5 and F.odds_opening_price(o) == 6.0 and F.odds_firm_or_drift(o) == 2.4
    r = F.entry_result(e)
    assert F.result_finish_position(r) == 1 and F.result_starting_price(r) == 5.5 and F.result_betfair_sp(r) == 5.8
    assert F.race_market_percentage(race_summary()) == 118.0


def test_positions_and_splits_in_running_order():
    p = past_event("R1", 14)
    # [Settle, 1200, 1000, 800, 600, 400, 200, Finish]: this run has pir8/6/4/2 and no 1200/1000 markers
    assert F.run_positions(p) == [5, None, None, 5, 5, 4, 3, 3]
    # first slot is S-8 because the race's first split is 8-6; 1200 and 1000 splits absent
    assert F.run_splits_vs_class(p) == [-0.4, None, None, 0.1, 0.5, 0.9, 1.2]
    assert F.run_to_600_vs_class(p) == -0.3 and F.run_last_600_vs_class(p) == 0.9
    assert F.past_event_track_speed_verified(p) is True
    bare = past_event("R2", 7, with_benchmark=False)
    assert F.run_positions(bare) == [5, None, None, 5, None, 4, None, 3]
    assert F.run_splits_vs_class(bare) == [None] * 7
    assert F.past_event_is_race(past_event("R3", 3, race=False)) is False


def test_speedmap_order_and_tempo():
    sm = speedmap()
    order = [(F.horse_id(e), rank) for e, rank in F.speedmap_predicted_order(F.speedmap_entries(sm))]
    # H2 and H0 tie on early speed 8.5; H2's lower settling score puts it in front
    assert order == [("H2", 1), ("H0", 2), ("H1", 3)]
    assert F.tempo_description(F.speedmap_tempo(sm)) == "Average to Fast"


def test_profile_policy_is_first_sight_only():
    assert decide_profile_fetch("h", None, 0).num_benchmarks == 10
    assert decide_profile_fetch("h", None, 5).num_benchmarks == 10
    assert decide_profile_fetch("h", None, 10).num_benchmarks is None
    assert decide_profile_fetch("h", {"profile_fetched_at": "2026-09-01"}, 3).num_benchmarks is None


def test_merge_runs_unions_and_orders_newest_first():
    old = [{"run_id": "a", "event_date": "2026-08-01"}, {"run_id": "b", "event_date": "2026-08-15", "x": 1}]
    new = [{"run_id": "b", "event_date": "2026-08-15", "x": 2}, {"run_id": "c", "event_date": "2026-09-01"}]
    merged = merge_runs(old, new)
    assert [r["run_id"] for r in merged] == ["c", "b", "a"] and merged[1]["x"] == 2


def test_saturday_meeting_estimate(tmp_path):
    spec = Spec.load(ROOT / "b2c-openapi.yaml")
    c = FormKingClient(spec, TEST_API_KEY, Ledger(tmp_path / "l.sqlite"), build_cost_table(spec, ROOT / "credits.yaml"))
    plans = [c.plan(ops.UPCOMING_MEETINGS, states="VIC"), c.plan(ops.MEETING_SPEEDMAPS, meetingId="M")]
    plans += [c.plan(ops.RACE_FORM, meetingId="M", raceId=f"R{i}", numBenchmarks=5, racesOnly=True, runners=12) for i in range(9)]
    cheap = estimate(plans).total          # 1 + 5 + 9 x 2 = 24, then 5 per never-seen horse
    deep = estimate(plans[:2] + [c.plan(ops.RACE_FORM, meetingId="M", raceId=f"R{i}", numBenchmarks=10, racesOnly=True, runners=12) for i in range(9)]).total
    assert cheap == 24
    assert deep == 1 + 5 + 9 * 32           # 294: the brief's "about 300 credits" for a nine-race Saturday at depth 10


def test_zero_position_means_no_marker():
    p = past_event("R9", 14)
    p["pos1200m"] = 0
    p["benchmark"]["pir8"] = 0
    # [Settle, 1200, 1000, 800, 600, 400, 200, Finish]: 1200 sent as 0 -> None; pir8 0 falls back to pos800m
    assert F.run_positions(p) == [5, None, None, 5, 5, 4, 3, 3]
