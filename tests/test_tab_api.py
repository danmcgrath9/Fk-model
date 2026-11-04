"""greyhound/tab_api.py: meetings filtered to Victorian greyhounds, race links followed, the open read when present."""
import csv

from greyhound import tab_api as TA


class Resp:
    def __init__(self, status, body):
        self.status_code, self._body = status, body

    def json(self):
        return self._body


class Session:
    def __init__(self, answers):
        self.answers, self.asked = answers, []

    def get(self, url, params=None, timeout=None, headers=None):
        self.asked.append((url, dict(params or {})))
        return self.answers[url]


MEETINGS = {"meetings": [
    {"meetingName": "SANDOWN PARK", "location": "VIC", "raceType": "G",
     "races": [{"raceNumber": 1, "_links": {"self": f"{TA.BASE}/racing/dates/2026-11-05/meetings/G/SAP/races/1?jurisdiction=VIC"}},
               {"raceNumber": 2, "_links": {"self": "/racing/dates/2026-11-05/meetings/G/SAP/races/2"}}]},
    {"meetingName": "FLEMINGTON", "location": "VIC", "raceType": "R", "races": [{"raceNumber": 1, "_links": {"self": "/x"}}]},
    {"meetingName": "WENTWORTH PARK", "location": "NSW", "raceType": "G", "races": [{"raceNumber": 1, "_links": {"self": "/y"}}]}]}
RACE1 = {"raceStartTime": "2026-11-05T08:00:00.000Z", "runners": [
    {"runnerNumber": 1, "runnerName": "KIWI EVOCA", "fixedOdds": {"returnWin": 1.45, "returnWinOpen": 1.95, "returnWinOpenDaily": 1.95,
     "bettingStatus": "Open", "flucs": [{"returnWin": 1.55, "returnWinTime": "2026-11-04T20:16:00Z"}, {"returnWin": 1.50, "returnWinTime": "2026-11-04T20:18:00Z"}]}},
    {"runnerNumber": 2, "runnerName": "GONE", "fixedOdds": {"bettingStatus": "Scratched"}}]}
RACE2 = {"runners": [{"runnerNumber": 3, "runnerName": "NO PRICES YET", "fixedOdds": {"bettingStatus": "NotOpen"}}]}


def test_collect_follows_links_and_reads_the_open(tmp_path):
    s = Session({f"{TA.BASE}/racing/dates/2026-11-05/meetings": Resp(200, MEETINGS),
                 f"{TA.BASE}/racing/dates/2026-11-05/meetings/G/SAP/races/1?jurisdiction=VIC": Resp(200, RACE1),
                 f"{TA.BASE}/racing/dates/2026-11-05/meetings/G/SAP/races/2": Resp(200, RACE2)})
    c = TA.TabClient(session=s)
    rows, fixed, runner, n = TA.collect(c, "2026-11-05")
    assert n == 2 and len(rows) == 3 and c.calls == 3                      # the gallops and the NSW dogs are not read
    assert s.asked[0][1] == {"jurisdiction": "VIC"} and s.asked[2][1] == {"jurisdiction": "VIC"} and s.asked[1][1] == {}
    r = rows[0]
    assert (r["venue"], r["race"], r["runner"], r["open"], r["open_daily"], r["current"], r["flucs"]) == ("SANDOWN PARK", 1, 1, 1.95, 1.95, 1.45, 2)
    assert r["first_fluc_at"] == "2026-11-04T20:16:00Z" and r["last_fluc_at"] == "2026-11-04T20:18:00Z" and r["scratched"] is False
    assert rows[1]["scratched"] is True and rows[1]["open"] is None and rows[2]["status"] == "NotOpen"
    assert "returnWinOpen" in fixed and "runnerName" in runner
    assert TA.record(c, "2026-11-05", "VIC", tmp_path) == 0
    with open(tmp_path / "tab-opens-2026-11-05.csv", newline="") as f:
        got = list(csv.DictReader(f))
    assert len(got) == 3 and got[0]["open"] == "1.95" and got[2]["open"] == ""


def test_probe_prints_names_and_a_table(capsys):
    s = Session({f"{TA.BASE}/racing/dates/2026-11-05/meetings": Resp(200, MEETINGS),
                 f"{TA.BASE}/racing/dates/2026-11-05/meetings/G/SAP/races/1?jurisdiction=VIC": Resp(200, RACE1),
                 f"{TA.BASE}/racing/dates/2026-11-05/meetings/G/SAP/races/2": Resp(200, RACE2)})
    assert TA.probe(TA.TabClient(session=s), "2026-11-05", "VIC") == 0
    out = capsys.readouterr().out
    assert "1 Victorian greyhound meetings: SANDOWN PARK" in out
    assert "fixedOdds fields: bettingStatus, flucs, returnWin, returnWinOpen, returnWinOpenDaily" in out
    assert "| SANDOWN PARK | 1 | 1 | Open | 1.95 | 1.95 | 1.45 | 2 |" in out
