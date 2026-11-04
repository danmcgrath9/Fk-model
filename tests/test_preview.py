"""greyhound/preview.py: the pre-race snapshot and the day-after compare, on a fake session; no comment text printed."""
import json
import os
import sys

from greyhound import preview as PV
from greyhound.topaz import TopazClient

sys.path.insert(0, os.path.dirname(__file__))
from test_topaz import Resp, Session  # noqa: E402

KEY = "k"


def test_snapshot_hashes_comments_and_compare_counts_changes(tmp_path, capsys):
    upcoming = Resp(200, [{"raceId": 7, "startTime": "x", "analystComment": "Open race", "tip1": 3, "isRaceResultEntered": False}])
    runs = Resp(200, [{"runId": 1, "dogId": 11, "comment": "Needs luck from the draw", "rating": 80, "isBestBet": True,
                       "startPrice": 4.5},
                      {"runId": 2, "dogId": 12, "comment": "", "rating": 70, "isBestBet": False, "startPrice": None}])
    c = TopazClient(KEY, session=Session(upcoming, runs), sleep=lambda _: None)
    assert PV.snapshot(c, tmp_path, 10) == 0
    out = capsys.readouterr().out
    assert "Needs luck" not in out and "comment filled on 1/2" in out
    snap = json.loads(next(tmp_path.glob("preview_*.json")).read_text())
    day = snap["taken"][:10]
    bulk = Resp(200, [{"runId": 1, "comment": "Needs luck from the draw", "rating": 80, "isBestBet": True, "startPrice": 6.0},
                      {"runId": 2, "comment": "Was slow away", "rating": 70, "isBestBet": False, "startPrice": 9.0}])
    c2 = TopazClient(KEY, session=Session(bulk), sleep=lambda _: None)
    assert PV.compare(c2, tmp_path, day) == 0
    out = capsys.readouterr().out
    assert "same 1" in out and "empty before, filled after 1" in out and "rating the same 2/2" in out
    assert "startPrice 0/2" in out and "slow away" not in out
