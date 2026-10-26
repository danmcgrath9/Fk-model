"""The in-season pieces: merging recently added matches, and the pricing window."""
import datetime as dt

import pandas as pd

from bbl.data import refresh
from bbl.live import log


def test_merge_replaces_revised_matches_in_every_table():
    held = pd.DataFrame(dict(match_id=['a', 'a', 'b'], v=[1, 2, 3]))
    new = pd.DataFrame(dict(match_id=['b', 'c'], v=[30, 40]))
    out, n = refresh.merge(held, new, {'b', 'c'})
    assert sorted(zip(out.match_id, out.v)) == [('a', 1), ('a', 2), ('b', 30), ('c', 40)]
    # a revised match with no rows in this table loses its stale ones
    out2, _ = refresh.merge(held, pd.DataFrame(columns=['match_id', 'v']), {'b'})
    assert sorted(out2.match_id) == ['a', 'a']


def test_pick_takes_the_link_from_the_page():
    html = '<a href="/downloads/recently_added_2_json.zip">2</a> <a href="/downloads/recently_added_7_json.zip">7</a>'
    assert refresh.pick(html) == 'https://cricsheet.org/downloads/recently_added_7_json.zip'


def test_window_prices_only_unplayed_games_in_the_next_days():
    f = pd.DataFrame(dict(date=['2026-10-28', '2026-10-29', '2026-10-31', '2026-11-05'], cricinfo_id=['1', '2', '3', '4'],
                          team1='A', team2='B', venue='V', gender='female', comp='WBBL'))
    w = log.window(f, held_ids={'2'}, days=3, today=dt.date(2026, 10, 29))
    assert list(w.cricinfo_id) == ['3']          # 28th is past, 2 is already played, 5 Nov is outside the window
