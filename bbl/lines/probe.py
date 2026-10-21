"""What does The Odds API actually hold for BBL (and WBBL)? A small, capped probe before any bulk pull.

Answers, each from a real response, in order of value (the cap stops the later ones first):
  0. free: which cricket sport keys exist (exact keys for BBL and WBBL), and the fixtures listed now
  1. which market keys AU books offer on upcoming games today (event markets endpoint, 1 credit each)
  2. coverage: does the archive list BBL games in each season since 2020/21 (1 credit per date)
  3. team markets: head-to-head every season; line and total on the last three seasons
  4. any non-team market found in (1), tried on archived games: books, players per game
  5. opening: on one 2025/26 game, how many days before the start head-to-head first appears

Costs (the-odds-api.com/liveapi/guides/v4): sports list and events list 0; historical events 1 (0 if
empty); historical odds and historical event odds 10 x markets x regions; event markets 1. The probe
stops before any call that would take it past MAX_CREDITS, reading the provider's own x-requests-used
header after every call.

Env: ODDS_API_KEY (GitHub secret; never printed), MAX_CREDITS (default 0 = the free calls only),
OUT (default bbl/cache/odds_probe)
"""
import datetime as dt
import json
import os
import sys

import requests

BASE = 'https://api.the-odds-api.com/v4'
KEY = os.environ.get('ODDS_API_KEY', '')
MAX_CREDITS = int(os.environ.get('MAX_CREDITS', '0'))
OUT = os.environ.get('OUT', 'bbl/cache/odds_probe')
TEAM_MARKETS = {'h2h', 'h2h_lay', 'spreads', 'totals'}
MAX_OTHER_MARKETS = 4

# 06:00 UTC = 5pm in Sydney (daylight time), before the usual 7:15pm start; mid-December and mid-January each season
SEASONS = {
    '2020/21': ['2020-12-20T06:00:00Z', '2021-01-15T06:00:00Z'],
    '2021/22': ['2021-12-15T06:00:00Z', '2022-01-12T06:00:00Z'],
    '2022/23': ['2022-12-20T06:00:00Z', '2023-01-12T06:00:00Z'],
    '2023/24': ['2023-12-15T06:00:00Z', '2024-01-12T06:00:00Z'],
    '2024/25': ['2024-12-20T06:00:00Z', '2025-01-10T06:00:00Z'],
    '2025/26': ['2025-12-19T06:00:00Z', '2026-01-09T06:00:00Z'],
}
FULL_TEAM_MARKETS_FROM = '2023/24'  # line and total tried on this season and later


class Budget:
    def __init__(self):
        self.start = None
        self.used = None
        self.calls = []

    def can(self, cost):
        spent = 0 if self.start is None else self.used - self.start
        return spent + cost <= MAX_CREDITS

    def note(self, resp, label):
        used = resp.headers.get('x-requests-used')
        if used is not None:
            used = int(float(used))
            last = int(float(resp.headers.get('x-requests-last', 0) or 0))
            if self.start is None:
                self.start = used - last
            self.used = used
        self.calls.append(dict(label=label, status=resp.status_code, cost=resp.headers.get('x-requests-last'),
                               remaining=resp.headers.get('x-requests-remaining')))

    @property
    def spent(self):
        return 0 if self.start is None else self.used - self.start


budget = Budget()


def get(path, params, label, cost):
    if not budget.can(cost):
        print(f'SKIPPED {label}: would pass the {MAX_CREDITS}-credit cap (spent {budget.spent})')
        return None
    r = requests.get(f'{BASE}{path}', params={**params, 'apiKey': KEY}, timeout=60)
    budget.note(r, label)
    # never echo the URL: it carries the key
    print(f'{label}: HTTP {r.status_code}, cost {r.headers.get("x-requests-last")}, remaining {r.headers.get("x-requests-remaining")}')
    if r.status_code != 200:
        print(f'  body: {r.text[:300]}')
        return None
    body = r.json()
    safe = ''.join(c if c.isalnum() or c in '-_.' else '_' for c in label)
    with open(os.path.join(OUT, safe + '.json'), 'w') as fh:
        json.dump(body, fh)
    return body


def market_summary(data, market):
    """Books, players (distinct outcome descriptions) and a sample outcome for one market in one event."""
    rows = []
    for bk in (data or {}).get('bookmakers', []):
        for mk in bk.get('markets', []):
            if mk.get('key') != market:
                continue
            outs = mk.get('outcomes', [])
            players = {o.get('description') for o in outs if o.get('description')}
            rows.append((bk.get('key'), len(players), outs[0] if outs else None))
    return rows


def fmt_outcome(o):
    if not o:
        return ''
    return ' '.join(str(x) for x in (o.get('description'), o.get('name'), o.get('point'), '@', o.get('price')) if x is not None)


def first_game_after(events, when):
    t = when.replace('Z', '+00:00')
    later = [e for e in events if e.get('commence_time', '').replace('Z', '+00:00') >= t]
    return sorted(later, key=lambda e: e['commence_time'])[0] if later else None


def main():
    if not KEY:
        sys.exit('ODDS_API_KEY is not set')
    os.makedirs(OUT, exist_ok=True)
    report = ['# The Odds API probe: BBL and WBBL', '', f'Credit cap for this run: {MAX_CREDITS}.', '']

    # 0. sport keys (free)
    sports = get('/sports', {'all': 'true'}, 'sports list', 0) or []
    cricket = [s for s in sports if (s.get('group') or '').lower() == 'cricket']
    report += ['## Cricket sport keys listed', '', '| key | title | description | active | has outrights |', '|---|---|---|---|---|']
    report += [f'| {s["key"]} | {s.get("title")} | {s.get("description")} | {s.get("active")} | {s.get("has_outrights")} |' for s in cricket]
    report.append('')
    bash = [s['key'] for s in cricket if 'big bash' in f'{s.get("title")} {s.get("description")}'.lower() or 'bbl' in s['key']]
    bbl = next((k for k in bash if 'women' not in k and 'wbbl' not in k), None)
    report += [f'Big Bash keys found: {", ".join(bash) or "NONE"}; men\'s key used below: `{bbl}`.', '']

    # 0b. fixtures listed now (free), and 1. market keys on them (1 credit each)
    other_markets = []
    report += ['## Upcoming games listed now, and the market keys AU books offer on them', '',
               '| sport | game | starts (UTC) | books | market keys offered |', '|---|---|---|---|---|']
    for key in bash:
        events = get(f'/sports/{key}/events', {}, f'events now {key}', 0) or []
        report.append(f'| {key} | {len(events)} games listed | | | |')
        for e in sorted(events, key=lambda x: x['commence_time'])[:2]:
            mk = get(f'/sports/{key}/events/{e["id"]}/markets', {'regions': 'au'}, f'markets now {e["id"][:8]}', 1)
            books = (mk or {}).get('bookmakers', [])
            keys = sorted({m['key'] for b in books for m in b.get('markets', [])})
            other_markets += [k for k in keys if k not in TEAM_MARKETS and k not in other_markets]
            report.append(f'| {key} | {e["away_team"]} at {e["home_team"]} | {e["commence_time"]} | {len(books)} | '
                          f'{", ".join(keys) or ("not checked" if mk is None else "none")} |')
    report.append('')
    other_markets = other_markets[:MAX_OTHER_MARKETS]
    report += [f'Non-team market keys to try on the archive: {", ".join(other_markets) or "none found"}.', '']

    if not bbl:
        report.append('No men\'s Big Bash key: the archive checks below were not run.')
    else:
        # 2 and 3. archive coverage and team markets per season
        report += ['## Archive: BBL games and team markets, one snapshot per season (5pm Sydney)', '',
                   '| season | snapshot asked | games listed | markets asked | games priced | books per game | books | sample head-to-head |',
                   '|---|---|---|---|---|---|---|---|']
        samples = {}
        for season, dates in SEASONS.items():
            d = dates[0]
            ev = get(f'/historical/sports/{bbl}/events', {'date': d}, f'events {d[:10]}', 1)
            games = (ev or {}).get('data') or []
            if not games and len(dates) > 1:
                d = dates[1]
                ev = get(f'/historical/sports/{bbl}/events', {'date': d}, f'events {d[:10]}', 1)
                games = (ev or {}).get('data') or []
            g = first_game_after(games, d)
            if g:
                samples[season] = (g, d)
            markets = 'h2h,spreads,totals' if season >= FULL_TEAM_MARKETS_FROM else 'h2h'
            snap = get(f'/historical/sports/{bbl}/odds', {'date': d, 'regions': 'au', 'markets': markets, 'oddsFormat': 'decimal'},
                       f'team markets {d[:10]}', 10 * len(markets.split(','))) if games else None
            data = (snap or {}).get('data') or []
            keys = sorted({b['key'] for x in data for b in x.get('bookmakers', [])})
            per_mkt = {m: sum(1 for x in data if any(mm['key'] == m for b in x.get('bookmakers', []) for mm in b.get('markets', [])))
                       for m in markets.split(',')}
            h = next((market_summary(x, 'h2h') for x in data if market_summary(x, 'h2h')), [])
            report.append(f'| {season} | {d[:10]} | {len(games)} | {markets} | {", ".join(f"{m} {n}" for m, n in per_mkt.items()) if snap else "not checked"} | '
                          f'{", ".join(str(len(x.get("bookmakers", []))) for x in data)} | {", ".join(keys)} | {fmt_outcome(h[0][2]) if h else ""} |')
        report.append('')

        # 4. the non-team markets on archived games (latest two seasons)
        if other_markets:
            report += ['## Non-team markets on archived games', '', '| season | game | market | books (players each) | sample |', '|---|---|---|---|---|']
            for season in list(SEASONS)[-2:]:
                if season not in samples:
                    continue
                g, d = samples[season]
                snap = get(f'/historical/sports/{bbl}/events/{g["id"]}/odds',
                           {'date': d, 'regions': 'au', 'markets': ','.join(other_markets), 'oddsFormat': 'decimal'},
                           f'other markets {season.replace("/", "-")}', 10 * len(other_markets))
                for m in other_markets:
                    rows = market_summary((snap or {}).get('data'), m)
                    s = next((x[2] for x in rows if x[2]), None)
                    report.append(f'| {season} | {g["away_team"]} at {g["home_team"]} | {m} | '
                                  f'{", ".join(f"{b} ({n})" for b, n, _ in rows) or ("none" if snap else "not checked")} | {fmt_outcome(s)} |')
            report.append('')

        # 5. when does head-to-head first appear?
        last = samples.get(list(SEASONS)[-1])
        if last:
            g = last[0]
            start = dt.datetime.fromisoformat(g['commence_time'].replace('Z', '+00:00'))
            report += [f'## When head-to-head first appears: {g["away_team"]} at {g["home_team"]}, start {g["commence_time"]}', '',
                       '| days before the start | snapshot returned | books with head-to-head |', '|---|---|---|']
            for days in (21, 10, 5, 2, 1):
                t = (start - dt.timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
                snap = get(f'/historical/sports/{bbl}/events/{g["id"]}/odds',
                           {'date': t, 'regions': 'au', 'markets': 'h2h', 'oddsFormat': 'decimal'}, f'opening -{days}d', 10)
                rows = market_summary((snap or {}).get('data'), 'h2h')
                report.append(f'| {days} | {(snap or {}).get("timestamp", "no snapshot / not checked")} | '
                              f'{", ".join(b for b, _, _ in rows) or "none"} |')
            report.append('')

    report += [f'**Credits spent this probe: {budget.spent}** (cap {MAX_CREDITS}); remaining on the plan: '
               f'{budget.calls[-1]["remaining"] if budget.calls else "unknown"}.', '',
               '| call | HTTP | cost | remaining |', '|---|---|---|---|']
    report += [f'| {c["label"]} | {c["status"]} | {c["cost"]} | {c["remaining"]} |' for c in budget.calls]
    text = '\n'.join(report) + '\n'
    open(os.path.join(OUT, 'PROBE.md'), 'w').write(text)
    print(text)
    summ = os.environ.get('GITHUB_STEP_SUMMARY')
    if summ:
        open(summ, 'a').write(text)


if __name__ == '__main__':
    main()
