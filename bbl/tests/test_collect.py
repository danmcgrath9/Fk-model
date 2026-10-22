"""The collectors' parsing and checks, on made-up inputs: no network."""
import numpy as np
import pandas as pd

from bbl.collect import coords, parse_wiki

PAGE = """intro {{Single-innings cricket match
| date = 14 December 2025
| time = 19:15
| daynight = y
| team1 = [[Sydney Sixers]] (H)
| team2 = [[Perth Scorchers (WBBL)|Perth Scorchers]]
| venue = [[Perth Stadium]], [[Perth]]<br/>Attendance: 26,823<ref name="x" />
| toss = Perth Scorchers won the toss and elected to field.
| report = [https://www.espncricinfo.com/ci/engine/match/1493238.html Scorecard]
| result = Perth Scorchers won by 5 wickets
| round = {{anchor|match1}} '''Match 1'''
}} text {{Limited overs matches | date = {{anchor|match2}} 20 December | time = 19:40 | team1 = [[A]] | team2 = [[B]]
| report = [http://www.espncricinfo.com/series/8044/game/1152511/x Scorecard] | venue = [[Docklands Stadium]]
}}"""


def test_template_parsing():
    b = parse_wiki.blocks(PAGE)
    assert len(b) == 2
    p = parse_wiki.params(b[0])
    assert p['team2'] == '[[Perth Scorchers (WBBL)|Perth Scorchers]]'      # pipe inside a link is not a separator
    name, home = parse_wiki.team(p['team1'])
    assert (name, home) == ('Sydney Sixers', True)
    assert parse_wiki.team(p['team2']) == ('Perth Scorchers', False)
    # an old page leaves the year off: December is the season's first year, January its second
    assert parse_wiki.parse_date('20 December', (2013, 2014)) == '2013-12-20'
    assert parse_wiki.parse_date('5 January', (2013, 2014)) == '2014-01-05'


def test_ground_check_refuses_wrong_continents():
    df = pd.DataFrame([dict(venue='Brisbane Cricket Ground', title='The Gabba', lat=-27.49, lon=153.04),
                       dict(venue='Eastern Oval, Ballarat', title='The Oval', lat=51.48, lon=-0.115),
                       dict(venue='M. A. Chidambaram Stadium, Chennai', title='M. A. Chidambaram Stadium', lat=13.06, lon=80.28),
                       dict(venue='Somewhere', title=None, lat=None, lon=None)])
    bad = coords.check(df)
    assert list(bad.venue) == ['Eastern Oval, Ballarat', 'Somewhere']


def test_every_known_bbl_ground_name_maps_to_an_article():
    for v in ['Brisbane Cricket Ground, Woolloongabba, Brisbane', 'W.A.C.A. Ground', 'Ninja Stadium, Hobart', 'Perth Stadium']:
        assert coords.TITLES.get(coords.head(v))
    assert coords.TITLES[coords.head('Brisbane Cricket Ground, Woolloongabba')] == 'The Gabba'   # not the SCG


def test_time_zones_and_utc_start():
    from bbl.collect import weather_join as w
    assert w.zone(-27.49, 153.04) == 'Australia/Brisbane'      # Gabba: no daylight saving
    assert w.zone(-31.96, 115.88) == 'Australia/Perth'
    assert w.zone(-34.92, 138.60) == 'Australia/Adelaide'
    assert w.zone(-42.88, 147.37) == 'Australia/Hobart'
    assert w.zone(-37.82, 144.98) == 'Australia/Sydney'        # Melbourne keeps Sydney's clock
    assert w.zone(-23.71, 133.88) == 'Australia/Darwin'        # Alice Springs
    assert w.zone(13.06, 80.28) == 'Asia/Kolkata'              # Chennai
    # 7:15pm on 14 Dec 2025 in Perth (UTC+8) is 11:15 UTC; at the Gabba (UTC+10, no DST) 09:15; at the MCG (DST, +11) 08:15
    assert str(w.start_utc('2025-12-14', '19:15', 'Australia/Perth')) == '2025-12-14 11:15:00+00:00'
    assert str(w.start_utc('2025-12-14', '19:15', 'Australia/Brisbane')) == '2025-12-14 09:15:00+00:00'
    assert str(w.start_utc('2025-12-14', '19:15', 'Australia/Sydney')) == '2025-12-14 08:15:00+00:00'
    assert w.start_utc('2025-12-14', None, 'Australia/Sydney') is None


def test_power_files_read_by_utc_hour(tmp_path):
    import json
    from bbl.collect import weather_join as w
    body = {'properties': {'parameter': {'T2M': {'2025121408': 24.0, '2025121409': 22.5}, 'T2MDEW': {'2025121408': 12.0, '2025121409': -999.0},
                                         'RH2M': {'2025121408': 50.0, '2025121409': 55.0}, 'PRECTOTCORR': {'2025121408': 0.0, '2025121409': 0.4},
                                         'WS2M': {'2025121408': 3.0, '2025121409': 2.0}}}}
    (tmp_path / '-37.8200_144.9833_2025.json').write_text(json.dumps(body))
    wx = w.load_power(str(tmp_path))
    s = wx[(-37.82, 144.9833)]
    assert s.loc['2025-12-14 08:00+00:00', 'T2M'] == 24.0
    assert np.isnan(s.loc['2025-12-14 09:00+00:00', 'T2MDEW'])   # -999 is missing, not a dew point
