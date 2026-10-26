"""Add Cricsheet's recently added matches to the held tables, without downloading the full archive again.

Cricsheet publishes small zips of recently added matches; their names are taken from its downloads page
(passed in as saved HTML, never guessed). Each new or revised match replaces any held rows for that match,
so a corrected scorecard updates in place. Only T20 matches are kept, as in cricsheet.py.

Usage: python -m bbl.data.refresh <downloads.html> <recent zip> <parquet dir>
       python -m bbl.data.refresh --pick <downloads.html>      (prints the link to fetch)
"""
import os
import re
import sys

import pandas as pd

from bbl.data import cricsheet

TABLES = ['t20_matches', 't20_players', 't20_innings', 't20_deliveries', 't20_powerplays', 't20_replacements']
PREFER = ['recently_added_7_json.zip', 'recently_added_30_json.zip', 'recently_added_2_json.zip']


def pick(html):
    links = set(re.findall(r'href="([^"]*recently_added_\d+_json\.zip)"', html))
    for want in PREFER:
        for l in links:
            if l.endswith(want):
                return l if l.startswith('http') else 'https://cricsheet.org' + ('' if l.startswith('/') else '/downloads/') + l
    raise SystemExit(f'no recently-added zip linked from the downloads page (found: {sorted(links)})')


def merge(held, new, ids):
    """Held rows for every match in `ids` (all the matches in the recent zip) are dropped, then `new` is appended:
    a revised match whose new version has no rows for this table (no substitutions, say) loses its stale ones too."""
    out = held[~held.match_id.isin(ids)]
    if new is not None and len(new):
        out = pd.concat([out, new], ignore_index=True)
    for c in out.columns:
        if out[c].dtype == object:
            out[c] = out[c].astype('string')
    return out.reset_index(drop=True), len(ids)


def main(html_path, zip_path, d):
    new = cricsheet.parse_zip(zip_path)
    held_ids = set(pd.read_parquet(os.path.join(d, 't20_matches.parquet'), columns=['match_id']).match_id)
    fresh = set(new['t20_matches'].match_id) - held_ids if len(new['t20_matches']) else set()
    ids = set(new['t20_matches'].match_id) if len(new['t20_matches']) else set()
    for t in TABLES:
        path = os.path.join(d, t + '.parquet')
        merged, n = merge(pd.read_parquet(path), new[t], ids)
        merged.to_parquet(path, index=False)
    nm = new['t20_matches']
    bb = nm[nm.competition.isin(['Big Bash League', "Women's Big Bash League"])] if len(nm) else nm
    print(f'recently added: {len(nm)} T20 matches ({len(fresh)} new to us, {len(nm) - len(fresh)} revised); '
          f'BBL/WBBL among them: {len(bb)}')
    with open(os.path.join(d, 'new_match_ids.txt'), 'w') as fh:
        fh.write(''.join(m + '\n' for m in sorted(fresh)))


if __name__ == '__main__':
    if sys.argv[1] == '--pick':
        print(pick(open(sys.argv[2]).read()))
    else:
        main(*sys.argv[1:])
