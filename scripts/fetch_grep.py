"""Fetch a public URL and print every match of a regex in it, with a little context, for finding the data endpoint a
web app calls (16 Nov 2026: the official Victorian deductions app's API).

    python scripts/fetch_grep.py URL REGEX [CONTEXT_CHARS]
"""
from __future__ import annotations

import re
import sys

import requests

url, rx = sys.argv[1], sys.argv[2]
ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 60
r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
print(f"## {url}\nstatus {r.status_code}, {len(r.text)} bytes\n")
seen = set()
for m in re.finditer(rx, r.text):
    s = r.text[max(0, m.start() - ctx): m.end() + ctx].replace("\n", " ")
    if m.group(0) in seen:
        continue
    seen.add(m.group(0))
    print(f"{m.group(0)}  ::  {s}")
