"""Bot log lines name the bookmaker account holder; Actions logs on this repo are public, so the name never prints."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "betmatic"))
from betmatic_send import redact_account  # noqa: E402


def test_account_holder_name_is_replaced():
    line = "[2026/10/27 07:22:40] TAB, Jane Example Smith : Skipped - Account balance is below Min Stake ($) (1)."
    out = redact_account(line)
    assert "Jane" not in out and "Smith" not in out
    assert out == "[2026/10/27 07:22:40] TAB, [account holder] : Skipped - Account balance is below Min Stake ($) (1)."


def test_lines_without_a_name_are_unchanged():
    for line in ("[2026/10/27 07:22:40] Add Tasks: 13996590",
                 "[2026/10/27 07:22:40] Checked availability — no sessions available for this notification GEELONG R1 N1.",
                 None):
        assert redact_account(line) == str(line)
