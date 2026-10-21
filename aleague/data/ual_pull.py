"""Pull Ultimate A-League match pages (line-ups, substitutions, goals, cards), once, politely.

Why this source: it is the only one found that records who played and for how long in every A-League
match, which player props need. Its content is licensed CC BY 4.0 (site footer, checked 21 Oct 2026,
inventory3_v1.tar.gz), its terms do not restrict automated access, and its robots.txt allows /match/
and /matches/. We identify ourselves with the repository URL, wait PAUSE seconds between requests,
keep every page we fetch, and never fetch a held season again (the season in play is refreshed only
when asked). Attribution: "Ultimate A-League (ultimatealeague.com), CC BY 4.0".

For each season: the season's match list (/matches/?show=season&season=YYYY-YY), then every match page
(/match/?match_id=N). Each season is written as <out>/ual_<season>.tar.gz so a run that stops part way
keeps every finished season.

Usage: python aleague/data/ual_pull.py --out aleague/cache/ual --seasons 2013-14,...  [--held held.txt]
"""
import argparse
import gzip
import io
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


class Getter:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers['User-Agent'] = UA
        self.t = 0.0
        self.n = 0

    def get(self, path):
        time.sleep(max(0.0, PAUSE - (time.time() - self.t)))
        for attempt in range(4):
            try:
                r = self.s.get(BASE + path, timeout=60)
            except requests.RequestException as e:
                print(f'  {path}: {e}; retrying'); time.sleep(30 * (attempt + 1)); continue
            self.t = time.time()
            self.n += 1
            if r.status_code in (429, 503):
                wait = int(r.headers.get('Retry-After', 0) or 0) or 60 * (attempt + 1)
                print(f'  {path}: HTTP {r.status_code}, waiting {wait} s'); time.sleep(wait); continue
            return r
        return None


def season_ids(html):
    return sorted({int(x) for x in re.findall(r'/match/\?match_id=(\d+)', html)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--seasons', required=True)
    ap.add_argument('--held', help='file listing release assets already held; those seasons are skipped')
    ap.add_argument('--refresh', default='', help='a season to pull again even if held (the one in play)')
    ap.add_argument('--upload', help='GitHub release to upload each finished season to, straight away')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    held = set(open(args.held).read().split()) if args.held and os.path.exists(args.held) else set()
    g, start, log = Getter(), time.time(), []
    for season in args.seasons.split(','):
        name = f'ual_{season}.tar.gz'
        if name in held and season != args.refresh:
            log.append(f'{season}: held, skipped'); continue
        if time.time() - start > BUDGET:
            log.append(f'{season}: not started, time budget used (push again to continue)'); continue
        r = g.get(f'/matches/?show=season&season={season}')
        if r is None or r.status_code != 200:
            log.append(f'{season}: season list HTTP {getattr(r, "status_code", "none")}'); continue
        ids = season_ids(r.text)
        if len(ids) < 10:  # a wrong address or a changed page; saving it would mark the season as held
            log.append(f'{season}: only {len(ids)} match links on the season page, not saved'); print(log[-1]); continue
        buf = io.BytesIO()
        got, bad = 0, []
        with tarfile.open(fileobj=buf, mode='w:gz') as tar:
            def add(fname, data):
                info = tarfile.TarInfo(fname); info.size = len(data); info.mtime = int(time.time())
                tar.addfile(info, io.BytesIO(data))
            add(f'{season}/season.html', r.content)
            for mid in ids:
                if time.time() - start > BUDGET:
                    bad.append('budget'); break
                p = g.get(f'/match/?match_id={mid}')
                if p is None or p.status_code != 200:
                    bad.append(f'{mid}:{getattr(p, "status_code", "none")}'); continue
                add(f'{season}/{mid}.html.gz', gzip.compress(p.content))
                got += 1
        if 'budget' in bad:
            log.append(f'{season}: stopped by the time budget after {got} of {len(ids)}; not saved, will redo')
            continue
        path = os.path.join(args.out, name)
        open(path, 'wb').write(buf.getvalue())
        if args.upload:  # a season only on this runner is lost if the job dies, so upload it now
            subprocess.run(['gh', 'release', 'upload', args.upload, path, '--clobber'], check=True)
        log.append(f'{season}: {len(ids)} match links, {got} pages saved'
                   + (f', failed: {", ".join(bad[:10])}' if bad else ''))
        print(log[-1], flush=True)
    log.append(f'{g.n} requests in {(time.time() - start) / 60:.0f} minutes')
    text = '\n'.join(log)
    print(text)
    open(os.path.join(args.out, 'pull_log.txt'), 'w').write(text + '\n')


if __name__ == '__main__':
    main()
