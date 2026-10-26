import pytest

from afl.live import team_sheet as TS

SHEET = """
# a comment line
Game: Adelaide v Fremantle, Adelaide Oval, 2027-03-20, round 2
Adelaide
B: A1, A2, A3
HB: A4, A5, A6
C: A7, A8, A9
HF: A10, A11, A12
F: A13, A14, A15
FOL: A16, A17, A18
I/C: A19, A20, A21, A22
SUB: A23
EMG: E1, E2
Fremantle
B: F1, F2, F3
int: F4
"""


def test_parse_positions_and_sub():
    df = TS.parse(SHEET, 2027)
    a = df[df.team == 'Adelaide'].set_index('player')
    assert len(a) == 23 and 'E1' not in a.index                  # emergencies are not playing
    assert a.named_pos['A8'] == 'centre' and a.named_pos['A7'] == 'wing'
    assert a.named_pos['A16'] == 'ruck' and a.named_pos['A17'] == 'centre'
    assert a.named_pos['A19'] == 'bench'
    assert a['sub']['A23'] == 1 and a['sub']['A1'] == 0          # sub named: everyone else known not to be
    f = df[df.team == 'Fremantle']
    assert (f['sub'] == '').all()                                 # no sub named yet: unknown, left blank
    assert set(df.home_team) == {'Adelaide'} and set(df.venue) == {'Adelaide Oval'} and set(df['round']) == {'2'}
    assert TS.check(df) == ['Fremantle on 2027-03-20: 4 players named (expected 22; 23 only in a season with a substitute)']


def test_season_comes_from_the_game_date_not_other_text():
    df = TS.parse('# notes about 2026\n' + SHEET)
    assert set(df.season) == {2027}


def test_refuses_lines_before_a_game():
    with pytest.raises(ValueError):
        TS.parse('B: X, Y\n', 2027)
