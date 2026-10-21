"""Third inventory look: what Ultimate A-League offers for reuse (CC BY 4.0, per its own footer).

Four pages, PAUSE seconds apart: its integration page (API and researcher sections), the downloadable
matches page, and one recent and one older match page, to see what a match carries (line-ups,
substitutions with minutes, cards). Usage: python aleague/data/inventory3.py --out aleague/cache/inventory3
"""
import argparse
import os
import re

from aleague.data.inventory2 import F, text_of

BASE = 'https://www.ultimatealeague.com'
PAGES = {'integration': '/integration/', 'downloadable': '/matches/?show=dl',
         'match 3268 (2026-27 round 1)': '/match/?match_id=3268', 'match 2400': '/match/?match_id=2400'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    f = F(args.out)
    report = ['# Ultimate A-League: what it offers', '']
    for name, path in PAGES.items():
        r = f.get(BASE + path, 'ual ' + name + '.html')
        if r is None or r.status_code != 200:
            report += [f'## {name}: HTTP {getattr(r, "status_code", "no answer")}', '']; continue
        lines = text_of(r.text)
        # skip the site navigation, which repeats on every page
        start = next((i for i, l in enumerate(lines) if l in ('2025-26', '2026-27')), 0)
        body = [l for l in lines[start:] if not re.fullmatch(r'20\d\d-\d\d', l)][:150]
        hrefs = sorted(set(re.findall(r'href="([^"]*(?:dl|download|csv|xls|json|api|export)[^"]*)"', r.text, re.I)))
        report += [f'## {name} ({path})', '', 'Links that look like downloads or an API: ' + (', '.join(hrefs[:30]) or 'none'),
                   '', '```', *body, '```', '']
    text = '\n'.join(report)
    open(os.path.join(args.out, 'INVENTORY3.md'), 'w').write(text)
    print(text)
    s = os.environ.get('GITHUB_STEP_SUMMARY')
    if s:
        open(s, 'a').write(text + '\n')


if __name__ == '__main__':
    main()
