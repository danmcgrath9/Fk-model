"""Pull Ultimate A-League match pages (line-ups, substitutions, goals, cards), once, politely.

Why this source: it is the only one found that records who played and for how long in every A-League
match, which player props need. Its content is licensed CC BY 4.0 (site footer, checked 21 Oct 2026,
inventory3_v1.tar.gz), its terms do not restrict automated access, and its robots.txt allows /match/
and /matches/. We identify ourselves with the repository URL, wait PAUSE seconds between requests,
keep every page we fetch, and never fetch a held page again (the season in play is refreshed only when
asked). Attribution: "Ultimate A-League (ultimatealeague.com), CC BY 4.0".

Resumable: pages go into <out>/pages/<season>/<id>.html.gz; every SAVE_EVERY pages the season so far is
uploaded as ual_<season>.partial.tar.gz, and a later run downloads that and carries on. A finished
season is uploaded as ual_<season>.tar.gz and its partial file deleted.

--probe: fetch one season list and three match pages, time them, save the list page; nothing else.

Usage: python aleague/data/ual_pull.py --out aleague/cache/ual --seasons 2013-14,... --held held.txt --upload aleague-history
"""
import argparse
import gzip
import os
import re
import subprocess
import tarfile
import time

import requests

BASE = 'https://www.ultimatealeague.com'
UA = (os.environ.get('ALEAGUE_UA', '').strip() or 'fk-model A-League research') + ' (https://github.com/danmcgrath9/Fk-model)'
PAUSE = float(os.environ.get('UAL_PAUSE', '5'))
BUDGET = float(os.environ.get('UAL_BUDGET_SECONDS', str(5 * 3600)))
SAVE_EVERY = 50


class Getter:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers['User-Agent'] = UA
        # the site closes idle kept-alive connections, so a reused one fails on the next request; a fresh
        # connection each time avoids a failed request and a retry wait per page
        self.s.headers['Connection'] = 'close'
        self.t = 0.0
        self.n = 0

    def get(self, path):
        time.sleep(max(0.0, PAUSE - (time.time() - self.t)))
        for attempt in range(4):
            t0 = time.time()
            try:
                r = self.s.get(BASE + path, timeout=60)
            except requests.RequestException as e:
                print(f'  {path}: {e}; retrying', flush=True); time.sleep(5 * (attempt + 1)); continue
            self.t = time.time()
            self.n += 1
            r.elapsed_s = self.t - t0
            if r.status_code in (429, 503):
                wait = int(r.headers.get('Retry-After', 0) or 0) or 60 * (attempt + 1)
                print(f'  {path}: HTTP {r.status_code}, waiting {wait} s', flush=True); time.sleep(wait); continue
            return r
        return None


def season_ids(html):
    return sorted({int(x) for x in re.findall(r'/match/\?match_id=(\d+)', html)})


def gh(*args, check=True):
    return subprocess.run(['gh', *args], check=check, capture_output=True, text=True)


def pack(folder, season, dest):
    with tarfile.open(dest, 'w:gz') as tar:
        tar.add(os.path.join(folder, season), arcname=season)


def probe(g, season, out):
    r = g.get(f'/matches/?show=season&season={season}')
    ids = season_ids(r.text) if r is not None else []
    open(os.path.join(out, f'probe_season_{season}.html'), 'wb').write(r.content if r is not None else b'')
    print(f'season list {season}: HTTP {getattr(r, "status_code", None)}, {getattr(r, "elapsed_s", 0):.1f} s, '
          f'{len(r.content) if r is not None else 0:,} bytes, {len(ids)} match ids, {ids[:3]} ... {ids[-3:]}', flush=True)
    for mid in ids[:3]:
        p = g.get(f'/match/?match_id={mid}')
        title = re.search(r'<title>(.*?)</title>', p.text if p is not None else '', re.S)
        print(f'  match {mid}: HTTP {getattr(p, "status_code", None)}, {getattr(p, "elapsed_s", 0):.1f} s, '
              f'{title.group(1).strip() if title else "no title"}', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--seasons', required=True)
    ap.add_argument('--held', help='file listing release assets already held')
    ap.add_argument('--refresh', default='', help='a season to pull again even if held (the one in play)')
    ap.add_argument('--upload', help='GitHub release to save progress to')
    ap.add_argument('--probe', action='store_true')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    held = set(open(args.held).read().split()) if args.held and os.path.exists(args.held) else set()
    g, start, log = Getter(), time.time(), []
    if args.probe:
        probe(g, args.seasons.split(',')[0], args.out)
        return
    folder = os.path.join(args.out, 'pages')
    for season in args.seasons.split(','):
        final, partial = f'ual_{season}.tar.gz', f'ual_{season}.partial.tar.gz'
        if final in held and season != args.refresh:
            log.append(f'{season}: held, skipped'); continue
        if time.time() - start > BUDGET:
            log.append(f'{season}: not started, time budget used'); continue
        os.makedirs(os.path.join(folder, season), exist_ok=True)
        if partial in held and args.upload and season != args.refresh:  # carry on where the last run stopped
            gh('release', 'download', args.upload, '--pattern', partial, '--dir', args.out, '--clobber')
            with tarfile.open(os.path.join(args.out, partial)) as tar:
                tar.extractall(folder, filter='data')
        if season == args.refresh and final in held and args.upload:
            # the season in play: start from what is held and fetch only matches not yet completed there
            gh('release', 'download', args.upload, '--pattern', final, '--dir', args.out, '--clobber')
            with tarfile.open(os.path.join(args.out, final)) as tar:
                tar.extractall(folder, filter='data')
            for f in os.listdir(os.path.join(folder, season)):
                if f[0].isdigit():
                    page = gzip.decompress(open(os.path.join(folder, season, f), 'rb').read())
                    if b'Completed' not in page[:200000]:
                        os.remove(os.path.join(folder, season, f))
        r = g.get(f'/matches/?show=season&season={season}')
        if r is None or r.status_code != 200:
            log.append(f'{season}: season list HTTP {getattr(r, "status_code", "none")}'); continue
        ids = season_ids(r.text)
        print(f'{season}: {len(ids)} match links on the season page', flush=True)
        if len(ids) < 10:  # a wrong address or a changed page; saving it would mark the season as held
            log.append(f'{season}: only {len(ids)} match links, not saved'); continue
        open(os.path.join(folder, season, 'season.html'), 'wb').write(r.content)
        have = {int(f.split('.')[0]) for f in os.listdir(os.path.join(folder, season)) if f[0].isdigit()}
        todo = [i for i in ids if i not in have]
        got, bad, stopped = 0, [], False
        for mid in todo:
            if time.time() - start > BUDGET:
                stopped = True; break
            p = g.get(f'/match/?match_id={mid}')
            if p is None or p.status_code != 200:
                bad.append(f'{mid}:{getattr(p, "status_code", "none")}'); continue
            open(os.path.join(folder, season, f'{mid}.html.gz'), 'wb').write(gzip.compress(p.content))
            got += 1
            if got % SAVE_EVERY == 0:
                print(f'  {season}: {len(have) + got} of {len(ids)} pages, {(time.time() - start) / 60:.0f} min', flush=True)
                if args.upload:
                    pack(folder, season, os.path.join(args.out, partial))
                    gh('release', 'upload', args.upload, os.path.join(args.out, partial), '--clobber')
        name = partial if stopped else final
        pack(folder, season, os.path.join(args.out, name))
        if args.upload:
            gh('release', 'upload', args.upload, os.path.join(args.out, name), '--clobber')
            if not stopped:
                gh('release', 'delete-asset', args.upload, partial, '--yes', check=False)
        log.append(f'{season}: {len(ids)} match links, {len(have) + got} pages held'
                   + (' (stopped by the time budget; the next run carries on)' if stopped else '')
                   + (f', failed: {", ".join(bad[:10])}' if bad else ''))
        print(log[-1], flush=True)
    log.append(f'{g.n} requests in {(time.time() - start) / 60:.0f} minutes')
    text = '\n'.join(log)
    print(text)
    open(os.path.join(args.out, 'pull_log.txt'), 'w').write(text + '\n')


if __name__ == '__main__':
    main()
