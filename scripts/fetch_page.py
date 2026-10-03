"""Fetch a public web page and print its text (tables kept as rows), for reading reference pages
such as a bookmaker's published deduction schedule from a runner with open internet.

    python scripts/fetch_page.py URL [URL ...]
"""
from __future__ import annotations

import html
import re
import sys

import requests


def text(h: str) -> str:
    h = re.sub(r"(?is)<(script|style|noscript).*?</\1>", "", h)
    h = re.sub(r"(?i)</t[dh]>", " | ", h)
    h = re.sub(r"(?i)<(br|/tr|/p|/li|/h\d|/div)[^>]*>", "\n", h)
    t = html.unescape(re.sub(r"<[^>]+>", "", h))
    return "\n".join(l.strip() for l in t.splitlines() if l.strip())


for url in sys.argv[1:]:
    print(f"## {url}\n")
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        print(f"status {r.status_code}, {len(r.text)} bytes\n")
        print(text(r.text)[:40000])
    except Exception as e:  # report and carry on to the next URL
        print(f"failed: {e}")
    print()
