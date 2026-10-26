"""Ideas from afl/docs/RESEARCH_BEST_MODEL.md that can be tested before any bookmaker prop line exists.

1. The market's view of the game (its margin and win chance, Squiggle's "Punters", 2017 on) as an input beside or in
   place of our Elo margin (research rank 2).
2. Each stat its own memory: exponentially weighted averages with shorter and longer half-lives (rank 6).
3. Substitute risk: how often the player has lately been subbed off or named sub, and how much his time on ground
   swings (rank 3, the cheap half; the full two-stage version is in the doc).
4. A spread that depends on the player: negative binomial spread as a function of the projection and of the player's
   own recent volatility, fitted on 2024 projections and scored on 2025-2026 (rank 7).

Same rules as afl/model/extra_test.py: fit 2013-2023, tune 2024, score 2025-2026 (never seen), paired per player-game;
kept where more than two standard errors better.

Usage: python -m afl.model.research_tests afl/cache afl/docs/RESEARCH_TESTS.md
"""
import json
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import optimize

from afl.model import props as P
from afl.model.disposals import nb_logpmf
from afl.model.extra_test import score
from afl.model.walkforward import STATS, stat_matrix

warnings.filterwarnings('ignore')


def market(m, cache):
    g = pd.read_parquet(f'{cache}/market_games.parquet')[['game', 'home', 'mkt_margin', 'mkt_p']]
    m = m.merge(g, on='game', how='left')
    home = m.team == m.home
    m['mkt_exp_margin'] = np.where(home, m.mkt_margin, -m.mkt_margin)
    m['mkt_win_p'] = np.where(home, m.mkt_p, 1 - m.mkt_p)
    m['mkt_blowout'] = m.mkt_exp_margin.abs()
    # the market's margin where it exists, our rating's where it does not (2013-2016)
    m['best_exp_margin'] = m.mkt_exp_margin.fillna(m.exp_margin)
    return m.drop(columns=['home', 'mkt_margin', 'mkt_p'])


def memory(m, stat):
    """Adopted: afl/model/props.py stat_features now builds these for every stat; kept here so the test reruns."""
    if f'{stat}_ewm2' in m:
        return m
    p = m.groupby('player_id', sort=False)[stat]
    for h in (2, 12, 30):
        m[f'{stat}_ewm{h}'] = p.transform(lambda x, h=h: x.shift(1).ewm(halflife=h, min_periods=1).mean())
    return m


def sub_risk(m):
    p = m.groupby('player_id', sort=False)
    m['subbed_off_rate10'] = p.subbed_off.transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    m['named_sub_rate10'] = p.named_sub.transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    m['TOG_sd10'] = p.TOG.transform(lambda x: x.shift(1).rolling(10, min_periods=3).std())
    m['TOG_min10'] = p.TOG.transform(lambda x: x.shift(1).rolling(10, min_periods=3).min())
    return m


def groups(stat):
    return {
        'market view of the game': ['mkt_exp_margin', 'mkt_win_p', 'mkt_blowout'],
        'market margin in place of ours': ['best_exp_margin'],
        'shorter and longer memory': [f'{stat}_ewm2', f'{stat}_ewm12', f'{stat}_ewm30'],
        'substitute risk': ['subbed_off_rate10', 'named_sub_rate10', 'TOG_sd10', 'TOG_min10'],
    }


def feature_tests(base, cache, rep, keep):
    for stat, label in STATS.items():
        m, feats, _ = stat_matrix(base, cache, stat)
        m = sub_risk(memory(market(m, cache), stat))
        tr, tu, te = m[m.season.between(2013, 2023)], m[m.season == 2024], m[m.season.isin([2025, 2026])]
        ll0, ae0 = score(tr, tu, te, feats, stat)
        rep += [f'### {label.capitalize()}', '', f'Current model: average miss {ae0.mean():.3f}.', '',
                '| tried | log-lik change | average miss change | kept |', '|---|---|---|---|']
        kept = []
        for g, cols in groups(stat).items():
            f = [c for c in feats if not (g == 'market margin in place of ours' and c in ('exp_margin', 'exp_blowout'))] + cols
            ll, ae = score(tr, tu, te, f, stat)
            d, da = ll - ll0, ae - ae0
            se = d.std() / np.sqrt(len(d))
            ok = d.mean() > 2 * se
            if ok:
                kept.append(g)
            rep.append(f'| {g} | {d.mean():+.4f} ± {se:.4f} | {da.mean():+.3f} ± {da.std() / np.sqrt(len(da)):.3f} | {"yes" if ok else "no"} |')
            print(stat, g, f'{d.mean():+.4f} ± {se:.4f}', flush=True)
        keep[stat] = kept
        rep.append('')


def volatility(cache):
    f = pd.read_parquet(f'{cache}/frame.parquet', columns=['game', 'player_id', 'dt', 'D', 'M', 'T', 'G']).sort_values('dt')
    p = f.groupby('player_id', sort=False)
    out = f[['game', 'player_id']].copy()
    for s in 'DMTG':
        sd = p[s].transform(lambda x: x.shift(1).rolling(10, min_periods=5).std())
        mean = p[s].transform(lambda x: x.shift(1).rolling(10, min_periods=5).mean())
        out[f'cv_{s}'] = (sd / mean.replace(0, np.nan)).clip(0, 3)
    return out


def fit_spread_model(y, mu, x):
    """a = exp(c0 + c1 log mu + c2 x), by maximum likelihood."""
    def nll(c):
        a = np.exp(np.clip(c[0] + c[1] * np.log(mu) + c[2] * x, -12, 3))
        return -nb_logpmf(y, mu, a).sum()
    return optimize.minimize(nll, x0=[np.log(0.05), 0.0, 0.0], method='Nelder-Mead', options={'maxiter': 2000}).x


def spread_test(cache, rep):
    wf = pd.read_parquet(f'{cache}/walkforward.parquet').merge(volatility(cache), on=['game', 'player_id'], how='left')
    rep += ['## A spread that depends on the player', '',
            'Spread = exp(c0 + c1 x log projection + c2 x the player\'s own recent volatility (sd / mean of his last 10)), '
            'fitted on 2024\'s out-of-sample projections, scored on 2025-2026 against the spread the walk-forward uses now '
            '(per position for disposals, one spread for the rest).', '',
            '| stat | c1 (projection) | c2 (volatility) | log-lik change | kept |', '|---|---|---|---|---|']
    res = {}
    for s, label in STATS.items():
        d = wf.dropna(subset=[s, f'mu_{s}', f'cv_{s}'])
        tu, te = d[d.season == 2024], d[d.season.isin([2025, 2026])]
        c = fit_spread_model(tu[s].to_numpy(), tu[f'mu_{s}'].to_numpy(), tu[f'cv_{s}'].to_numpy())
        a_new = np.exp(np.clip(c[0] + c[1] * np.log(te[f'mu_{s}']) + c[2] * te[f'cv_{s}'], -12, 3))
        diff = nb_logpmf(te[s].to_numpy(), te[f'mu_{s}'].to_numpy(), a_new.to_numpy()) - \
            nb_logpmf(te[s].to_numpy(), te[f'mu_{s}'].to_numpy(), te[f'a_{s}'].to_numpy())
        se = diff.std() / np.sqrt(len(diff))
        ok = diff.mean() > 2 * se
        res[s] = {'c': c.tolist(), 'kept': bool(ok)}
        rep.append(f'| {label} | {c[1]:+.3f} | {c[2]:+.3f} | {diff.mean():+.4f} ± {se:.4f} | {"yes" if ok else "no"} |')
        print(s, 'spread model', c, f'{diff.mean():+.4f} ± {se:.4f}', flush=True)
    rep.append('')
    return res


def position_test(cache, out_md):
    """The team-sheet position (afl/model/named_position.py). Fryzigg stops at 2025, so: fit 2013-2022, tune 2023,
    score 2024-2025. Appends to the report."""
    from afl.model import named_position as NP
    base = P.team_expected_score(pd.read_parquet(f'{cache}/frame.parquet'))
    rep = ['## The position on the team sheet', '',
           'Named position (centre square, ruck, wing, back, forward, bench, sub) and how often he has lately been named in '
           'the centre square. Fryzigg ends at 2025, so fitted 2013-2022, tuned 2023, scored 2024-2025.', '',
           '| stat | matched | log-lik change | average miss change | kept |', '|---|---|---|---|---|']
    kept = {}
    for stat, label in STATS.items():
        m, feats, _ = stat_matrix(base, cache, stat)
        m = NP.attach(m, cache)
        tr, tu, te = m[m.season.between(2013, 2022)], m[m.season == 2023], m[m.season.isin([2024, 2025])]
        ll0, ae0 = score(tr, tu, te, feats, stat)
        ll, ae = score(tr, tu, te, feats + NP.columns(), stat)
        d, da = ll - ll0, ae - ae0
        se = d.std() / np.sqrt(len(d))
        kept[stat] = bool(d.mean() > 2 * se)
        rep.append(f'| {label} | {te.named_pos.notna().mean():.0%} | {d.mean():+.4f} ± {se:.4f} | {da.mean():+.3f} ± {da.std() / np.sqrt(len(da)):.3f} | {"yes" if kept[stat] else "no"} |')
        print(stat, 'named position', f'{d.mean():+.4f} ± {se:.4f}', flush=True)
    open(out_md, 'a').write('\n'.join(rep) + '\n\n')
    k = json.load(open(f'{cache}/research_kept.json'))
    k['named_position'] = kept
    json.dump(k, open(f'{cache}/research_kept.json', 'w'), indent=1)
    print('\n'.join(rep))


def redistribution_test(cache, out_md):
    """Who inherits the ball when a teammate is out (afl/model/redistribution.py). Appends to the report."""
    from afl.model import redistribution as R
    from afl.model.walkforward import prepare
    base = P.team_expected_score(pd.read_parquet(f'{cache}/frame.parquet'))
    rep = ['## Who inherits the ball when a teammate is out', '',
           'Per stat: the usual output of players missing from last week\'s side, each player\'s share-weighted slice of it, '
           'the same for centre clearances, and his own record in past games when a key midfielder was out. Fitted '
           '2013-2023, tuned 2024, scored 2025-2026.', '',
           '| stat | log-lik change | average miss change | kept |', '|---|---|---|---|']
    kept = {}
    for stat, label in STATS.items():
        m, feats, _ = prepare(base, cache, stat)
        m = R.add(m, stat)
        m = P.eligible(m)
        m = m[m[f'{stat}_l10'].notna()]
        tr, tu, te = m[m.season.between(2013, 2023)], m[m.season == 2024], m[m.season.isin([2025, 2026])]
        ll0, ae0 = score(tr, tu, te, feats, stat)
        ll, ae = score(tr, tu, te, feats + R.columns(stat), stat)
        d, da = ll - ll0, ae - ae0
        se = d.std() / np.sqrt(len(d))
        kept[stat] = bool(d.mean() > 2 * se)
        rep.append(f'| {label} | {d.mean():+.4f} ± {se:.4f} | {da.mean():+.3f} ± {da.std() / np.sqrt(len(da)):.3f} | {"yes" if kept[stat] else "no"} |')
        print(stat, 'redistribution', f'{d.mean():+.4f} ± {se:.4f}', flush=True)
    open(out_md, 'a').write('\n'.join(rep) + '\n\n')
    print('\n'.join(rep))


def ensemble_test(cache, out_md, seeds=(7, 11, 23, 41, 59)):
    """One model against the average of several fitted with different random seeds (rows and columns sampled
    differently each time). Appends to the report."""
    import lightgbm as lgb
    from afl.model.disposals import fit_dispersion
    from afl.model.walkforward import params_for
    base = P.team_expected_score(pd.read_parquet(f'{cache}/frame.parquet'))
    rep = ['## One model or an average of several', '',
           f'The current model against the average of {len(seeds)} fitted with different random seeds. Fitted 2013-2023, '
           'tuned 2024, scored 2025-2026.', '', '| stat | log-lik change | average miss change | kept |', '|---|---|---|---|']
    kept = {}
    for stat, label in STATS.items():
        m, feats, _ = stat_matrix(base, cache, stat)
        tr, tu, te = m[m.season.between(2013, 2023)], m[m.season == 2024], m[m.season.isin([2025, 2026])]
        mus_tu, mus_te = [], []
        for sd in seeds:
            mdl = lgb.LGBMRegressor(objective='poisson', **{**params_for(stat), 'random_state': sd}).fit(
                tr[feats], tr[stat], eval_set=[(tu[feats], tu[stat])], callbacks=[lgb.early_stopping(150, verbose=False)])
            mus_tu.append(mdl.predict(tu[feats]))
            mus_te.append(mdl.predict(te[feats]))
        y_tu, y = tu[stat].to_numpy(), te[stat].to_numpy()
        a1 = max(fit_dispersion(y_tu, mus_tu[0]), 1e-3)
        ak = max(fit_dispersion(y_tu, np.mean(mus_tu, 0)), 1e-3)
        d = nb_logpmf(y, np.mean(mus_te, 0), ak) - nb_logpmf(y, mus_te[0], a1)
        da = np.abs(y - np.mean(mus_te, 0)) - np.abs(y - mus_te[0])
        se = d.std() / np.sqrt(len(d))
        kept[stat] = bool(d.mean() > 2 * se)
        rep.append(f'| {label} | {d.mean():+.4f} ± {se:.4f} | {da.mean():+.3f} ± {da.std() / np.sqrt(len(da)):.3f} | {"yes" if kept[stat] else "no"} |')
        print(stat, 'ensemble', f'{d.mean():+.4f} ± {se:.4f}', flush=True)
    open(out_md, 'a').write('\n'.join(rep) + '\n\n')
    print('\n'.join(rep))


def movers_test(cache, out_md):
    """Players who changed clubs (afl/model/movers.py). Appends to the report, with how many mover rows were scored."""
    from afl.model import movers as MV
    from afl.model.walkforward import prepare
    base = P.team_expected_score(pd.read_parquet(f'{cache}/frame.parquet'))
    rep = ['## Players who changed clubs', '',
           'Games at his current club, a new-club flag (first 16 games after 20+ elsewhere), playing his former club, and '
           'how far his output at the new club has moved from what he brought. Fitted 2013-2023, tuned 2024, scored '
           '2025-2026; also scored on the mover rows alone, where any effect would show.', '',
           '| stat | log-lik change (all) | on new-club rows | on former-club games | kept |', '|---|---|---|---|---|']
    for stat, label in STATS.items():
        m, feats, _ = prepare(base, cache, stat)
        m = MV.add(m, stat)
        m = P.eligible(m)
        m = m[m[f'{stat}_l10'].notna()]
        tr, tu, te = m[m.season.between(2013, 2023)], m[m.season == 2024], m[m.season.isin([2025, 2026])]
        ll0, _ = score(tr, tu, te, feats, stat)
        ll, _ = score(tr, tu, te, feats + MV.columns(stat), stat)
        d = ll - ll0
        se = d.std() / np.sqrt(len(d))
        nc, vf = (te.new_club == 1).to_numpy(), (te.vs_former_club == 1).to_numpy()
        part = lambda k: f'{d[k].mean():+.4f} ± {d[k].std() / np.sqrt(k.sum()):.4f} ({k.sum():,})'
        ok = d.mean() > 2 * se
        rep.append(f'| {label} | {d.mean():+.4f} ± {se:.4f} | {part(nc)} | {part(vf)} | {"yes" if ok else "no"} |')
        print(stat, 'movers', f'{d.mean():+.4f} ± {se:.4f}', flush=True)
    open(out_md, 'a').write('\n'.join(rep) + '\n\n')
    print('\n'.join(rep))


def grounds_test(cache, out_md):
    """Ground shape and size, measured per stat and per position (afl/model/grounds.py). Appends to the report."""
    from afl.model import grounds as GR
    from afl.model.walkforward import prepare
    base = P.team_expected_score(pd.read_parquet(f'{cache}/frame.parquet'))
    rep = ['## Ground shape and size', '',
           'What each ground has done lately to each stat, overall and for each position group, and how often the player '
           'has played there. Fitted 2013-2023, tuned 2024, scored 2025-2026; also scored at the grounds most unlike the '
           'MCG (Kardinia Park, the SCG, the Gabba, Docklands).', '',
           '| stat | log-lik change (all) | at those four grounds | kept |', '|---|---|---|---|']
    odd = {'Kardinia Park', 'S.C.G.', 'Gabba', 'Docklands'}
    kept = {}
    for stat, label in STATS.items():
        m, feats, _ = prepare(base, cache, stat)
        m = GR.add(m, stat)
        m = P.eligible(m)
        m = m[m[f'{stat}_l10'].notna()]
        tr, tu, te = m[m.season.between(2013, 2023)], m[m.season == 2024], m[m.season.isin([2025, 2026])]
        ll0, _ = score(tr, tu, te, feats, stat)
        ll, _ = score(tr, tu, te, feats + GR.columns(stat), stat)
        d = ll - ll0
        se = d.std() / np.sqrt(len(d))
        k = te.venue.isin(odd).to_numpy()
        kept[stat] = bool(d.mean() > 2 * se)
        rep.append(f'| {label} | {d.mean():+.4f} ± {se:.4f} | {d[k].mean():+.4f} ± {d[k].std() / np.sqrt(k.sum()):.4f} ({k.sum():,}) | {"yes" if kept[stat] else "no"} |')
        print(stat, 'grounds', f'{d.mean():+.4f} ± {se:.4f}', flush=True)
    open(out_md, 'a').write('\n'.join(rep) + '\n\n')
    print('\n'.join(rep))


def league_level_test(cache, out_md):
    """The league's level of each stat in recent games (the model already has it for disposals: league_game_D), so a
    rule change that moves marks, tackles or goals reaches the projection within a few rounds. Appends to the report."""
    from afl.model.walkforward import prepare
    base = P.team_expected_score(pd.read_parquet(f'{cache}/frame.parquet'))
    rep = ['## The league level of each stat', '',
           'Average per game of the stat over the league\'s last 36 games (before this one), and the same over the last 9. '
           'Fitted 2013-2023, tuned 2024, scored 2025-2026, and on 2026 alone (the year the game changed most).', '',
           '| stat | log-lik change (2025-26) | on 2026 | kept |', '|---|---|---|---|']
    for stat, label in STATS.items():
        m, feats, _ = prepare(base, cache, stat)
        gt = m.groupby(['game', 'dt'], as_index=False)[stat].sum(min_count=1).sort_values('dt')
        gt[f'league_{stat}_36'] = gt[stat].shift(1).rolling(36, min_periods=9).mean()
        gt[f'league_{stat}_9'] = gt[stat].shift(1).rolling(9, min_periods=5).mean()
        m = m.merge(gt[['game', f'league_{stat}_36', f'league_{stat}_9']], on='game', how='left')
        cols = [f'league_{stat}_36', f'league_{stat}_9']
        m = P.eligible(m)
        m = m[m[f'{stat}_l10'].notna()]
        tr, tu, te = m[m.season.between(2013, 2023)], m[m.season == 2024], m[m.season.isin([2025, 2026])]
        ll0, _ = score(tr, tu, te, feats, stat)
        ll, _ = score(tr, tu, te, [f for f in feats if f not in cols] + cols, stat)
        d = ll - ll0
        se = d.std() / np.sqrt(len(d))
        k = (te.season == 2026).to_numpy()
        ok = d.mean() > 2 * se
        rep.append(f'| {label} | {d.mean():+.4f} ± {se:.4f} | {d[k].mean():+.4f} ± {d[k].std() / np.sqrt(k.sum()):.4f} | {"yes" if ok else "no"} |')
        print(stat, 'league level', f'{d.mean():+.4f} ± {se:.4f}', flush=True)
    open(out_md, 'a').write('\n'.join(rep) + '\n\n')
    print('\n'.join(rep))


def context_test(cache, out_md):
    """Game time, umpire crew, coach, ruck matchup, opposition style (afl/model/context.py), each group on its own."""
    from afl.model import context as C
    from afl.model.walkforward import prepare
    base = P.team_expected_score(pd.read_parquet(f'{cache}/frame.parquet'))
    rep = ['## Game context: time, umpires, coach, ruck matchup, opposition style', '',
           'Each group added on its own to the current model. Fitted 2013-2023, tuned 2024, scored 2025-2026.', '',
           '| stat | game time | umpire crew | coach | ruck matchup | opposition style |', '|---|---|---|---|---|---|']
    for stat, label in STATS.items():
        m, feats, _ = prepare(base, cache, stat)
        m = C.add(m, cache, stat)
        m = P.eligible(m)
        m = m[m[f'{stat}_l10'].notna()]
        tr, tu, te = m[m.season.between(2013, 2023)], m[m.season == 2024], m[m.season.isin([2025, 2026])]
        ll0, _ = score(tr, tu, te, feats, stat)
        cells = []
        for g, cols in C.groups().items():
            ll, _ = score(tr, tu, te, feats + cols, stat)
            d = ll - ll0
            se = d.std() / np.sqrt(len(d))
            cells.append(f'{d.mean():+.4f} ± {se:.4f}{" **kept**" if d.mean() > 2 * se else ""}')
            print(stat, g, f'{d.mean():+.4f} ± {se:.4f}', flush=True)
        rep.append(f'| {label} | ' + ' | '.join(cells) + ' |')
    open(out_md, 'a').write('\n'.join(rep) + '\n\n')
    print('\n'.join(rep))


def run(cache, out_md):
    base = P.team_expected_score(pd.read_parquet(f'{cache}/frame.parquet'))
    rep = ['# Research ideas, tested without bookmaker lines', '',
           'From docs/RESEARCH_BEST_MODEL.md. Fitted 2013-2023, tuned 2024, scored 2025-2026 (never seen), paired per '
           'player-game, ± one standard error. Kept where more than two standard errors better. The market view of the game '
           'exists from 2017 (Squiggle "Punters"); earlier rows carry none and the model treats them as unknown.', '',
           '## New inputs', '']
    keep = {}
    feature_tests(base, cache, rep, keep)
    spread = spread_test(cache, rep)
    open(out_md, 'w').write('\n'.join(rep) + '\n')
    json.dump({'inputs': keep, 'spread': spread}, open(f'{cache}/research_kept.json', 'w'), indent=1)
    print('\n'.join(rep))


if __name__ == '__main__':
    if len(sys.argv) > 3 and sys.argv[3] == 'positions':
        position_test(sys.argv[1], sys.argv[2])
        sys.exit()
    if len(sys.argv) > 3 and sys.argv[3] == 'context':
        context_test(sys.argv[1], sys.argv[2])
        sys.exit()
    if len(sys.argv) > 3 and sys.argv[3] == 'league':
        league_level_test(sys.argv[1], sys.argv[2])
        sys.exit()
    if len(sys.argv) > 3 and sys.argv[3] == 'grounds':
        grounds_test(sys.argv[1], sys.argv[2])
        sys.exit()
    if len(sys.argv) > 3 and sys.argv[3] == 'movers':
        movers_test(sys.argv[1], sys.argv[2])
        sys.exit()
    if len(sys.argv) > 3 and sys.argv[3] == 'ensemble':
        ensemble_test(sys.argv[1], sys.argv[2])
        sys.exit()
    if len(sys.argv) > 3 and sys.argv[3] == 'redistribution':
        redistribution_test(sys.argv[1], sys.argv[2])
        sys.exit()
    run(sys.argv[1] if len(sys.argv) > 1 else 'afl/cache', sys.argv[2] if len(sys.argv) > 2 else 'afl/docs/RESEARCH_TESTS.md')
