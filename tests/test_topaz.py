"""Topaz client and pull: no network, a fake session stands in for the API."""
import gzip
import json
from datetime import date

import pytest

from greyhound import pull as P
from greyhound.topaz import TopazClient, TopazError

KEY = "secret-key-123"


class Resp:
    def __init__(self, status, body=None, headers=None):
        self.status_code, self._body, self.headers = status, body, headers or {}
        self.text = json.dumps(body) if body is not None else ""

    def json(self):
        return self._body


class Session:
    """Answers each GET from a queue of responses and records what was asked."""
    def __init__(self, *responses):
        self.queue, self.asked = list(responses), []

    def get(self, url, headers=None, params=None, timeout=None):
        self.asked.append((url, dict(headers)))
        return self.queue.pop(0)


def client(*responses, **kw):
    s = Session(*responses)
    return TopazClient(KEY, session=s, sleep=lambda _s: None, **kw), s


def test_bulk_month_path_and_key_header():
    c, s = client(Resp(200, [{"dogId": 1}]))
    assert c.bulk_runs_month("VIC", 2024, 3) == [{"dogId": 1}]
    url, headers = s.asked[0]
    assert url == "https://topaz.grv.org.au/api/bulk/runs/VIC/2024/3"
    assert headers["X-API-Key"] == KEY


def test_key_never_in_repr_or_errors():
    c, _ = client(Resp(401), Resp(500, {"x": 1}))
    assert KEY not in repr(c)
    with pytest.raises(TopazError) as e:
        c.bulk_runs_month("VIC", 2024, 3)
    assert KEY not in str(e.value) and "401" in str(e.value)


def test_missing_key_is_refused(monkeypatch):
    monkeypatch.delenv("TOPAZ_API_KEY", raising=False)
    with pytest.raises(TopazError):
        TopazClient(session=Session())


def test_404_is_no_data_not_an_error():
    c, _ = client(Resp(404))
    assert c.bulk_runs_month("NSW", 2020, 1) == []


def test_429_and_5xx_retried_then_succeed_with_retry_after_honoured():
    waits = []
    s = Session(Resp(429, headers={"Retry-After": "7"}), Resp(503), Resp(200, [{"a": 1}]))
    c = TopazClient(KEY, session=s, sleep=waits.append, pause=2.0)
    assert c.bulk_runs_month("QLD", 2025, 6) == [{"a": 1}]
    assert 7.0 in waits and c.calls == 3


def test_retries_run_out():
    c, _ = client(*[Resp(500)] * 3, retries=2)
    with pytest.raises(TopazError, match="after 3 tries"):
        c.bulk_runs_month("SA", 2025, 6)


def test_unknown_state_refused_before_any_call():
    c, s = client()
    with pytest.raises(ValueError):
        c.bulk_runs_month("XYZ", 2025, 1)
    assert s.asked == []


def test_months_inclusive_across_a_year():
    assert P.months("2025-11", "2026-02") == [(2025, 11), (2025, 12), (2026, 1), (2026, 2)]
    with pytest.raises(ValueError):
        P.months("2026-03", "2026-02")


def test_still_moving_is_this_and_last_month_including_january():
    assert P.still_moving(2026, 1, date(2026, 1, 5)) and P.still_moving(2025, 12, date(2026, 1, 5))
    assert not P.still_moving(2025, 11, date(2026, 1, 5))


def test_pull_skips_held_months_repulls_moving_ones_and_respects_budget(tmp_path):
    today = date(2026, 10, 25)
    P.write_atomic(P.file_for(tmp_path, "VIC", 2026, 7), [{"old": 1}])   # held, settled
    P.write_atomic(P.file_for(tmp_path, "VIC", 2026, 9), [{"old": 1}])   # held, but last month: re-pulled
    c, s = client(Resp(200, [{"r": 8}]), Resp(200, [{"r": 9}]), Resp(200, []))
    rep = P.pull(c, ["VIC"], P.months("2026-07", "2026-10"), tmp_path, set(), today, max_calls=3)
    assert [(r[1], r[3]) for r in rep] == [("2026-07", "held"), ("2026-08", "pulled"),
                                           ("2026-09", "pulled"), ("2026-10", "pulled, empty")]
    with gzip.open(P.file_for(tmp_path, "VIC", 2026, 9), "rt") as f:
        assert json.load(f) == [{"r": 9}]
    c2, _ = client(Resp(200, [{"r": 1}]))
    rep2 = P.pull(c2, ["NSW"], P.months("2026-07", "2026-08"), tmp_path, set(), today, max_calls=1)
    assert [r[3] for r in rep2] == ["pulled", "budget"]
    assert not list(tmp_path.glob("*.part"))


def test_refresh_pulls_a_held_month_again(tmp_path):
    P.write_atomic(P.file_for(tmp_path, "VIC", 2024, 5), [])
    c, _ = client(Resp(200, [{"r": 1}]))
    rep = P.pull(c, ["VIC"], [(2024, 5)], tmp_path, {"2024-05"}, date(2026, 10, 25), max_calls=10)
    assert rep[0][3] == "pulled"


def test_main_refuses_without_terms_flag(monkeypatch, capsys):
    monkeypatch.delenv("TOPAZ_TERMS_READ", raising=False)
    monkeypatch.setenv("TOPAZ_API_KEY", KEY)
    assert P.main(["--probe"]) == 2
    assert "TOPAZ_TERMS_READ" in capsys.readouterr().out


def test_probe_prints_columns_not_contents(capsys):
    c, _ = client(Resp(200, {"ok": True}),
                  Resp(200, [{"dogName": "SECRET DOG", "boxNumber": 3}, {"dogName": "X", "boxNumber": None}]))
    P.probe(c, date(2026, 10, 18))
    out = capsys.readouterr().out
    assert "boxNumber" in out and "filled on 1/2" in out and "SECRET DOG" not in out


def test_no_access_is_its_own_error_and_not_retried():
    from greyhound.topaz import TopazNoAccess
    c, s = client(Resp(400, {"error": True, "message": "You do not have access to data before 1-Jan-2013 for VIC."}))
    with pytest.raises(TopazNoAccess):
        c.bulk_runs_day("VIC", 2013, 1, 1)
    assert len(s.asked) == 1


def test_by_day_builds_the_month_from_days_and_skips_days_outside_access(tmp_path):
    no = Resp(400, {"error": True, "message": "You do not have access to data before 1-Jan-2013 for VIC."})
    days = [no] + [Resp(200, [{"r": d}]) for d in range(2, 32)]             # Jan 2013: day 1 refused, 30 answer
    c, s = client(*days)
    rep = P.pull(c, ["VIC"], [(2013, 1)], tmp_path, set(), date(2026, 11, 4), max_calls=100, by_day=True)
    assert rep[0][2] == 30 and rep[0][3] == "pulled, 1 days outside the key's access"
    assert s.asked[0][0].endswith("/bulk/runs/VIC/2013/1/1") and s.asked[-1][0].endswith("/bulk/runs/VIC/2013/1/31")
    with gzip.open(P.file_for(tmp_path, "VIC", 2013, 1), "rt") as f:
        assert len(json.load(f)) == 30


def test_by_day_stops_at_today_in_the_current_month(tmp_path):
    c, s = client(*[Resp(200, []) for _ in range(3)])                       # 1-3 Nov: Topaz serves to yesterday
    rep = P.pull(c, ["VIC"], [(2026, 11)], tmp_path, set(), date(2026, 11, 4), max_calls=100, by_day=True)
    assert len(s.asked) == 3 and rep[0][3] == "pulled, empty"


def test_a_failed_or_unfinished_month_is_not_written_and_the_rest_carry_on(tmp_path):
    bad = [Resp(500)] * 5                                                   # one day fails after every retry
    c, _ = client(Resp(200, [{"r": 1}]), *bad, *[Resp(200, [{"r": 2}]) for _ in range(28)])
    rep = P.pull(c, ["VIC"], [(2014, 1), (2014, 2)], tmp_path, set(), date(2026, 11, 4), max_calls=1000,
                 by_day=True)
    assert rep[0][3].startswith("failed") and rep[0][2] is None
    assert not P.file_for(tmp_path, "VIC", 2014, 1).exists()
    assert rep[1][3] == "pulled" and rep[1][2] == 28                        # February still pulled
    c2, _ = client(*[Resp(200, [{"r": 1}]) for _ in range(5)])
    rep2 = P.pull(c2, ["VIC"], [(2015, 3)], tmp_path, set(), date(2026, 11, 4), max_calls=5, by_day=True)
    assert rep2[0][3] == "budget" and not P.file_for(tmp_path, "VIC", 2015, 3).exists()


class SlowDaySession:
    """Answers any day after a short wait, from several threads at once; records when each call started."""
    def __init__(self, wait=0.05):
        import threading
        self.wait, self.lock, self.asked, self.live, self.peak = wait, threading.Lock(), [], 0, 0

    def get(self, url, headers=None, params=None, timeout=None):
        import time
        with self.lock:
            self.asked.append((url, time.monotonic())); self.live += 1; self.peak = max(self.peak, self.live)
        time.sleep(self.wait)
        with self.lock:
            self.live -= 1
        return Resp(200, [{"day": int(url.rsplit("/", 1)[1])}])


def test_workers_overlap_calls_keep_the_cap_and_return_days_in_order(tmp_path):
    import time
    s = SlowDaySession(wait=0.05)
    c = TopazClient(KEY, session=s, max_per_minute=6000)                     # one start every 10 ms
    t0 = time.monotonic()
    rep = P.pull(c, ["VIC"], [(2014, 1)], tmp_path, set(), date(2026, 11, 4), max_calls=1000, by_day=True, workers=6)
    assert rep[0][2] == 31 and rep[0][3] == "pulled" and s.peak > 1           # overlapped
    starts = sorted(t for _, t in s.asked)
    assert starts[-1] - starts[0] >= 30 * 0.01 * 0.9                         # 31 starts span 30 slots: the cap held
    assert time.monotonic() - t0 < 31 * 0.05                                  # quicker than one at a time
    with gzip.open(P.file_for(tmp_path, "VIC", 2014, 1), "rt") as f:
        assert [r["day"] for r in json.load(f)] == list(range(1, 32))
