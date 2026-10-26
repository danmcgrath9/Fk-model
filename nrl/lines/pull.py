"""The historical odds pull: dry run by default, pulls only when nrl/lines/plan.json says approved.

Per round (from our fixture list, nrl/cache/team_wf.parquet, so only games we price):
  team markets (h2h, line, total), one sport-level call per snapshot, covering every game listed at that time:
    open   the Monday before the round, 12:00 Sydney (before teams are named)
    named  the Tuesday, 20:00 Sydney (after the lists)
    close  30 minutes before each kick-off, one call per distinct kick-off time
  anytime try scorer, one event-level call per game at named and at close (from prop_from)
Cost (the-odds-api.com v4): 10 x markets x regions per historical odds call. The dry run prints every call and the
total; the real run stops before any call that would pass max_credits (read from x-requests-used) and never buys a
snapshot already held (raw files are keyed by call). Env: ODDS_API_KEY.

Usage: python nrl/lines/pull.py nrl/cache [--dry]
"""
import datetime as dt
import json
import os
import sys
import time
from zoneinfo import ZoneInfo

import pandas as pd
import requests

BASE = 'https://api.the-odds-api.com/v4'
SYD = ZoneInfo('Australia/Sydney')
OUT = 'nrl/cache/odds_raw'


def round_snapshots(games, plan):
    """[(label, utc iso, kind, payload)] for every call the plan needs."""
    calls = []
    games = games.copy()
    games['ko'] = pd.to_datetime(games.kick_off).dt.tz_localize(None)
    # kick_off in the team frame is Sydney local
    games['ko_syd'] = games.ko.dt.tz_localize(SYD, ambiguous=True, nonexistent='shift_forward')
    games['week'] = games.ko_syd.dt.strftime('%G-%V')
    nm = len(plan['team_markets'])
    for wk, g in games.groupby('week'):
        first = g.ko_syd.min()
        monday = (first - pd.Timedelta(days=first.weekday())).normalize()
        # a round starting on a Monday or Tuesday: step back a week for its Monday and Tuesday snapshots
        if first.weekday() <= 1:
            monday -= pd.Timedelta(days=7)
        o_h, o_m = map(int, plan['snapshots_sydney']['open'].split()[1].split(':'))
        n_h, n_m = map(int, plan['snapshots_sydney']['named'].split()[1].split(':'))
        opn = monday + pd.Timedelta(hours=o_h, minutes=o_m)
        named = monday + pd.Timedelta(days=1, hours=n_h, minutes=n_m)
        for label, t in (('open', opn), ('named', named)):
            calls.append((f'team-{label}-{wk}', t.tz_convert('UTC'), 'team', 10 * nm))
        if plan.get('close_mode', 'per_kickoff') == 'per_day':
            # one snapshot 30 minutes before each match day's first game: later games that day are priced a few
            # hours before their kick-off (late, not the final close), at a fraction of the cost
            kos = g.groupby(g.ko_syd.dt.date).ko_syd.min().sort_values()
        else:
            kos = pd.Series(sorted(g.ko_syd.unique()))
        for ko in kos:
            t = pd.Timestamp(ko) - pd.Timedelta(minutes=plan['close_minutes_before'])
            calls.append((f'team-close-{pd.Timestamp(ko).strftime("%Y%m%dT%H%M")}', t.tz_convert('UTC'), 'team', 10 * nm))
        for r in g.itertuples():
            if r.ko_syd >= pd.Timestamp(plan['prop_from'], tz=SYD):
                for label, t in (('named', named), ('close', r.ko_syd - pd.Timedelta(minutes=plan['close_minutes_before']))):
                    calls.append((f'props-{label}-{r.match_id}', t.tz_convert('UTC'), ('props', r), 10 * len(plan['prop_markets'])))
    # identical close snapshots across rounds dedupe by label
    seen, out = set(), []
    for c in calls:
        if c[0] not in seen:
            seen.add(c[0])
            out.append(c)
    return out


def main(cache, dry=True):
    plan = json.load(open('nrl/lines/plan.json'))
    dry = dry or not plan.get('approved')
    wf = pd.read_parquet(f'{cache}/team_wf.parquet')
    games = wf[wf.season.isin(plan['seasons'])].drop_duplicates('match_id')
    calls = round_snapshots(games, plan)
    os.makedirs(OUT, exist_ok=True)
    held = set(os.listdir(OUT))
    todo = [c for c in calls if f'{c[0]}.json' not in held]
    cost = sum(c[3] for c in todo)
    by = pd.DataFrame([(c[0].split('-')[0] + '-' + c[0].split('-')[1], c[3]) for c in todo], columns=['kind', 'credits'])
    print(f'{len(calls):,} calls planned, {len(todo):,} not yet held, {cost:,} credits at most '
          f'(cap {plan["max_credits"]:,}); by kind: {by.groupby("kind").credits.agg(["count", "sum"]).to_dict("index")}')
    if dry:
        print('DRY RUN: nothing bought. Set "approved": true in nrl/lines/plan.json after the founder OKs this total.')
        return
    key = os.environ.get('ODDS_API_KEY', '')
    if not key:
        sys.exit('ODDS_API_KEY is not set')
    start_used, spent = None, 0
    sport, region = plan['sport'], plan['region']
    event_ids = {}
    for label, t, kind, c in todo:
        if spent + c > plan['max_credits']:
            print(f'stopping before {label}: would pass the cap (spent {spent})')
            break
        iso = t.strftime('%Y-%m-%dT%H:%M:%SZ')
        if kind == 'team':
            url = f'{BASE}/historical/sports/{sport}/odds'
            params = {'date': iso, 'regions': region, 'markets': ','.join(plan['team_markets']), 'oddsFormat': 'decimal'}
        else:
            r = kind[1]
            if (r.match_id) not in event_ids:
                ev = requests.get(f'{BASE}/historical/sports/{sport}/events', params={'date': iso, 'apiKey': key}, timeout=60)
                body = ev.json() if ev.status_code == 200 else {}
                event_ids.update(match_events(body.get('data') or [], games, cache))
                time.sleep(0.5)
            eid = event_ids.get(r.match_id)
            if not eid:
                print(f'{label}: no event id found; skipped')
                continue
            url = f'{BASE}/historical/sports/{sport}/events/{eid}/odds'
            params = {'date': iso, 'regions': region, 'markets': ','.join(plan['prop_markets']), 'oddsFormat': 'decimal'}
        resp = requests.get(url, params={**params, 'apiKey': key}, timeout=60)
        used = resp.headers.get('x-requests-used')
        if used is not None:
            used = int(float(used))
            start_used = used - int(float(resp.headers.get('x-requests-last', 0) or 0)) if start_used is None else start_used
            spent = used - start_used
        print(f'{label}: HTTP {resp.status_code}, cost {resp.headers.get("x-requests-last")}, spent {spent}')
        if resp.status_code == 200:
            json.dump({'label': label, 'requested': iso, 'body': resp.json()}, open(os.path.join(OUT, f'{label}.json'), 'w'))
        time.sleep(0.5)
    print(f'credits spent this run: {spent}')


def match_events(events, games, cache):
    """Odds API event id per our match_id: canonical team names and kick-off within 36 hours."""
    from nrl.data.teams import canonical
    canon = canonical(cache)
    out = {}
    gk = games.assign(ko=pd.to_datetime(games.kick_off).dt.tz_localize(SYD, ambiguous=True, nonexistent='shift_forward'))
    for e in events:
        h, a = canon(e.get('home_team')), canon(e.get('away_team'))
        t = pd.Timestamp(e['commence_time'])
        cand = gk[(((gk.team == h) & (gk.opp == a)) | ((gk.team == a) & (gk.opp == h))) & ((gk.ko - t).abs() < pd.Timedelta(hours=36))]
        if len(cand):
            out[cand.match_id.iloc[0]] = e['id']
    return out


if __name__ == '__main__':
    main(sys.argv[1], dry='--dry' in sys.argv)
