"""greyhound/isolynx.py: the dog list from cached runs, the resumable group pull, and the flattening."""
import gzip
import json
import os
import sys

import pytest

from greyhound import isolynx as I
from greyhound.topaz import TopazClient

sys.path.insert(0, os.path.dirname(__file__))
from test_topaz import Resp, Session  # noqa: E402


def write_runs(d, name, rows):
    with gzip.open(d / name, "wt", encoding="utf-8") as f:
        json.dump(rows, f)


def test_tracked_dogs_filters_by_track_and_date(tmp_path):
    write_runs(tmp_path, "runs_VIC_2024-03.json.gz", [
        {"dogId": 1, "trackName": "The Meadows", "meetingDate": "2024-03-02T00:00:00"},
        {"dogId": 2, "trackName": "Geelong", "meetingDate": "2024-03-02T00:00:00"},
        {"dogId": 3, "trackName": "Sandown Park", "meetingDate": "2024-03-01T00:00:00"}])
    write_runs(tmp_path, "runs_VIC_2021-03.json.gz", [{"dogId": 4, "trackName": "Sandown Park", "meetingDate": "2021-03-02"}])
    assert I.tracked_dogs(tmp_path, "2024-03-02") == [1]
    assert I.tracked_dogs(tmp_path, "2021-01-01") == [1, 3, 4]


def run_payload(race, dog, d):
    return {"raceId": race, "dogId": dog, "raceDate": d, "venueCode": "MEP", "raceDistance": 525, "boxNumber": 1,
            "place": 2, "resultTime": 30.1, "averageSpeed": 17.4, "maxSpeed": 18.9, "averageToRail": 1.2,
            "jumpSplit": {"elapsedTime": 0.3, "splitSpeed": 5.0, "averageToRail": 0.9, "positionInRunning": 3},
            "runnerSplitsFromStart50": [{"splitDistance": 50, "elapsedTime": 3.2, "splitSpeed": 15.6, "positionInRunning": 2},
                                        {"splitDistance": 100, "elapsedTime": 6.0, "splitSpeed": 17.9, "positionInRunning": 2}],
            "runnerSplitsToFinish50": [{"splitDistance": 100, "deltaTime": 2.9}, {"splitDistance": 50, "deltaTime": 3.0}],
            "runnerSplitsTrackMarks": [{"elapsedTime": 5.1, "positionInRunning": 2}]}


def test_pull_writes_groups_whole_skips_held_and_retries_failed(tmp_path, monkeypatch):
    monkeypatch.setattr(I, "GROUP", 2)
    s = Session(Resp(200, [run_payload(10, 1, "2024-03-02")]), Resp(200, []),       # group 0: dogs 1, 2
                Resp(500), Resp(500), Resp(500), Resp(500), Resp(500))               # group 1: dog 3 fails every try
    c = TopazClient("k", session=s, sleep=lambda _: None, max_per_minute=100000)
    rep = I.pull(c, [1, 2, 3], tmp_path, workers=1, max_minutes=10)
    assert rep["pulled"] == 1 and rep["failed"] == 1 and rep["runs"] == 1
    assert I.group_file(tmp_path, 0).exists() and not I.group_file(tmp_path, 1).exists()
    # a second run holds group 0 and retries group 1
    s2 = Session(Resp(200, [run_payload(11, 3, "2024-03-03")]))
    c2 = TopazClient("k", session=s2, sleep=lambda _: None, max_per_minute=100000)
    rep2 = I.pull(c2, [1, 2, 3], tmp_path, workers=1, max_minutes=10)
    assert rep2["held"] == 1 and rep2["pulled"] == 1 and len(s2.asked) == 1
    t = I.table(tmp_path)
    assert len(t) == 2 and set(t.race_id) == {10, 11}
    r = t[t.race_id == 10].iloc[0]
    assert (r.t50, r.v100, r.pos50, r.last100, r.last50, r.jump_pos, r.mark1_time) == (3.2, 17.9, 2, 5.9, 3.0, 3, 5.1)


def test_forbidden_stops_the_isolynx_pull_dead(tmp_path):
    from greyhound.topaz import TopazForbidden
    s = Session(Resp(401), Resp(200, []), Resp(200, []))
    c = TopazClient("k", session=s, sleep=lambda _: None, max_per_minute=100000)
    with pytest.raises(TopazForbidden):
        I.pull(c, [1, 2, 3], tmp_path, workers=1, max_minutes=10)
    assert len(s.asked) == 1 and not I.group_file(tmp_path, 0).exists()


def test_probe_reports_each_endpoint_by_shape_and_never_a_value(tmp_path, capsys):
    write_runs(tmp_path, "runs_VIC_2024-03.json.gz", [
        {"raceId": 500, "dogId": 1, "trackName": "The Meadows", "meetingDate": "2024-03-02T00:00:00"},
        {"raceId": 501, "dogId": 2, "trackName": "Sandown Park", "meetingDate": "2024-03-09T00:00:00"}])
    s = Session(Resp(200, [{"dogId": 2, "jumpSplit": {"elapsedTime": 0.31}, "resultTime": 29.87}]), Resp(401),
                Resp(200, {"positions": [1, 2], "raceId": 501}))
    c = TopazClient("k", session=s, sleep=lambda _: None)
    assert I.probe(c, tmp_path, "2024-01-01") == 0
    out = capsys.readouterr().out
    assert "probing race 501 (2024-03-09), dog 2" in out
    assert "isolynx/501/splits: ok, a list of 1; fields: dogId, jumpSplit, resultTime" in out
    assert "isolynx/501/positions: NOT ALLOWED" in out
    assert "isolynx/dog/2/splits: ok, an object; fields: positions, raceId" in out
    assert "29.87" not in out and "0.31" not in out


def test_trouble_finds_a_check_between_the_first_and_last_100_metres():
    from greyhound.isolynx import trouble

    def split(d, v, p):
        return {"splitDistance": d, "splitSpeed": v, "positionInRunning": p}
    # 400 m: steady 17 m/s, then at 250 m the speed dips to 15.4 and the dog drops from 2nd to 5th
    s = [split(50, 14, 3), split(100, 16.5, 2), split(150, 17, 2), split(200, 17, 2), split(250, 15.4, 5),
         split(300, 17, 5), split(350, 16.8, 4), split(400, 16.5, 4)]
    t = trouble(s, 400)
    assert abs(t["dip"] - (15.4 - 17.0)) < 1e-12 and t["pos_lost"] == 3 and t["checked"] == 1
    # the same run without the check: a gentle fade, no places lost; the jump at 50-100 m and the last 100 m ignored
    clean = [split(50, 14, 6), split(100, 16.5, 2), split(150, 17, 2), split(200, 17, 2), split(250, 16.9, 2),
             split(300, 16.8, 2), split(350, 15.0, 5), split(400, 14.0, 6)]
    t = trouble(clean, 400)
    assert t["checked"] == 0 and t["pos_lost"] == 0 and abs(t["dip"] - (16.9 - 16.9)) < 1e-12
    assert trouble([], 400) == {"dip": None, "pos_lost": None, "checked": None}
