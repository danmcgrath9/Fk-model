"""Team model: win chance (head-to-head) and runs totals, at the open and with teams named.

Walk-forward and out of sample: every BBL or WBBL season is predicted by a model fitted only on
club T20 games (same gender) that started before that season's first game. A BBL season is ~44
games, too few to fit on alone; the IPL, Blast, PSL and the rest carry the fitting.

Choices (feature set, model type, spreads) are made on the 'choose' seasons only (2022/23, 2023/24),
reported on 'confirm' (2024/25), and the 'final' season (2025/26) is scored once, at the end, with
FINAL=1. 'fit' seasons are reported for reference only: the walk-forward never trains on its own season.

Markets priced:
  head-to-head   P(team wins), ties and no results excluded (books' rules on a tie vary: dead heat or super over)
  first innings  runs scored by the side batting first, a full 20 overs or all out, no rain rule
  match runs     both innings, same condition on the first innings and no rain rule
A runs line (handicap) is not priced: a chase stops when it wins, so a runs margin only exists for the
side batting first, and Australian books offer cricket lines rarely. Revisit if the odds probe finds them.

Usage: python -m bbl.model.team bbl/cache/parquet   (writes TEAM.md and team_preds.parquet)
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

EVAL_SEASONS = ['2018/19', '2019/20', '2020/21', '2021/22', '2022/23', '2023/24', '2024/25', '2025/26']
CHOOSE = ['2022/23', '2023/24']
CONFIRM = ['2024/25']
FINAL = ['2025/26']

# Chosen on 2022/23-2023/24 (docs/TEAM_STEP3.md has the sweeps): the rating and how often the side has played
# at the ground. Lineup strength, the toss, and who is in or out since last game all scored at or below this
# on the choose seasons, so 'teams named' uses the same inputs for win chance; the XI still feeds totals and props.
SIDE_OPEN = ['elo_pre', 'venue_share']
SIDE_NAMED = ['elo_pre', 'venue_share']
WIN_EXTRA_NAMED = []
# After the toss (bbl/docs/RESEARCH.md section 8): who chases, and chasing at night, chosen on 2022/23-2023/24
# for BBL (0.0615 -> 0.0695 bits; 2024/25 -0.020 -> +0.009). Not for WBBL, where both made it worse.
WIN_AFTER_TOSS = {'BBL': ['chase', 'chase_night'], 'WBBL': []}
WIN_C = 0.1
# every side feature the win and totals models can use, carried for the opponent too
PAIR_COLS = ['elo_pre', 'venue_share', 'n_outs', 'outs_runs', 'n_ins', 'ins_runs'] + [
    f'{c}_{v}' for c in ('xi_runs', 'xi_sixes', 'xi_econ', 'xi_wkts', 'xi_debutants') for v in ('open', 'named')]
# first-innings runs: BBL is best priced off the ground's own running average; WBBL off the full ridge model
TOTALS_KIND = {('first_inns_runs', 'BBL'): 'venue', ('first_inns_runs', 'WBBL'): 'model',
               ('match_runs', 'BBL'): 'model', ('match_runs', 'WBBL'): 'model'}
TOTALS_ALPHA = 1.0


def pairs(t):
    """Each team-game with its opponent's side features attached as opp_<feature>."""
    cols = PAIR_COLS
    o = t[['match_id', 'team_key'] + cols].rename(columns={'team_key': 'opp_key', **{c: 'o_' + c for c in cols}})
    x = t.drop(columns=[c for c in t.columns if c.startswith('opp_') and c != 'opp_key']).merge(o, on=['match_id', 'opp_key'])
    for c in cols:
        x['d_' + c] = x[c] - x['o_' + c]
    x['bat_first_x_venue'] = (x.batted_first - 0.5) * (x.venue_bat_first_win.fillna(0.5) - 0.5) * 4
    return x


def add_toss_context(x, d):
    """Who chases (+0.5) or sets (-0.5), and chasing at night (start 5:30pm or later, from match_context.parquet).
    Only for the 'after the toss' price: before it, nobody knows who chases."""
    path = os.path.join(d, 'match_context.parquet')
    ctx = pd.read_parquet(path, columns=['match_id', 'start_hour']) if os.path.exists(path) else pd.DataFrame(columns=['match_id', 'start_hour'])
    x = x.drop(columns=[c for c in ('start_hour',) if c in x]).merge(ctx, on='match_id', how='left')
    x['chase'] = 0.5 - x.batted_first
    night = (x.start_hour >= 17.5).astype(float).where(x.start_hour.notna())
    x['chase_night'] = x.chase * night.fillna(night.mean() if night.notna().any() else 0.5)
    return x


def win_features(version, comp=None):
    side = SIDE_OPEN if version == 'open' else SIDE_NAMED
    feats = ['d_' + c for c in side]
    if version == 'named':
        feats += WIN_EXTRA_NAMED
    if version == 'after_toss':
        feats += WIN_AFTER_TOSS.get(comp, [])
    return feats


def season_start(t, season, comps=('BBL', 'WBBL'), gender=None):
    s = t[(t.season == season) & t.comp.isin(comps)]
    if gender:
        s = s[s.gender == gender]
    return s.dt.min()


def _fill(X, med):
    return X.fillna(med)


def fit_predict_win(x, version, kind='logit'):
    """Walk-forward win chances for every BBL/WBBL team-game in EVAL_SEASONS."""
    club = x[(x.team_type == 'club') & x.won.isin([0.0, 1.0])] if 'team_type' in x else x[x.won.isin([0.0, 1.0])]
    out = []
    for gender, comp in (('male', 'BBL'), ('female', 'WBBL')):
        feats = win_features(version, comp)
        for season in EVAL_SEASONS:
            test = x[(x.comp == comp) & (x.season == season)]
            if test.empty:
                continue
            start = test.dt.min()
            train = club[(club.gender == gender) & (club.dt < start)]
            med = train[feats].median()
            if kind == 'elo':
                p = 1 / (1 + 10 ** (-test.d_elo_pre / 400))
            else:
                mdl = make_pipeline(StandardScaler(), LogisticRegression(C=WIN_C, max_iter=1000))
                mdl.fit(_fill(train[feats], med), train.won.astype(int))
                p = mdl.predict_proba(_fill(test[feats], med))[:, 1]
            out.append(test[['match_id', 'team_key', 'opp_key', 'season', 'comp', 'won']].assign(p_raw=p))
    r = pd.concat(out)
    # symmetric: a game's two rows must add to one
    o = r[['match_id', 'team_key', 'p_raw']].rename(columns={'team_key': 'opp_key', 'p_raw': 'p_opp'})
    r = r.merge(o, on=['match_id', 'opp_key'])
    r['p'] = (r.p_raw + 1 - r.p_opp) / 2
    return r.drop(columns=['p_raw', 'p_opp'])


def win_scores(r):
    g = r[r.won.isin([0.0, 1.0])]
    p = g.p.clip(1e-6, 1 - 1e-6)
    return pd.Series(dict(games=len(g) // 2, logloss=float(-(g.won * np.log(p) + (1 - g.won) * np.log(1 - p)).mean()),
                          brier=float(((p - g.won) ** 2).mean()), tips=float(((p > 0.5) == (g.won == 1)).mean()),
                          bits=float((1 + np.log2(np.where(g.won == 1, p, 1 - p))).mean())))


# ---------------------------------------------------------------- totals

TOT_BAT = ['xi_runs', 'xi_sixes', 'elo_pre']
TOT_BOWL = ['xi_econ', 'xi_wkts', 'elo_pre']


def totals_frame(x, version):
    """One row per game: the side batting first and the side bowling first, and the targets."""
    sfx = '_' + version
    bf = x[x.batted_first == 1].copy()
    f = {}
    for c in TOT_BAT:
        col = c if c == 'elo_pre' else c + sfx
        f['bat_' + c] = bf[col]
        f['bowl_' + c] = bf['o_' + col]
    for c in TOT_BOWL:
        col = c if c == 'elo_pre' else c + sfx
        f['bowlside_' + c] = bf['o_' + col]
        f['batside_' + c] = bf[col]
    d = pd.DataFrame(f, index=bf.index)
    d = d.loc[:, ~d.columns.duplicated()]
    d['venue_first_runs'] = bf.venue_first_runs
    keep = ['match_id', 'season', 'comp', 'gender', 'dt', 'team_type', 'first_inns_runs', 'match_runs', 'full_first_inns',
            'method', 'result', 'team_key', 'opp_key', 'venue_c']
    return pd.concat([bf[[k for k in keep if k in bf]], d], axis=1)


def totals_features(tf):
    return [c for c in tf.columns if c.startswith(('bat_', 'bowl_', 'bowlside_', 'batside_'))] + ['venue_first_runs']


def swap_sides(tf):
    """The same game with the other side batting first: what 'at the open' must allow for (toss unknown)."""
    s = tf.copy()
    pairs_ = [('bat_xi_runs', 'bowl_xi_runs'), ('bat_xi_sixes', 'bowl_xi_sixes'), ('bat_elo_pre', 'bowl_elo_pre'),
              ('bowlside_xi_econ', 'batside_xi_econ'), ('bowlside_xi_wkts', 'batside_xi_wkts')]
    for a, b in pairs_:
        if a in s and b in s:
            s[a], s[b] = tf[b].to_numpy(), tf[a].to_numpy()
    return s


def fit_predict_totals(x, version, target):
    tf = totals_frame(x, version)
    feats = totals_features(tf)
    ok = tf.full_first_inns & tf.method.isna() & (tf.result != 'no result')
    if target == 'match_runs':
        ok &= tf.match_runs.notna()
    club = tf[ok & (tf.team_type == 'club')]
    out = []
    for gender, comp in (('male', 'BBL'), ('female', 'WBBL')):
        for season in EVAL_SEASONS:
            test = tf[(tf.comp == comp) & (tf.season == season) & ok]
            if test.empty:
                continue
            train = club[(club.gender == gender) & (club.dt < test.dt.min())]
            med = train[feats].median()
            recent = train[train.dt >= train.dt.max() - pd.Timedelta(days=3 * 365)]
            if TOTALS_KIND[(target, comp)] == 'venue':
                # the ground's running average of full first innings, games before this one only (frame.venue_features)
                same = train[train.comp == comp]
                mu = test.venue_first_runs.fillna(same[target].mean()).to_numpy()
                r_same = same[same.dt >= same.dt.max() - pd.Timedelta(days=3 * 365)]
                sd = float(np.std(r_same[target] - r_same.venue_first_runs.fillna(same[target].mean())))
            else:
                mdl = make_pipeline(StandardScaler(), Ridge(alpha=TOTALS_ALPHA))
                mdl.fit(_fill(train[feats], med), train[target])
                mu = mdl.predict(_fill(test[feats], med))
                if version == 'open':     # who bats first is not known at the open: average the two orders
                    mu = (mu + mdl.predict(_fill(swap_sides(test)[feats], med))) / 2
                # spread: residual sd over the last three seasons of the training data (fit-side only)
                sd = float(np.std(recent[target] - mdl.predict(_fill(recent[feats], med))))
            out.append(test[['match_id', 'season', 'comp', target, 'venue_first_runs']].assign(mu=mu, sd=sd))
    return pd.concat(out)


def totals_scores(r, target):
    y = r[target]
    z = (y - r.mu) / r.sd
    crps = r.sd * (z * (2 * stats.norm.cdf(z) - 1) + 2 * stats.norm.pdf(z) - 1 / np.sqrt(np.pi))
    base = r.venue_first_runs if target == 'first_inns_runs' else None
    s = dict(games=len(r), mae=float((y - r.mu).abs().mean()), crps=float(crps.mean()), sd=float(r.sd.mean()),
             within_1sd=float((z.abs() <= 1).mean()))
    if base is not None:
        s['mae_venue_avg'] = float((y - base.fillna(base.mean())).abs().mean())
    return pd.Series(s)


def p_over(mu, sd, line):
    """P(total > line) for a .5 line from the normal; integers: continuity at the half run."""
    return 1 - stats.norm.cdf((np.floor(line) + 0.5 - mu) / sd)


def GROUPS():
    g = [('choose 22/23-23/24', CHOOSE), ('confirm 24/25', CONFIRM), ('fit-era 18/19-21/22', EVAL_SEASONS[:4])]
    return g + ([('FINAL 25/26', FINAL)] if os.environ.get('FINAL') == '1' else [])


def md(df):
    cols = list(df.columns)
    out = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for r in df.itertuples(index=False):
        out.append('| ' + ' | '.join(f'{v:.3f}' if isinstance(v, float) else str(v) for v in r) + ' |')
    return '\n'.join(out)


def report(d):
    t = pd.read_parquet(os.path.join(d, 'team_frame.parquet'))
    m = pd.read_parquet(os.path.join(d, 't20_matches.parquet'), columns=['match_id', 'team_type'])
    t = t.merge(m, on='match_id')
    x = add_toss_context(pairs(t), d)
    lines = ['# BBL team model', '',
             'Walk-forward: each season predicted by a model fitted on club T20 games of the same gender that started '
             'before it. Choices made on 2022/23 and 2023/24 only; 2024/25 confirms; 2025/26 '
             + ('is scored below (FINAL=1).' if os.environ.get('FINAL') == '1' else 'is held back, untouched.'), '']
    preds = []
    for comp in ('BBL', 'WBBL'):
        lines += [f'## {comp}: head-to-head', '', 'bits: 1 + log2(chance given to the winner), averaged; 0 is a coin flip, higher is better.', '']
        rows = []
        for name, kind, version in (('rating only (Elo)', 'elo', 'open'), ('at the open', 'logit', 'open'),
                                    ('teams named', 'logit', 'named'), ('after the toss', 'logit', 'after_toss')):
            r = fit_predict_win(x, version, kind)
            r = r[r.comp == comp]
            if kind == 'logit':
                preds.append(r.assign(model='win_' + version))
            for group, seasons in GROUPS():
                s = win_scores(r[r.season.isin(seasons)])
                rows.append(dict(seasons=group, model=name, **s.to_dict()))
        lines += [md(pd.DataFrame(rows).sort_values(['seasons', 'model'])), '']
        for target, label in (('first_inns_runs', 'first-innings runs'), ('match_runs', 'match runs')):
            rows = []
            for version in ('open', 'named'):
                r = fit_predict_totals(x, version, target)
                r = r[r.comp == comp]
                preds.append(r.assign(model=f'{target}_{version}'))
                for group, seasons in GROUPS():
                    s = totals_scores(r[r.season.isin(seasons)], target)
                    rows.append(dict(seasons=group, model='at the open' if version == 'open' else 'teams named', **s.to_dict()))
            lines += [f'## {comp}: {label}', '', 'Full first innings, no rain rule. crps: the miss of the whole distribution in runs (lower is better).', '',
                      md(pd.DataFrame(rows).sort_values(['seasons', 'model'])), '']
    text = '\n'.join(lines)
    p = pd.concat(preds, ignore_index=True)
    if os.environ.get('FINAL') != '1':
        p = p[~p.season.isin(FINAL)]
    p.to_parquet(os.path.join(d, 'team_preds.parquet'), index=False)
    open(os.path.join(d, 'TEAM.md'), 'w').write(text)
    print(text)


if __name__ == '__main__':
    report(sys.argv[1])
