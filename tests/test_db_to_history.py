"""db_to_history: nothing is deleted from the database unless the release holds every
moved race exactly as the database served it."""
import sys
from decimal import Decimal
from pathlib import Path

from fk import history as H

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import db_to_history as M  # noqa: E402


def _row(rid, day="2026-06-01", pre=True, state="VIC"):
    # the shape Db.resulted_races returns, Decimal included (Postgres numeric)
    return {"race_id": rid, "date": day, "track": "Sale", "distance_m": 1200, "lws": Decimal("91.5"),
            "entries": [{"horse": {"id": "H1"}, "horseResult": {"finishPosition": 1, "betfairStartingPrice": 3.4}}],
            "speedmap": None, "tempo": None, "going": "Good 4", "state": state, "pulled_before_jump": pre}


def test_a_race_reads_back_from_its_day_file_with_the_same_fingerprint(tmp_path):
    rows = [M.normalise(_row("SALE_010626_1")), M.normalise(_row("SALE_010626_2"))]
    for day, bundles in M.plan_days(rows).items():
        H.write_day(tmp_path, day, bundles)
    manifest = {r["race_id"]: M.fingerprint(r) for r in rows}
    assert M.check(manifest, tmp_path) == []
    assert rows[0]["lws"] == 91.5                 # Decimal became a float before it was fingerprinted


def test_a_missing_or_altered_race_fails_the_check(tmp_path):
    a, b = M.normalise(_row("R_A")), M.normalise(_row("R_B"))
    H.write_day(tmp_path, "2026-06-01", [a])
    changed = dict(b, track="Moe")
    H.write_day(tmp_path, "2026-06-01", [changed])
    manifest = {"R_A": M.fingerprint(a), "R_B": M.fingerprint(b), "R_C": M.fingerprint(a)}
    assert M.check(manifest, tmp_path) == ["R_B", "R_C"]


def test_merging_into_an_existing_day_keeps_the_races_already_there(tmp_path):
    H.write_day(tmp_path, "2026-06-01", [M.normalise(_row("OLD"))])
    H.write_day(tmp_path, "2026-06-01", [M.normalise(_row("NEW"))])
    assert H.held_race_ids(tmp_path) == {"OLD", "NEW"}


def test_days_are_grouped_and_in_order():
    rows = [_row("B", "2026-06-02"), _row("A", "2026-06-01"), _row("C", "2026-06-02")]
    assert {d: [r["race_id"] for r in rs] for d, rs in M.plan_days(rows).items()} == {"2026-06-01": ["A"], "2026-06-02": ["B", "C"]}


def test_the_pulled_before_the_jump_flag_is_read_from_the_files(tmp_path):
    H.write_day(tmp_path, "2026-06-01", [M.normalise(_row("LIVE")), M.normalise(_row("BACKFILL", pre=False)),
                                          M.normalise(_row("NSWLIVE", state="NSW"))])
    assert H.pulled_before_jump_ids(tmp_path, "VIC") == {"LIVE"}
    assert H.pulled_before_jump_ids(tmp_path, None) == {"LIVE", "NSWLIVE"}

    class FakeDb:
        def races_pulled_before_the_jump(self, state):
            return {"STILL_IN_DB"}
    assert H.pulled_before_jump(FakeDb(), tmp_path, "VIC") == {"LIVE", "STILL_IN_DB"}


def test_a_moved_race_reads_back_as_resulted_for_the_fit(tmp_path):
    H.write_day(tmp_path, "2026-06-01", [M.normalise(_row("SALE_010626_1"))])
    got = list(H.resulted_races(tmp_path, "VIC"))
    assert [b["race_id"] for b in got] == ["SALE_010626_1"] and got[0]["going"] == "Good 4"
