import pytest

from fk.credits import UnknownCost, build_cost_table, parse_cost_from_text
from fk.spec import Spec, SpecError
from mini_spec import MINI_SPEC


def test_operations_and_params_resolve_including_refs():
    spec = Spec(MINI_SPEC)
    op = spec.find_operation("Get Race Form")
    assert op.method == "get" and op.path == "/races/{raceId}/form"
    assert op.path_params() == ["raceId"]
    assert op.query_params() == ["numBenchmarks"]
    # shared path-level parameters are inherited
    assert spec.find_operation("get-meeting-speedmaps").path_params() == ["meetingId"]
    assert spec.find_operation("getRaceResults").summary == "Get Race Results"


def test_unknown_operation_lists_what_exists():
    with pytest.raises(SpecError) as e:
        Spec(MINI_SPEC).find_operation("Get Race Odds")
    assert "Get Race Form" in str(e.value) and "fk/ops.py" in str(e.value)


def test_server_and_header_come_from_spec():
    spec = Spec(MINI_SPEC)
    assert spec.base_url() == "https://example.test/v1"
    assert spec.api_key_header() == "X-API-Key"


def test_costs_from_table_prose_and_extension(tmp_path):
    table = build_cost_table(Spec(MINI_SPEC))
    assert table.cost_of("Get Upcoming Meetings") == 1          # info.description table
    assert table.cost_of("Get Meeting Speedmaps") == 5
    assert table.cost_of("Get Race Form", {"numBenchmarks": 10}) == 30   # operation description prose
    assert table.cost_of("Get Horse Profile", {"numBenchmarks": 5}) == 0   # x-credits tier
    assert table.cost_of("Get Horse Profile", {"numBenchmarks": 10}) == 4
    with pytest.raises(UnknownCost):
        table.cost_of("Get Race Results")   # nothing states it: refused, never assumed


def test_overrides_file_wins(tmp_path):
    f = tmp_path / "credits.yaml"
    f.write_text("Get Race Form:\n  - when: {numBenchmarks: '<=5'}\n    cost: 0\n  - cost: 12\nGet Race Results: 2\n")
    table = build_cost_table(Spec(MINI_SPEC), f)
    assert table.cost_of("Get Race Form", {"numBenchmarks": 5}) == 0
    assert table.cost_of("Get Race Form", {"numBenchmarks": 10}) == 12
    assert table.cost_of("Get Race Results") == 2


def test_parse_cost_from_text():
    assert parse_cost_from_text("This call costs 10 credits.") == 10
    assert parse_cost_from_text("Free of charge") == 0
    assert parse_cost_from_text("Returns the meeting list.") is None
