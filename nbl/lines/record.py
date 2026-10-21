"""Record NBL prices from Australian books through the week (The Odds API): the openers, the moves and
the close, so our prices can finally be tested against real ones.

Each run (every 30 minutes from the workflow) decides what is worth a call:
  team markets  head-to-head, line and total for every listed game, at most every TEAM_EVERY hours, and
                again when a game tips within CLOSE_MINUTES (the close)
  player props  points, rebounds, assists, threes, PRA for each game tipping within PROP_HOURS, at most
                every PROP_EVERY hours per game, and once more within CLOSE_MINUTES of its tip
Every call is priced first and skipped if it would take this run past MAX_CREDITS or the season past
NBL_BUDGET (60,000: the NBL share of the shared key). Spend is read from the provider's own
x-requests-last header and kept in a ledger on the nbl-history release, so the season total is ours, not
the whole key's. The response bodies are appended to lines_<date>.jsonl.gz.

Costs: NOT verified against The Odds API's own pages (blocked from here); secondhand sources say /events
is free and /odds and event odds cost 1 per market per region. Nothing relies on that: every call's real
cost, the events call included, is read from x-requests-last and written to the ledger. If those rules
hold, covering every game this season costs about 13,000 credits (team markets ~5,400, props ~7,700).

Env: ODDS_API_KEY (never printed), MAX_CREDITS (default 60 a run), NBL_BUDGET (60000), STATE (directory
holding ledger.csv and today's jsonl.gz; the workflow syncs it with the release)
"""
import datetime as dt
import gzip
import json
import os
import sys

import pandas as pd
import requests

BASE = 'https://api.the-odds-api.com/v4'
SPORT = 'basketball_nbl'
TEAM_MARKETS = ['h2h', 'spreads', 'totals']
PROP_MARKETS = ['player_points', 'player_rebounds', 'player_assists', 'player_threes', 'player_points_rebounds_assists']
TEAM_EVERY, PROP_EVERY, PROP_HOURS, CLOSE_MINUTES = 2.0, 3.0, 30.0, 40.0
LEDGER_COLS = ['at', 'kind', 'event', 'cost', 'status']


def load_ledger(state):
    path = os.path.join(state, 'ledger.csv')
    if os.path.exists(path):
        led = pd.read_csv(path)
        led['at'] = pd.to_datetime(led['at'], utc=True)
        return led
    return pd.DataFrame(columns=LEDGER_COLS).astype({'cost': float})


def plan(events, ledger, now):
    """What to call this run: [('team', None) | ('props', event_id), ...], before any budget check.
    events: list of dicts with id and commence_time; ledger: earlier calls."""
    calls = []
    ok = ledger[ledger.status == 200] if len(ledger) else ledger
    tips = {e['id']: pd.Timestamp(e['commence_time']) for e in events}
    upcoming = {k: t for k, t in tips.items() if t > now}
    team = ok[ok.kind == 'team'] if len(ok) else ok
    last_team = team['at'].max() if len(team) else None
    closing = [k for k, t in upcoming.items() if (t - now) <= pd.Timedelta(minutes=CLOSE_MINUTES)]
    closed_already = set()
    if len(team):
        for k in closing:
            if (team['at'] >= tips[k] - pd.Timedelta(minutes=CLOSE_MINUTES)).any():
                closed_already.add(k)
    if upcoming and (last_team is None or now - last_team >= pd.Timedelta(hours=TEAM_EVERY) or set(closing) - closed_already):
        calls.append(('team', None))
    for k, t in sorted(upcoming.items(), key=lambda x: x[1]):
        if t - now > pd.Timedelta(hours=PROP_HOURS):
            continue
        mine = ok[(ok.kind == 'props') & (ok.event == k)] if len(ok) else ok
        last = mine['at'].max() if len(mine) else None
        in_close = (t - now) <= pd.Timedelta(minutes=CLOSE_MINUTES)
        close_done = len(mine) and (mine['at'] >= t - pd.Timedelta(minutes=CLOSE_MINUTES)).any()
        if last is None or now - last >= pd.Timedelta(hours=PROP_EVERY) or (in_close and not close_done):
            calls.append(('props', k))
    return calls


def estimated_cost(kind):
    return len(TEAM_MARKETS) if kind == 'team' else len(PROP_MARKETS)


def main():
    key = os.environ.get('ODDS_API_KEY', '')
    if not key:
        print('ODDS_API_KEY is not set: nothing recorded (add the repository secret to start).')
        return 0
    state = os.environ.get('STATE', 'nbl/cache/lines')
    os.makedirs(state, exist_ok=True)
    max_run = float(os.environ.get('MAX_CREDITS', '60'))
    budget = float(os.environ.get('NBL_BUDGET', '60000'))
    now = pd.Timestamp.now(tz='UTC')
    ledger = load_ledger(state)
    season_spent = float(ledger.cost.fillna(0).sum()) if len(ledger) else 0.0

    r = requests.get(f'{BASE}/sports/{SPORT}/events', params={'apiKey': key}, timeout=60)
    if r.status_code != 200:
        print(f'events: HTTP {r.status_code} {r.text[:200]}')
        return 1
    events = r.json()
    ev_cost = float(r.headers.get('x-requests-last', 0) or 0)
    calls = plan(events, ledger, now)
    print(f'{len(events)} events listed; {len(calls)} calls planned; season spend so far {season_spent:.0f} of {budget:.0f}')
    spent, rows, bodies = ev_cost, [dict(at=now, kind='events', event=None, cost=ev_cost, status=200)], []
    for kind, ev in calls:
        est = estimated_cost(kind)
        if spent + est > max_run or season_spent + spent + est > budget:
            print(f'SKIPPED {kind} {ev or ""}: over the cap (this run {spent:.0f}/{max_run:.0f}, season {season_spent + spent:.0f}/{budget:.0f})')
            continue
        if kind == 'team':
            url, mk = f'{BASE}/sports/{SPORT}/odds', TEAM_MARKETS
        else:
            url, mk = f'{BASE}/sports/{SPORT}/events/{ev}/odds', PROP_MARKETS
        resp = requests.get(url, params={'apiKey': key, 'regions': 'au', 'markets': ','.join(mk), 'oddsFormat': 'decimal'}, timeout=60)
        cost = float(resp.headers.get('x-requests-last', est) or est)
        spent += cost
        rows.append(dict(at=now, kind=kind, event=ev, cost=cost, status=resp.status_code))
        # never echo the URL: it carries the key
        print(f'{kind} {ev or ""}: HTTP {resp.status_code}, cost {cost:.0f}, remaining on the key {resp.headers.get("x-requests-remaining")}')
        if resp.status_code == 200:
            bodies.append(dict(at=now.isoformat(), kind=kind, event=ev, body=resp.json()))
    if len(rows) > 1 or ev_cost > 0:
        ledger = pd.concat([ledger, pd.DataFrame(rows)], ignore_index=True)
        ledger.to_csv(os.path.join(state, 'ledger.csv'), index=False)
    if bodies:
        day = now.tz_convert('Australia/Melbourne').strftime('%Y-%m-%d')
        with gzip.open(os.path.join(state, f'lines_{day}.jsonl.gz'), 'at') as fh:
            for b in bodies:
                fh.write(json.dumps(b) + '\n')
    print(f'this run spent {spent:.0f}; season {season_spent + spent:.0f} of {budget:.0f}')
    summ = os.environ.get('GITHUB_STEP_SUMMARY')
    if summ:
        open(summ, 'a').write(f'NBL lines: {len(bodies)} snapshots, {spent:.0f} credits; season {season_spent + spent:.0f} of {budget:.0f}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
