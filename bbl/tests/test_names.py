from bbl.live import names

POOL = ['SPD Smith', 'DA Warner', 'Rashid Khan', 'MR Marsh', 'SE Marsh', 'Q de Kock', 'AJ Turner']


def test_initial_and_surname():
    assert names.match('Steve Smith', POOL, manual={}) == ('SPD Smith', 'initial+surname')
    assert names.match('Quinton de Kock', POOL, manual={}) == ('Q de Kock', 'initial+surname')
    assert names.match('Rashid Khan', POOL, manual={}) == ('Rashid Khan', 'exact')


def test_never_guesses():
    who, how = names.match('Marsh', POOL, manual={})
    assert who is None and how.startswith('ambiguous')
    assert names.match('Mitchell Marsh', POOL, manual={}) == ('MR Marsh', 'initial+surname')
    assert names.match('Glenn Maxwell', POOL, manual={})[0] is None


def test_override_wins():
    assert names.match('Mitch Marsh', POOL, team='Perth Scorchers', manual={('Perth Scorchers', 'mitch marsh'): 'MR Marsh'}) == ('MR Marsh', 'override')
