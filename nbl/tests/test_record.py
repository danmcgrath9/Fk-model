"""When the line recorder calls, and when it holds back (no network)."""
import pandas as pd

from nbl.lines import record

NOW = pd.Timestamp('2026-10-23 06:00', tz='UTC')


def ev(i, hours):
    return dict(id=i, commence_time=(NOW + pd.Timedelta(hours=hours)).isoformat())


def led(rows):
    d = pd.DataFrame(rows, columns=record.LEDGER_COLS)
    d['at'] = pd.to_datetime(d['at'], utc=True)
    return d


def test_first_run_takes_team_markets_and_props_only_for_games_inside_the_window():
    calls = record.plan([ev('a', 5), ev('b', 50)], led([]), NOW)
    assert ('team', None) in calls
    assert ('props', 'a') in calls and ('props', 'b') not in calls


def test_recent_pulls_are_not_repeated():
    l = led([(NOW - pd.Timedelta(hours=1), 'team', None, 3, 200), (NOW - pd.Timedelta(hours=1), 'props', 'a', 5, 200)])
    assert record.plan([ev('a', 5)], l, NOW) == []


def test_the_close_is_taken_once_inside_the_last_forty_minutes():
    l = led([(NOW - pd.Timedelta(hours=1), 'team', None, 3, 200), (NOW - pd.Timedelta(hours=1), 'props', 'a', 5, 200)])
    calls = record.plan([ev('a', 0.5)], l, NOW)
    assert ('team', None) in calls and ('props', 'a') in calls
    l2 = led([(NOW - pd.Timedelta(minutes=10), 'team', None, 3, 200), (NOW - pd.Timedelta(minutes=10), 'props', 'a', 5, 200)])
    assert record.plan([ev('a', 0.4)], l2, NOW) == []


def test_failed_calls_do_not_count_as_taken():
    l = led([(NOW - pd.Timedelta(minutes=5), 'team', None, 0, 500)])
    assert ('team', None) in record.plan([ev('a', 10)], l, NOW)


def test_no_games_no_calls():
    assert record.plan([ev('old', -3)], led([]), NOW) == []


def test_half_time_snapshot_once_between_40_and_80_minutes_after_the_tip():
    l = led([])
    calls = record.plan([ev('live', -55 / 60)], l, NOW)
    assert ('half', 'live') in calls
    assert ('half', 'live') not in record.plan([ev('live', -20 / 60)], l, NOW)        # too early
    done = led([(NOW - pd.Timedelta(minutes=10), 'half', 'live', 2, 200)])
    assert ('half', 'live') not in record.plan([ev('live', -65 / 60)], done, NOW)     # already taken
