from datetime import date

from fk.cache import decide_profile_fetch, merge_runs
from fk.client import FormKingClient
from fk.config import TEST_API_KEY
from fk.credits import build_cost_table
from fk.estimate import estimate
from fk.ledger import Ledger
from fk.spec import Spec
from mini_spec import MINI_SPEC


def test_profile_policy():
    assert decide_profile_fetch("h", None, None, None).num_benchmarks == 10
    known = {"profile_depth": 10, "profile_fetched_at": "2026-09-01"}
    assert decide_profile_fetch("h", known, date(2026, 9, 1), date(2026, 9, 1)).num_benchmarks is None
    assert decide_profile_fetch("h", known, date(2026, 9, 1), date(2026, 9, 8)).num_benchmarks == 5
    assert decide_profile_fetch("h", known, date(2026, 9, 1), None).num_benchmarks is None


def test_merge_runs_unions_and_orders_newest_first():
    old = [{"run_id": "a", "event_date": "2026-08-01"}, {"run_id": "b", "event_date": "2026-08-15", "x": 1}]
    new = [{"run_id": "b", "event_date": "2026-08-15", "x": 2}, {"run_id": "c", "event_date": "2026-09-01"}]
    merged = merge_runs(old, new)
    assert [r["run_id"] for r in merged] == ["c", "b", "a"]
    assert merged[1]["x"] == 2


def test_estimate_groups_by_operation_and_price(tmp_path):
    spec = Spec(MINI_SPEC)
    c = FormKingClient(spec, TEST_API_KEY, Ledger(tmp_path / "l.sqlite"), build_cost_table(spec))
    plans = [c.plan("Get Meeting Speedmaps", meetingId="M")] + [c.plan("Get Race Form", raceId=f"R{i}", numBenchmarks=10) for i in range(9)]
    est = estimate(plans)
    # 5 + 9 x 30 = 275, hand-calculated
    assert est.total == 275
    assert [(l.operation, l.calls, l.credits) for l in est.lines] == [("Get Meeting Speedmaps", 1, 5), ("Get Race Form", 9, 270)]
    assert "TOTAL" in est.render(1000) and "after this run 725" in est.render(1000)
