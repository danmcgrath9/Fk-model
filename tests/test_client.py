import pytest
import requests

from fk.client import FormKingClient, FormKingError, LiveCallRefused
from fk.config import TEST_API_KEY
from fk.credits import build_cost_table
from fk.ledger import Ledger
from fk.spec import Spec, SpecError
from mini_spec import MINI_SPEC


class FakeResponse:
    def __init__(self, status, body):
        self.status_code, self._body, self.text = status, body, str(body)
    def json(self):
        return self._body


class FakeSession:
    def __init__(self, status=200, body=None):
        self.calls, self.status, self.body = [], status, body if body is not None else {"ok": True}
    def request(self, method, url, params=None, headers=None, timeout=None):
        self.calls.append((method, url, params, headers))
        return FakeResponse(self.status, self.body)


def make(tmp_path, key=TEST_API_KEY, allow_live=False, session=None):
    spec = Spec(MINI_SPEC)
    ledger = Ledger(tmp_path / "l.sqlite", 1000)
    return FormKingClient(spec, key, ledger, build_cost_table(spec), allow_live=allow_live, session=session or FakeSession()), ledger


def test_plan_prices_and_validates_params(tmp_path):
    c, _ = make(tmp_path)
    p = c.plan("Get Race Form", raceId="R1", numBenchmarks=10)
    assert p.credits == 30
    with pytest.raises(SpecError):
        c.plan("Get Race Form", raceId="R1", numBenchmark=10)   # typo in a param name is refused
    with pytest.raises(SpecError):
        c.plan("Get Race Form")                                  # required path param missing


def test_call_builds_url_headers_and_records_ledger(tmp_path):
    s = FakeSession()
    c, ledger = make(tmp_path, session=s)
    out = c.call("Get Race Form", raceId="R1", numBenchmarks=10)
    assert out == {"ok": True}
    method, url, params, headers = s.calls[0]
    assert (method, url) == ("GET", "https://example.test/v1/races/R1/form")
    assert params == {"numBenchmarks": 10}
    assert headers["X-API-Key"] == TEST_API_KEY
    row = ledger.rows()[0]
    assert row.key_kind == "test" and row.credits == 30 and row.http_status == 200
    assert ledger.balance() == 1000   # test key never charged


def test_live_key_refused_without_allow_live(tmp_path):
    c, ledger = make(tmp_path, key="real-key")
    with pytest.raises(LiveCallRefused):
        c.call("Get Upcoming Meetings")
    assert ledger.rows() == []        # nothing hit the network, nothing recorded


def test_failed_live_call_is_still_ledgered(tmp_path):
    s = FakeSession(status=500, body={"error": "boom"})
    c, ledger = make(tmp_path, key="real-key", allow_live=True, session=s)
    with pytest.raises(FormKingError):
        c.call("Get Upcoming Meetings")
    row = ledger.rows()[0]
    assert row.http_status == 500 and row.credits == 1 and row.key_kind == "live"
    assert ledger.balance() == 999
