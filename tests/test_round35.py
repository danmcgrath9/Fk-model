"""Round 35: the Betwatch field at TAB's open against who ran (topaz_round35)."""
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round35 as R35  # noqa: E402


def _race(rid="r1", day="2024-03-02"):
    fl = lambda p, t: {"Tab": {"last": [p, t], "flucs": [[p, t]]}}   # noqa: E731
    return {"id": rid, "date": day, "start": f"{day}T09:00:00Z", "runners": [
        {"name": "Alpha", "scratched": None, "emergency": False, "books": fl(2.0, f"{day}T00:00:00Z")},
        {"name": "Bravo", "scratched": None, "emergency": False, "books": fl(4.0, f"{day}T00:00:00Z")},
        {"name": "Charlie", "scratched": f"{day}T05:00:00Z", "emergency": False, "books": fl(5.0, f"{day}T00:00:00Z")},
        {"name": "Delta", "scratched": None, "emergency": True, "books": fl(8.0, f"{day}T00:10:00Z")},
        {"name": "Echo", "scratched": f"{day}T00:00:00Z", "emergency": False, "books": {}},
    ]}


def test_race_audit_marks_the_field_at_the_open_and_the_later_scratching():
    rows = {r["dog_raw"]: r for r in R35.race_audit(_race())}
    assert rows["Alpha"]["in_field"] and not rows["Alpha"]["later"]
    assert rows["Charlie"]["in_field"] and rows["Charlie"]["later"]
    assert rows["Delta"]["in_field"] and rows["Delta"]["emergency"] and not rows["Delta"]["scr_time"]
    assert not rows["Echo"]["in_field"]
    book = 1 / 2 + 1 / 4 + 1 / 5 + 1 / 8
    assert abs(rows["Alpha"]["book"] - book) < 1e-12 and abs(rows["Delta"]["share"] - (1 / 8) / book) < 1e-12
    assert rows["Alpha"]["n_later"] == 1 and rows["Alpha"]["ded"] == 0.20   # 100c / $5 = 20c
    assert rows["Alpha"]["lead_h"] == 9.0


def test_an_emergency_topaz_has_scratched_is_a_phantom(tmp_path, capsys):
    bw, tz = tmp_path / "bw", tmp_path / "tz"
    bw.mkdir()
    tz.mkdir()
    with gzip.open(bw / "betwatch_VIC_G_2024-03.json.gz", "wt") as fh:
        json.dump({"races": [_race()]}, fh)
    runs = [{"meetingDate": "2024-03-02", "dogName": n, "raceId": 7, "scratched": s}
            for n, s in (("ALPHA", False), ("BRAVO", False), ("CHARLIE", True), ("DELTA", True), ("ECHO", True))]
    with gzip.open(tz / "runs_VIC_2024-03.json.gz", "wt") as fh:
        json.dump(runs, fh)
    a = R35.mark_topaz(R35.load(str(bw)), R35.topaz_status(str(tz)))
    st = dict(zip(a._dn, a.tz))
    assert st == {"ALPHA": "ran", "BRAVO": "ran", "CHARLIE": "scratched", "DELTA": "scratched", "ECHO": "scratched"}
    os.environ["BETWATCH_DIR"] = str(bw)
    try:
        assert R35.main(str(tz), "t") == 0
    finally:
        del os.environ["BETWATCH_DIR"]
    out = capsys.readouterr().out
    row = next(line for line in out.splitlines() if line.startswith("| 2024-03 |"))
    cells = [c.strip() for c in row.strip("|").split("|")]
    assert cells[13] == "1.00" and cells[14] == "100.0%" and cells[16] == "100%"   # one phantom, an emergency
    assert "| 2024 | 3 | 66.7% | 33.3% |" in out
