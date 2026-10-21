"""Out-of-sample test of the team model, before any betting lines exist.

Without lines there is no ROI and no closing line value to report: what can be measured is whether
the model's probabilities are better than simple alternatives on seasons it never saw.

Season split, as the house standard asks (seasons by their end year):
  tune     2016-2020   hyperparameters chosen here (half-life, season carry-over, ridge, rho)
  confirm  2021-2023   the chosen settings must still be at or near the best here
  final    2024-2026   looked at once, at the end, with the settings frozen

Each prediction is made from a fit on matches before its day (aleague/model/team.py).
Compared with:
  base rates  home/draw/away, over 2.5 and both-teams-to-score shares from all earlier seasons
  Elo         rolling Elo with a home bonus and the earlier seasons' draw share

Scores (lower is better): log loss and ranked probability score (RPS) for head-to-head, log loss for
over 2.5 goals and both teams to score. Differences are bootstrapped by week (a round's games share
news and weather, so they are resampled together); a 90% interval that crosses zero is reported as
no difference.

Usage: python -m aleague.model.evaluate <tables dir> <report.md> [--final]
"""
import itertools
import sys

import numpy as np
import pandas as pd

from aleague.model.team import fit_rho, reprice, rolling_predictions

TUNE, CONFIRM, FINAL = [2016, 2017, 2018, 2019, 2020], [2021, 2022, 2023], [2024, 2025, 2026]
GRID = dict(half_life=[180, 365, 730], carry=[0.25, 0.5, 0.75, 1.0], reg=[2.0, 4.0, 8.0, 16.0, 32.0])
EPS = 1e-12


def outcome(p):
    return np.where(p.home_goals > p.away_goals, 0, np.where(p.home_goals == p.away_goals, 1, 2))


def losses(p):
    """Per-match losses for each market."""
    y = outcome(p)
    P = np.clip(p[['p_home', 'p_draw', 'p_away']].to_numpy(dtype=float), EPS, 1)
    ll = -np.log(P[np.arange(len(y)), y])
    cum = np.cumsum(P, axis=1)[:, :2]
    obs = np.cumsum(np.eye(3)[y], axis=1)[:, :2]
    rps = ((cum - obs) ** 2).sum(axis=1) / 2
    over = (p.home_goals + p.away_goals > 2.5).to_numpy()
    po = np.clip(p.p_over25.to_numpy(dtype=float), EPS, 1 - EPS)
    ll_over = -np.where(over, np.log(po), np.log(1 - po))
    both = ((p.home_goals > 0) & (p.away_goals > 0)).to_numpy()
    pb = np.clip(p.p_btts.to_numpy(dtype=float), EPS, 1 - EPS)
    ll_btts = -np.where(both, np.log(pb), np.log(1 - pb))
    return pd.DataFrame(dict(ll_h2h=ll, rps=rps, ll_over25=ll_over, ll_btts=ll_btts), index=p.index)


def base_rates(matches, seasons):
    """Each season predicted with the shares from every earlier season."""
    played = matches[matches.home_goals_90.notna()].copy()
    played['hg'], played['ag'] = played.home_goals_90.astype(float), played.away_goals_90.astype(float)
    out = []
    for s in seasons:
        past = played[played.season < s]
        cur = played[played.season == s]
        pr = dict(p_home=(past.hg > past.ag).mean(), p_draw=(past.hg == past.ag).mean(),
                  p_away=(past.hg < past.ag).mean(), p_over25=(past.hg + past.ag > 2.5).mean(),
                  p_btts=((past.hg > 0) & (past.ag > 0)).mean())
        out.append(pd.DataFrame(dict(match_id=cur.match_id, season=s, date=cur.date, home_goals=cur.hg,
                                     away_goals=cur.ag, **pr)))
    return pd.concat(out, ignore_index=True)


def elo(matches, seasons, k=20.0, home=60.0, regress=0.25):
    """Rolling Elo; the draw share and goal-market shares come from earlier seasons."""
    played = matches[matches.home_goals_90.notna()].sort_values('date')
    r, out, last_season = {}, [], None
    for _, g in played.iterrows():
        if g.season != last_season:
            r = {t: 1500 + (v - 1500) * (1 - regress) for t, v in r.items()}
            past = played[played.season < g.season]
            hg, ag = past.home_goals_90.astype(float), past.away_goals_90.astype(float)
            draw = (hg == ag).mean() if len(past) else 0.27
            over = (hg + ag > 2.5).mean() if len(past) else 0.55
            bt = ((hg > 0) & (ag > 0)).mean() if len(past) else 0.55
            last_season = g.season
        rh, ra = r.get(g.home, 1500.0), r.get(g.away, 1500.0)
        e = 1 / (1 + 10 ** (-(rh - ra + (0 if g.neutral else home)) / 400))
        if g.season in seasons:
            out.append(dict(match_id=g.match_id, season=g.season, date=g.date, home_goals=float(g.home_goals_90),
                            away_goals=float(g.away_goals_90), p_home=(1 - draw) * e, p_draw=draw,
                            p_away=(1 - draw) * (1 - e), p_over25=over, p_btts=bt))
        s = 1.0 if g.home_goals_90 > g.away_goals_90 else 0.5 if g.home_goals_90 == g.away_goals_90 else 0.0
        r[g.home], r[g.away] = rh + k * (s - e), ra - k * (s - e)
    return pd.DataFrame(out)


def week_of(dates):
    d = pd.to_datetime(pd.Series(dates))
    return (d - pd.to_timedelta(d.dt.dayofweek, unit='D')).dt.date.to_numpy()


def boot_diff(a, b, groups, n=2000, seed=7):
    """Mean of a - b with a 90% interval, resampling whole weeks."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame(dict(d=np.asarray(a) - np.asarray(b), g=groups))
    by = df.groupby('g').d.agg(['sum', 'count'])
    s, c = by['sum'].to_numpy(), by['count'].to_numpy()
    idx = rng.integers(0, len(by), size=(n, len(by)))
    means = s[idx].sum(1) / c[idx].sum(1)
    return df.d.mean(), np.percentile(means, 5), np.percentile(means, 95)


def _one(args):
    matches, hl, ca, rg = args
    p = rolling_predictions(matches, TUNE + CONFIRM, half_life=hl, carry=ca, reg=rg, rho=0.0)
    return dict(half_life=hl, carry=ca, reg=rg, preds=p)


def tune(matches):
    import os
    from concurrent.futures import ProcessPoolExecutor
    jobs = [(matches, hl, ca, rg) for hl, ca, rg in itertools.product(GRID['half_life'], GRID['carry'], GRID['reg'])]
    with ProcessPoolExecutor(max_workers=max(1, (os.cpu_count() or 2) - 0)) as ex:
        return list(ex.map(_one, jobs))


def main(tables, report, show_final=False):
    matches = pd.read_parquet(f'{tables}/matches.parquet')
    lines = ['# A-League Men team model, step 1: out-of-sample results', '',
             'Expected goals per side from a time-weighted Dixon-Coles model, refitted before every match day '
             'on earlier matches only; every market priced from one score matrix. "At the open" only: '
             'no line-ups in the data yet. No betting lines yet either, so this measures the probabilities '
             'against simple alternatives, not profit.', '']

    # 1. tune on 2016-2020 (rho fitted for each setting on the tune seasons), confirm on 2021-2023
    grid = tune(matches)
    res, confirm_losses = [], {}
    for gset in grid:
        p = gset['preds']
        t = p[p.season.isin(TUNE)]
        rho = fit_rho(t)
        p2 = reprice(p, rho)
        L = losses(p2)
        tm, cm = p2.season.isin(TUNE).to_numpy(), p2.season.isin(CONFIRM).to_numpy()
        score = lambda mask: (L.ll_h2h[mask].mean() + L.ll_over25[mask].mean())  # noqa: E731
        key = (gset['half_life'], gset['carry'], gset['reg'])
        confirm_losses[key] = pd.Series((L.ll_h2h + L.ll_over25)[cm].to_numpy(), index=p2.match_id[cm].to_numpy())
        res.append(dict(half_life=gset['half_life'], carry=gset['carry'], reg=gset['reg'], rho=rho,
                        tune=score(tm), confirm=score(cm)))
    res = pd.DataFrame(res).sort_values('tune').reset_index(drop=True)
    res['confirm_rank'] = res.confirm.rank().astype(int)
    best = res.iloc[0]
    res.to_csv(report.replace('.md', '_grid.csv'), index=False)
    cbest = res.sort_values('confirm').iloc[0]
    a = confirm_losses[(best.half_life, best.carry, best.reg)]
    b = confirm_losses[(cbest.half_life, cbest.carry, cbest.reg)].reindex(a.index)
    dates = matches.set_index('match_id').date.reindex(a.index)
    gap, glo, ghi = boot_diff(a.to_numpy(), b.to_numpy(), week_of(dates.to_numpy()))
    lines += ['## Settings, chosen on 2016-2020 and checked on 2021-2023', '',
              'Score = head-to-head log loss + over 2.5 log loss (lower is better). Top five by the tune seasons, '
              f'out of {len(res)} combinations:', '',
              res.head(5).round(4).to_markdown(index=False), '',
              f'Chosen: half-life {best.half_life:.0f} days, season carry-over {best.carry}, ridge {best.reg}, '
              f'rho {best.rho:.3f}. On the confirm seasons it ranks {int(best.confirm_rank)} of {len(res)} '
              f'(best confirm score {res.confirm.min():.4f}, chosen {best.confirm:.4f}). The gap to the best '
              f'setting on the confirm seasons is {gap:+.4f} a match, 90% interval {glo:+.4f} to {ghi:+.4f} '
              f'(resampling weeks): {"within noise" if glo <= 0 else "a real gap"}. Spread of the tune score '
              f'across all {len(res)} settings: {res.tune.min():.4f} to {res.tune.max():.4f}.', '']

    # 2. final seasons, frozen settings
    shown = TUNE + CONFIRM + (FINAL if show_final else [])
    final = rolling_predictions(matches, shown, half_life=best.half_life, carry=best.carry,
                                reg=best.reg, rho=best.rho)
    base = base_rates(matches, shown)
    el = elo(matches, shown)
    ids = set(final.match_id) & set(base.match_id) & set(el.match_id)
    final, base, el = (x[x.match_id.isin(ids)].sort_values('match_id').reset_index(drop=True) for x in (final, base, el))
    Lm, Lb, Le = losses(final), losses(base), losses(el)

    lines += ['## Every season, settings frozen (tune, confirm, then the final three)', '',
              '| season | games | model h2h log loss | Elo | base rates | model RPS | Elo RPS | model over 2.5 | base | model BTTS | base |',
              '|---|---|---|---|---|---|---|---|---|---|---|']
    for s in shown:
        k = (final.season == s).to_numpy()
        lines.append(f'| {s - 1}-{str(s)[2:]} | {k.sum()} | {Lm.ll_h2h[k].mean():.4f} | {Le.ll_h2h[k].mean():.4f} | '
                     f'{Lb.ll_h2h[k].mean():.4f} | {Lm.rps[k].mean():.4f} | {Le.rps[k].mean():.4f} | '
                     f'{Lm.ll_over25[k].mean():.4f} | {Lb.ll_over25[k].mean():.4f} | '
                     f'{Lm.ll_btts[k].mean():.4f} | {Lb.ll_btts[k].mean():.4f} |')
    lines.append('')

    if not show_final:
        text = '\n'.join(lines + ['Final seasons not shown yet (run with --final once the settings are frozen).'])
        open(report, 'w').write(text + '\n')
        print(text)
        return best
    k = final.season.isin(FINAL).to_numpy()
    wk = week_of(final.date[k])
    lines += ['## The final three seasons together (2023-24 to 2025-26), 90% intervals by week', '',
              '| comparison | mean difference (negative = model better) | 90% interval | verdict |', '|---|---|---|---|']
    for name, a, b in [('h2h log loss: model - base rates', Lm.ll_h2h, Lb.ll_h2h),
                       ('h2h log loss: model - Elo', Lm.ll_h2h, Le.ll_h2h),
                       ('h2h RPS: model - Elo', Lm.rps, Le.rps),
                       ('over 2.5 log loss: model - base rates', Lm.ll_over25, Lb.ll_over25),
                       ('BTTS log loss: model - base rates', Lm.ll_btts, Lb.ll_btts)]:
        d, lo, hi = boot_diff(a[k], b[k], wk)
        verdict = 'model better' if hi < 0 else 'model worse' if lo > 0 else 'no difference'
        lines.append(f'| {name} | {d:+.4f} | {lo:+.4f} to {hi:+.4f} | {verdict} |')
    lines.append('')

    # 3. calibration on the final seasons
    f = final[k].copy()
    lines += ['## Calibration, final three seasons (does a 40% home win happen 40% of the time?)', '',
              '| market | predicted band | games | average predicted | happened |', '|---|---|---|---|---|']
    for col, hit, name in [('p_home', f.home_goals > f.away_goals, 'home win'),
                           ('p_draw', f.home_goals == f.away_goals, 'draw'),
                           ('p_away', f.home_goals < f.away_goals, 'away win'),
                           ('p_over25', f.home_goals + f.away_goals > 2.5, 'over 2.5')]:
        bands = pd.cut(f[col], [0, .2, .3, .4, .5, .6, .7, 1])
        for b, x in f.groupby(bands, observed=True):
            lines.append(f'| {name} | {b} | {len(x)} | {x[col].mean():.3f} | {hit[x.index].mean():.3f} |')
    lines.append('')
    goals = f.home_goals + f.away_goals
    lines += [f'Goals per game, final three seasons: predicted {(f.lam_home + f.lam_away).mean():.2f}, '
              f'actual {goals.mean():.2f}. Home win share predicted {f.p_home.mean():.3f}, actual '
              f'{(f.home_goals > f.away_goals).mean():.3f}; draws {f.p_draw.mean():.3f} against '
              f'{(f.home_goals == f.away_goals).mean():.3f}.', '']
    text = '\n'.join(lines)
    open(report, 'w').write(text + '\n')
    print(text)
    final.to_parquet(report.replace('.md', '_predictions.parquet'), index=False)
    return best


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], show_final='--final' in sys.argv)
