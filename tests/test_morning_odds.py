import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from morning_odds import merged_entry  # noqa: E402


def test_the_morning_refresh_keeps_the_evening_form_and_takes_the_new_prices():
    stored = {"pastEvents": ["a", "b"], "recentTrials": ["t"], "odds": {"bestNow": 4.0}, "scratched": False}
    fresh = {"pastEvents": ["a"], "odds": {"bestNow": 5.0}, "scratched": True, "horseResult": {"finishPosition": 1}}
    out = merged_entry(stored, fresh)
    assert out["pastEvents"] == ["a", "b"] and out["recentTrials"] == ["t"]
    assert out["odds"] == {"bestNow": 5.0} and out["scratched"] is True and out["horseResult"] == {"finishPosition": 1}
    # nothing stored yet: the fresh entry as it is
    assert merged_entry(None, fresh) == fresh
    # a stored copy with no history does not blank the fresh one's
    assert merged_entry({"pastEvents": []}, fresh)["pastEvents"] == ["a"]
