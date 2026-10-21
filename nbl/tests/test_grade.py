"""Grading a saved sheet against results (no cache needed)."""
import numpy as np
import pandas as pd

from nbl.model import grade

TIP = pd.Timestamp('2026-10-21 08:30', tz='UTC')


def _sheet():
    base = dict(game='g1', tip=TIP, home='H', away='A', priced_at=TIP - pd.Timedelta(hours=3), team=np.nan, player=np.nan)
    rows = [dict(base, kind='team', market='h2h', side='home', line=np.nan, p=0.7, mu=6.0),
            dict(base, kind='team', market='line', side='home', line=-5.0, p=0.55, mu=6.0),
            dict(base, kind='team', market='line', side='home', line=-4.0, p=0.6, mu=6.0),
            dict(base, kind='team', market='total', side='over', line=180.5, p=0.5, mu=181.0),
            dict(base, kind='prop', market='pts', side='over', line=14.5, p=0.6, mu=16.0, team='H', player='Jo Smith'),
            dict(base, kind='prop', market='pts', side='over', line=4.5, p=0.4, mu=4.0, team='H', player='Al Bench'),
            # a sheet priced after the tip is never graded
            dict(base, kind='team', market='h2h', side='home', line=np.nan, p=0.99, mu=30.0, priced_at=TIP + pd.Timedelta(hours=1))]
    return pd.DataFrame(rows)


def test_outcomes_and_voids():
    games = pd.DataFrame([dict(game='g1', home_score=90.0, away_score=86.0, scheduled=False)])
    players = pd.DataFrame([dict(game='g1', player='Jo Smith', played=1.0, pts=20.0, reb=0, ast=0, fg3m=0, pra=20.0),
                            dict(game='g1', player='Al Bench', played=0.0, pts=0.0, reb=0, ast=0, fg3m=0, pra=0.0)])
    sh = _sheet()
    sh = sh[sh.priced_at < sh.tip]
    s = grade.outcomes(sh, games, players).reset_index(drop=True)
    y = dict(zip(zip(s.market, s.line.fillna(0)), s.y))
    assert y[('h2h', 0)] == 1.0                    # home won by 4
    assert y[('line', -5.0)] == 0.0                # -5 does not cover a 4-point win
    assert np.isnan(y[('line', -4.0)])             # -4 is a push: left out
    assert y[('total', 180.5)] == 0.0              # 176 total
    assert y[('pts', 14.5)] == 1.0                 # 20 points
    assert np.isnan(y[('pts', 4.5)])               # did not take the court: void


def test_last_sheet_before_tip_is_kept(tmp_path):
    sh = _sheet()
    early = sh.copy(); early['priced_at'] = TIP - pd.Timedelta(days=2); early['p'] = 0.1
    early.to_csv(tmp_path / 'prices_2026-10-19.csv', index=False)
    sh.to_csv(tmp_path / 'prices_2026-10-21.csv', index=False)
    s = grade.load_sheets(str(tmp_path))
    assert (s.priced_at == TIP - pd.Timedelta(hours=3)).all()
    assert s[s.market == 'h2h'].p.tolist() == [0.7]
