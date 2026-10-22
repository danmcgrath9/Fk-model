"""Record what each NBL data source says about reuse, before anything is pulled from it.

Fetches each site's robots.txt and its terms pages once, strips the HTML, and prints every sentence
that mentions scraping, automated access, downloading, reproduction or commercial use. Run from GitHub's
runners (the sites are not reachable from the cloud session). Reading a terms page is not a data pull.

Usage: python nbl/data/terms.py > terms.md
"""
import re
import sys
import time

import requests

UA = 'fk-model NBL research (terms check)'
PAGES = {
    'NBL website': ['https://www.nbl.com.au/robots.txt', 'https://www.nbl.com.au/terms-and-conditions',
                    'https://www.nbl.com.au/terms-of-use', 'https://www.nbl.com.au/privacy-policy'],
    'Genius Sports / FIBA LiveStats (the NBL stats feed nblR scrapes)': [
        'https://fibalivestats.dcd.shared.geniussports.com/robots.txt', 'https://www.geniussports.com/terms-of-use/'],
    'Australia Sports Betting (historical NBL odds)': [
        'https://www.aussportsbetting.com/robots.txt',
        'https://www.aussportsbetting.com/data/historical-nbl-results-and-odds-data/',
        'https://www.aussportsbetting.com/terms-of-use/', 'https://www.aussportsbetting.com/terms-and-conditions/'],
    'BetExplorer (historical odds pages)': ['https://www.betexplorer.com/robots.txt', 'https://www.betexplorer.com/terms-of-use/'],
}
WORDS = re.compile(r'scrap|crawl|robot|automat|spider|download|reproduc|redistribut|commercial|personal use|'
                   r'data mining|harvest|copy|licen[cs]e|permission|xlsx|excel|\.xls', re.I)


def text_of(html):
    html = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', html)
    html = re.sub(r'(?s)<[^>]+>', ' ', html)
    html = re.sub(r'&nbsp;|&#160;', ' ', html)
    return re.sub(r'\s+', ' ', html)


def main():
    for site, urls in PAGES.items():
        print(f'## {site}\n')
        for url in urls:
            try:
                r = requests.get(url, headers={'User-Agent': UA}, timeout=30)
            except requests.RequestException as e:
                print(f'**{url}**: no answer ({type(e).__name__})\n')
                continue
            print(f'**{url}**: HTTP {r.status_code}\n')
            if r.status_code != 200:
                continue
            if url.endswith('robots.txt'):
                print('```\n' + r.text[:1500] + '\n```\n')
                continue
            sentences = re.split(r'(?<=[.!?])\s+', text_of(r.text))
            hits = [s.strip() for s in sentences if WORDS.search(s) and len(s) < 600]
            links = sorted(set(re.findall(r'href="([^"]+\.xlsx?)"', r.text)))
            for s in hits[:40]:
                print(f'- {s}')
            if links:
                print('\nSpreadsheet links on the page: ' + ', '.join(links))
            print()
            time.sleep(3)


if __name__ == '__main__':
    sys.exit(main())
