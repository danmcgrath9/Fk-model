import gzip
import sys
from pathlib import Path

from fixtures import meeting_lite, race_summary, speedmap
from fk import history as H

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def _bundle(rid="FLEM_120926_3", results=True, state="VIC"):
    m = meeting_lite(state=state)
    form = race_summary(rid=rid, n_runners=3)
    if results:
        for i, e in enumerate(form["entries"]):
            e["horseResult"] = dict(finishPosition=i + 1, betfairStartingPrice=[2.5, 4.0, 6.0][i], startingPrice=[2.4, 3.8, 5.5][i])
    return H.race_bundle(m, form, speedmap(rid))


def test_bundle_carries_what_the_fit_reads_in_the_database_shape():
    b = _bundle()
    assert b["race_id"] == "FLEM_120926_3"
    assert b["date"] == "2026-09-12" and b["track"] == "Flemington" and b["state"] == "VIC"
    assert b["distance_m"] == 1400 and b["lws"] == 92.0
    assert len(b["entries"]) == 3 and all("pastEvents" in e for e in b["entries"])
    # speedmap runners in predicted early order: H2 and H0 both score 8.5, the lower pir leads
    assert [r["horse_id"] for r in b["speedmap"]] == ["H2", "H0", "H1"]
    assert [r["predicted_position"] for r in b["speedmap"]] == [1, 2, 3]
    assert b["tempo"]["description"] == "Average to Fast"
    assert H.is_resulted(b)
    assert not H.is_resulted(_bundle(results=False))


def test_no_speedmap_is_none_not_an_error():
    b = H.race_bundle(meeting_lite(), race_summary(), None)
    assert b["speedmap"] is None and b["tempo"] is None


def test_day_file_round_trips_and_a_top_up_keeps_what_was_there(tmp_path):
    a, b = _bundle("R_A"), _bundle("R_B")
    path = H.write_day(tmp_path, "2026-09-12", [a])
    assert path.name == "2026-09-12.jsonl.gz"
    with gzip.open(path, "rt") as fh:
        assert len(fh.readlines()) == 1
    H.write_day(tmp_path, "2026-09-12", [b])
    got = H.read_file(path)
    assert [x["race_id"] for x in got] == ["R_A", "R_B"]
    assert got[0] == a                          # nothing lost or altered in the round trip
    assert H.held_race_ids(tmp_path) == {"R_A", "R_B"}


def test_same_content_writes_the_same_bytes(tmp_path):
    p = H.write_day(tmp_path / "x", "2026-09-12", [_bundle("R_A")])
    q = H.write_day(tmp_path / "y", "2026-09-12", [_bundle("R_A")])
    assert p.read_bytes() == q.read_bytes()


def test_resulted_races_filters_state_results_and_what_the_database_holds(tmp_path):
    H.write_day(tmp_path, "2026-09-12", [_bundle("R_VIC"), _bundle("R_NSW", state="NSW"),
                                          _bundle("R_NORES", results=False), _bundle("R_INDB")])
    H.write_day(tmp_path, "2026-09-11", [_bundle("R_OLD")])
    ids = [b["race_id"] for b in H.resulted_races(tmp_path, "VIC", skip={"R_INDB"})]
    assert ids == ["R_OLD", "R_VIC"]            # oldest day first
    assert {b["race_id"] for b in H.resulted_races(tmp_path, None)} == {"R_VIC", "R_NSW", "R_INDB", "R_OLD"}


def test_no_directory_means_no_races():
    assert list(H.resulted_races(None)) == [] and H.held_race_ids(Path("/nonexistent/dir")) == set()


def test_a_file_race_becomes_the_same_race_the_database_row_would(tmp_path):
    import backtest as S
    b = _bundle()
    H.write_day(tmp_path, b["date"], [b])
    from_file, proj_file = S.races_from_rows(H.resulted_races(tmp_path, "VIC"))
    from_row, proj_row = S.races_from_rows([b])
    assert len(from_file) == 1
    assert [(r.horse_id, r.bsp, r.finish, r.x) for r in from_file[0].runners] == \
           [(r.horse_id, r.bsp, r.finish, r.x) for r in from_row[0].runners]
    assert [r.bsp for r in from_file[0].runners] == [2.5, 4.0, 6.0]
    assert proj_file.keys() == proj_row.keys() == {b["race_id"]}


def test_history_pull_imports():
    import history_pull  # noqa: F401  the script's imports resolve
