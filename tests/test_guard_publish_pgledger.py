import os
from datetime import datetime, timezone

import pytest

from fk.guard import CreditCapExceeded, check_spend
from fk.ledger import Ledger
from publish_report import summary_markdown, upload_and_sign


def test_cap_and_floor():
    check_spend(300, 5000, cap=600, floor=1000)
    with pytest.raises(CreditCapExceeded):
        check_spend(3000, 20000, cap=600, floor=1000)      # the "3,000 instead of 300" case
    with pytest.raises(CreditCapExceeded):
        check_spend(300, 1200, cap=600, floor=1000)        # would leave 900, under the floor


def test_summary_markdown():
    md = summary_markdown([("2026-09-12-flemington.html", "https://x/signed")], 7, ["month 2026-09: balance 19700"])
    assert "[2026-09-12-flemington.html](https://x/signed)" in md and "7 days" in md and "balance 19700" in md
    assert "No report files" in summary_markdown([], 7, [])


class FakeResp:
    def __init__(self, status, body):
        self.status_code, self._body, self.text = status, body, str(body)
    def json(self):
        return self._body


class FakeSession:
    def __init__(self):
        self.posts = []
    def post(self, url, **kw):
        self.posts.append((url, kw))
        if "/object/sign/" in url:
            return FakeResp(200, {"signedURL": "/object/sign/fk-reports/a.html?token=abc"})
        return FakeResp(200, {"Key": "fk-reports/a.html"})


def test_upload_and_sign_builds_full_url(tmp_path):
    f = tmp_path / "a.html"
    f.write_text("<p>hi</p>")
    s = FakeSession()
    url = upload_and_sign("https://proj.supabase.co", "KEY", f, 7, session=s)
    assert url == "https://proj.supabase.co/storage/v1/object/sign/fk-reports/a.html?token=abc"
    up_url, kw = s.posts[0]
    assert up_url.endswith("/storage/v1/object/fk-reports/a.html") and kw["headers"]["x-upsert"] == "true"
    assert s.posts[1][1]["json"] == {"expiresIn": 7 * 86400}


@pytest.mark.skipif(not os.environ.get("FK_TEST_DATABASE_URL"), reason="set FK_TEST_DATABASE_URL to a Postgres with sql/001 and 002 applied")
def test_postgres_ledger_matches_sqlite_semantics():
    l = Ledger.postgres(os.environ["FK_TEST_DATABASE_URL"], monthly_allowance=100)
    l.conn.execute("delete from fk.credit_ledger")
    l.conn.commit()
    at = datetime(2026, 9, 11, tzinfo=timezone.utc)
    l.record("Get Race Form", 30, key_kind="live", params={"raceId": "R1"}, at=at)
    l.record("Get Race Form", 30, key_kind="test", at=at)
    l.adjust(5, "usage tab", at=at)
    assert l.spent("2026-09") == 35 and l.balance("2026-09") == 65
    rows = l.rows("2026-09")
    assert [r.balance_after for r in rows] == [70, None, 65]
    assert rows[0].params == {"raceId": "R1"}
    assert l.summary("2026-09")["by_operation"][0]["credits"] == 30
    l.close()
