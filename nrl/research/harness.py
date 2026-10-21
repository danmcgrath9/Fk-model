"""Score a team-model variant on DEV and CONFIRM against the current model, the same way every time.

A variant is a function that takes the team-games table (one row per game, home view) and returns it with
extra columns, plus the feature lists to use. Fitted on FIT (2003-2018) like the live model.
"""
import numpy as np
import pandas as pd

from nrl.model import team


def score_variant(g, margin_feats, total_feats=None, label=''):
    total_feats = total_feats or team.TOTAL_FEATURES
    fit = g[g.season.isin(team.FIT)]
    mm = team.LinearT().fit(fit[margin_feats].to_numpy(), fit.margin.to_numpy())
    tm = team.LinearT().fit(fit[total_feats].to_numpy(), fit.total.to_numpy())
    rows = []
    for lab, ss in (('dev', team.DEV), ('confirm', team.CONFIRM)):
        t = g[g.season.isin(ss)]
        X, Xt = t[margin_feats].to_numpy(), t[total_feats].to_numpy()
        r = team.score(team.win_prob(mm, X), t.margin.to_numpy())
        rows.append(dict(variant=label, set=lab, bits=r['bits'], logloss=r['logloss'],
                         mae_margin=np.abs(mm.mean(X) - t.margin).mean(), mae_total=np.abs(tm.mean(Xt) - t.total).mean()))
    return pd.DataFrame(rows), mm, tm
