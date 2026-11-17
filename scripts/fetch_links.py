"""Fetch a public web page and print every link and frame source on it (href, src, data-src), optionally only those
containing a word, for finding where a page loads its data from (16 Nov 2026: Racing Victoria's deductions table).

    python scripts/fetch_links.py URL [WORD]
"""
from __future__ import annotations

import html
import re
import sys

import requests

url = sys.argv[1]
word = sys.argv[2].lower() if len(sys.argv) > 2 else ""
r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
print(f"## {url}\nstatus {r.status_code}, {len(r.text)} bytes\n")
seen = set()
for m in re.finditer(r'(?i)(href|src|data-src)\s*=\s*["\']([^"\']+)["\']', r.text):
    u = html.unescape(m.group(2))
    if u in seen or (word and word not in u.lower()):
        continue
    seen.add(u)
    print(m.group(1), u)
for m in re.finditer(r'(?i)<iframe[^>]*>', r.text):
    print("IFRAME", m.group(0)[:300])
