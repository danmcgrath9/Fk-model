"""A past round priced as if unplayed must get the same features the history gives it: proof that the live path uses
only what was known before the bounce, and that it builds the same inputs the models were trained on."""
import os

import numpy as np
import pandas as pd
import pytest

from afl.live.price_round import build_live
from afl.model import frame as F

CACHE = 'afl/cache'
# features that average over the whole league's recent games: a later game in the round legitimately sees the earlier
# games of that round in the history and not when they are unplayed, so these are checked on the round's first game only
LEAGUE = {'league_game_D', 'venue_rel', 'opp_conc_rel'}


@pytest.mark.skipif(not os.path.exists(f'{CACHE}/afltables.parquet'), reason='needs afl/cache')
def test_unplayed_round_gets_the_same_features():
    at = pd.read_parquet(f'{CACHE}/afltables.parquet')
    fw = pd.read_parquet(f'{CACHE}/footywire.parquet')
    base = F.base_table(at, fw)
    base = base[base.season >= 2024]
    rnd = base[(base.season == 2026) & (base.Round.astype(str) == '20')]
    start, end = rnd.dt.min(), rnd.dt.max()
    known = F.add_features(base[base.dt <= end])
    hist = base[base.dt < start]
    named = pd.DataFrame({'season': rnd.season, 'round': rnd.Round, 'date': rnd.date, 'venue': rnd.venue,
                          'home_team': np.where(rnd.is_home == 1, rnd.team, rnd.opp),
                          'away_team': np.where(rnd.is_home == 1, rnd.opp, rnd.team),
                          'team': rnd.team, 'player': rnd.Player, 'sub': rnd.named_sub, 'player_id': rnd.player_id})
    live, games, problems = build_live(hist, named)
    assert problems == []
    assert games == set(rnd.game)
    a = known[known.game.isin(games)].set_index(['game', 'player_id']).sort_index()
    b = live[live.game.isin(games)].set_index(['game', 'player_id']).sort_index()
    assert len(a) == len(b) == len(rnd)
    first = a.reset_index().sort_values('dt').game.iloc[0]
    for c in F.FEATURES:
        if c == 'age':      # carried forward from his last game; a debutant has none (and is never priced)
            k = b[c].notna()
            assert k.sum() >= len(b) - 10 and np.allclose(a[c][k], b[c][k], atol=0.01), c
            continue
        x, y = (a.loc[first, c], b.loc[first, c]) if c in LEAGUE else (a[c], b[c])
        assert np.allclose(x.astype(float), y.astype(float), equal_nan=True), c
