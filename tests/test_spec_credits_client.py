"""Against the real spec (b2c-openapi.yaml 1.0.8) and the committed credits.yaml."""
import pytest

from conftest import ROOT
from fixtures import race_summary
from fk import ops
from fk.client import FormKingClient, FormKingError, LiveCallRefused
from fk.config import TEST_API_KEY
from fk.credits import UnknownCost, build_cost_table
from fk.fields import count_benchmarks
from fk.ledger import Ledger
from fk.spec import Spec, SpecError

SPEC = Spec.load(ROOT / "b2c-openapi.yaml")
COSTS = build_cost_table(SPEC, ROOT / "credits.yaml")


def test_every_operation_in_ops_exists_in_the_spec():
    names = [ops.UPCOMING_MEETINGS, ops.MEETINGS_BY_DATE, ops.MEETING_SUMMARY, ops.MEETING_SPEEDMAPS, ops.RACE_FORM, ops.HORSE_FORM, ops.USAGE_LOG]
    paths = {n: SPEC.find_operation(n).path for n in names}
    assert paths[ops.RACE_FORM] == "/b2c/meetings/{meetingId}/races/{raceId}"
    assert paths[ops.HORSE_FORM] == "/b2c/horses/{horseId}"
    assert paths[ops.MEETING_SUMMARY] == "/b2c/meetings/{meetingId}"
    assert SPEC.base_url() == "https://api.formking.com.au"
    assert SPEC.api_key_header() == "x-api-key"
    assert SPEC.version == "1.0.8"


def test_costs_match_the_spec_table():
    # flat costs from the "Credit Sizing by API" table
    assert COSTS.cost_of(ops.UPCOMING_MEETINGS) == 1
    assert COSTS.cost_of(ops.MEETING_SUMMARY) == 5
    assert COSTS.cost_of(ops.MEETING_SPEEDMAPS) == 5
    # race form: 2 at numBenchmarks<=5; at 10 with 12 runners 2 + 0.5 x 5 x 12 = 32, inside the spec's "15 to 50"
    assert COSTS.cost_of(ops.RACE_FORM, {"numBenchmarks": 5}) == 2
    assert COSTS.cost_of(ops.RACE_FORM, {}) == 2                     # default depth is 5
    assert COSTS.cost_of(ops.RACE_FORM, {"numBenchmarks": 10}, runners=12) == 32
    assert COSTS.cost_of(ops.RACE_FORM, {"numBenchmarks": 10}, runners=6) == 17
    # horse form at 10: 2 + 2.5 = 4.5, rounded up to 5 (the spec's "max cost is 12" is at full depth)
    assert COSTS.cost_of(ops.HORSE_FORM, {"numBenchmarks": 10}) == 5
    # actual charge from the response: 12 runners with 8 benchmarks each = 2 + 0.5 x 3 x 12 = 20
    assert COSTS.actual_cost(ops.RACE_FORM, {"numBenchmarks": 10}, [8] * 12) == 20
    # numBenchmarks=8 with one runner: 2 + 1.5 = 3.5 -> 4 (the 1.0.8 release note's rounding example)
    assert COSTS.actual_cost(ops.HORSE_FORM, {"numBenchmarks": 8}, [8]) == 4
    with pytest.raises(UnknownCost):
        COSTS.cost_of("Get Something Else")


def test_count_benchmarks_reads_both_shapes():
    rs = race_summary(n_runners=3, n_benchmarks=4)
    assert count_benchmarks(rs) == [4, 4, 4]
    assert count_benchmarks({"id": "H0", "pastEvents": rs["entries"][0]["pastEvents"]}) == [4]
    assert count_benchmarks([]) is None


class FakeResponse:
    def __init__(self, status, body):
        self.status_code, self._body, self.text, self.headers = status, body, str(body), {}
    def json(self):
        return self._body


class FakeSession:
    def __init__(self, status=200, body=None):
        self.calls, self.status, self.body = [], status, body if body is not None else {"ok": True}
    def request(self, method, url, params=None, headers=None, timeout=None):
        self.calls.append((method, url, params, headers))
        return FakeResponse(self.status, self.body)


def make(tmp_path, key=TEST_API_KEY, allow_live=False, session=None):
    ledger = Ledger(tmp_path / "l.sqlite", 1000)
    return FormKingClient(SPEC, key, ledger, COSTS, allow_live=allow_live, session=session or FakeSession()), ledger


def test_plan_validates_params_against_the_spec(tmp_path):
    c, _ = make(tmp_path)
    p = c.plan(ops.RACE_FORM, meetingId="M", raceId="R", numBenchmarks=10, racesOnly=True, runners=12)
    assert p.credits == 32
    with pytest.raises(SpecError):
        c.plan(ops.RACE_FORM, meetingId="M", raceId="R", numBenchmark=10)   # typo refused
    with pytest.raises(SpecError):
        c.plan(ops.RACE_FORM, raceId="R")                                   # meetingId missing
    assert c.plan(ops.UPCOMING_MEETINGS, states="VIC").credits == 1


def test_call_builds_url_and_ledgers_the_actual_charge(tmp_path):
    body = race_summary(n_runners=3, n_benchmarks=8)     # asked 10, got 8 each: 2 + 0.5 x 3 x 3 = 6.5 -> 7
    s = FakeSession(body=body)
    c, ledger = make(tmp_path, session=s)
    out = c.call(ops.RACE_FORM, meetingId="FLEM_120926", raceId="FLEM_120926_3", numBenchmarks=10, racesOnly=True, runners=3)
    assert out is body
    method, url, params, headers = s.calls[0]
    assert (method, url) == ("GET", "https://api.formking.com.au/b2c/meetings/FLEM_120926/races/FLEM_120926_3")
    assert params == {"numBenchmarks": 10, "racesOnly": True}
    assert headers["x-api-key"] == TEST_API_KEY
    row = ledger.rows()[0]
    assert row.credits == 7 and "estimated 10, charged 7" in (row.note or "")   # asked 10 over 3 runners: 2 + 7.5 -> 10
    assert ledger.balance() == 1000    # test key: recorded, never charged


def test_live_key_refused_without_allow_live(tmp_path):
    c, ledger = make(tmp_path, key="real-key")
    with pytest.raises(LiveCallRefused):
        c.call(ops.UPCOMING_MEETINGS)
    assert ledger.rows() == []


def test_failed_live_call_is_still_ledgered(tmp_path):
    s = FakeSession(status=402, body={"error": "Payment Required"})
    c, ledger = make(tmp_path, key="real-key", allow_live=True, session=s)
    with pytest.raises(FormKingError):
        c.call(ops.UPCOMING_MEETINGS)
    row = ledger.rows()[0]
    assert row.http_status == 402 and row.credits == 1 and row.key_kind == "live"


def test_server_error_is_retried_once_then_raised(tmp_path, monkeypatch):
    import fk.client as client_mod
    monkeypatch.setattr(client_mod.time, "sleep", lambda s: None)
    s = FakeSession(status=500, body={"message": "Internal server error"})
    c, ledger = make(tmp_path, session=s)
    with pytest.raises(FormKingError):
        c.call(ops.MEETING_SPEEDMAPS, meetingId="caulfield-20260711")
    assert len(s.calls) == 2                 # one retry
    assert len(ledger.rows()) == 2           # both attempts ledgered, as the spec bills them
