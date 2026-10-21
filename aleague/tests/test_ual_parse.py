"""Ultimate A-League match page parser, on a saved page (match 2400, Melbourne Victory 0-0 Brisbane
Roar, 12 Apr 2022; content Ultimate A-League, CC BY 4.0)."""
import os

from aleague.data.ual_parse import parse_match

PAGE = os.path.join(os.path.dirname(__file__), 'fixtures', 'ual_match_2400.html')


def test_match_2400():
    r = parse_match(open(PAGE, errors='replace').read(), 2400)
    m = r['match']
    assert (m['home'], m['away'], m['round'], m['season']) == ('Melbourne Victory', 'Brisbane Roar', '7', '2021-22')
    assert (m['home_goals'], m['away_goals'], m['attendance'], m['referee']) == (0, 0, 6127, 'Kurt Ams')
    # four yellow cards: Olsen 32' (away), Marchan 44' and Broxham 83' (home), Holmes 87' (away)
    assert [(e['side'], e['minute'], e['player']) for e in r['events']] == [
        ('away', 32, 'Nick Olsen'), ('home', 44, 'Rai Marchan'), ('home', 83, 'Leigh Broxham'), ('away', 87, 'Jordan Holmes')]
    p = {(x['side'], x['player']): x for x in r['players']}
    # 11 starters and 7 on the bench each side; every side's minutes add to 11 x 90 = 990
    for side in ('home', 'away'):
        rows = [x for x in r['players'] if x['side'] == side]
        assert sum(x['starter'] for x in rows) == 11 and len(rows) == 18
        assert sum(x['minutes'] for x in rows) == 990
    # Marchan came off at 57 and Broxham on at 57: 57 and 33 minutes
    assert p[('home', 'Rai Marchan')]['minutes'] == 57 and p[('home', 'Leigh Broxham')]['minutes'] == 33
    assert p[('away', 'Jordan Holmes')]['gk']
