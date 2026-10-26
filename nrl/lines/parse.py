"""Raw Odds API snapshots (nrl/lines/pull.py) -> one price table.

Rows: label (team-open-..., team-named-..., team-close-..., props-named-<match>, props-close-<match>), snapshot,
event_id, commence, home, away (canonical club names), book, market, outcome, point, price. Usage: python
nrl/lines/parse.py nrl/cache -> nrl/cache/odds.parquet
"""
import glob
import json
import os
import sys

import pandas as pd

from nrl.data.teams import canonical


def rows_of(label, snap, event, canon):
    for bk in event.get('bookmakers', []):
        for mk in bk.get('markets', []):
            for o in mk.get('outcomes', []):
                yield dict(label=label, kind=label.split('-')[1], snapshot=snap, event_id=event.get('id'),
                           commence=event.get('commence_time'), home=canon(event.get('home_team')),
                           away=canon(event.get('away_team')), book=bk.get('key'), market=mk.get('key'),
                           outcome=o.get('name'), description=o.get('description'), point=o.get('point'), price=o.get('price'))


def parse(cache, raw_dir=None):
    canon = canonical(cache)
    raw_dir = raw_dir or os.path.join(cache, 'odds_raw')
    out = []
    for f in sorted(glob.glob(os.path.join(raw_dir, '*.json'))):
        r = json.load(open(f))
        body = r.get('body') or {}
        data = body.get('data')
        events = data if isinstance(data, list) else [data] if data else []
        for e in events:
            out.extend(rows_of(r['label'], body.get('timestamp'), e, canon))
    df = pd.DataFrame(out)
    if len(df):
        df['commence'] = pd.to_datetime(df.commence, utc=True)
    return df


def main(cache):
    df = parse(cache)
    df.to_parquet(f'{cache}/odds.parquet', index=False)
    print(f'odds: {len(df):,} prices, {df.event_id.nunique() if len(df) else 0} events, books {sorted(df.book.unique()) if len(df) else []}')


if __name__ == '__main__':
    main(sys.argv[1])
