from datetime import datetime, timezone

from fk.ledger import Ledger


def test_balance_is_derived_from_live_rows_only(tmp_path):
    l = Ledger(tmp_path / "c.sqlite", monthly_allowance=100)
    at = datetime(2026, 9, 11, tzinfo=timezone.utc)
    l.record("Get Race Form", 30, key_kind="live", at=at)
    l.record("Get Race Form", 30, key_kind="test", at=at)
    l.record("Get Upcoming Meetings", 1, key_kind="live", at=at)
    assert l.spent("2026-09") == 31
    assert l.balance("2026-09") == 69
    rows = l.rows("2026-09")
    assert [r.balance_after for r in rows] == [70, None, 69]   # test rows carry no balance


def test_month_window_and_reconciliation(tmp_path):
    l = Ledger(tmp_path / "c.sqlite", monthly_allowance=20000)
    l.record("Get Race Form", 30, at=datetime(2026, 8, 31, 23, 59, tzinfo=timezone.utc))
    l.record("Get Race Form", 30, at=datetime(2026, 9, 1, 0, 1, tzinfo=timezone.utc))
    assert l.spent("2026-08") == 30 and l.spent("2026-09") == 30
    # site says 45 used in September: we under-counted by 15
    l.adjust(45 - l.spent("2026-09"), "usage tab", at=datetime(2026, 9, 2, tzinfo=timezone.utc))
    assert l.spent("2026-09") == 45
    assert l.balance("2026-09") == 19955
    assert l.summary("2026-09")["by_operation"][0]["operation"] == "Get Race Form"


def test_billing_period_runs_from_the_invoice_day(tmp_path):
    # This account's allowance resets on the 11th (invoice paid 11 Sep 2026), not the 1st.
    l = Ledger(tmp_path / "c.sqlite", monthly_allowance=20000, period_start_day=11)
    l.record("Get Race Form", 5, at=datetime(2026, 9, 10, 23, 59, tzinfo=timezone.utc))   # last period
    l.record("Get Race Form", 7, at=datetime(2026, 9, 11, 0, 0, tzinfo=timezone.utc))     # this one starts
    l.record("Get Race Form", 11, at=datetime(2026, 10, 1, 0, 1, tzinfo=timezone.utc))    # 1 Oct: same period
    l.record("Get Race Form", 13, at=datetime(2026, 10, 11, 0, 0, tzinfo=timezone.utc))   # next period
    assert l.spent("2026-08") == 5
    assert l.spent("2026-09") == 7 + 11
    assert l.spent("2026-10") == 13
    assert l.period(datetime(2026, 10, 1, tzinfo=timezone.utc))[0] == "2026-09"
    assert [r.balance_after for r in l.rows()] == [19995, 19993, 19982, 19987]
