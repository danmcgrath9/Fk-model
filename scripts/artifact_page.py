"""Turn a built report into a page body for hosting that wraps it in its own skeleton.

Keeps the title, the stylesheet, the embedded plotly.js and everything inside <body>;
drops the doctype, <html>, <head> and <body> wrappers. Nothing else changes, so the
hosted page is the report byte for byte where it matters.

    python scripts/artifact_page.py reports/2026-09-12-flemington.html out/flemington.html
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def to_body(html: str) -> str:
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    style = re.search(r"<style>.*?</style>", html, re.S)
    scripts = re.findall(r"<script>.*?</script>", html[: html.find("</head>")], re.S)
    body = re.search(r"<body>(.*)</body>", html, re.S)
    if not (title and style and body):
        raise SystemExit("not a report this script knows: no title, style or body")
    out = f"<title>{title.group(1)}</title>{style.group(0)}{''.join(scripts)}{body.group(1)}"
    # plotly.min.js carries one literal U+FFFD inside a regex (/\ufffd/g). Some hosts refuse a
    # file holding that character; the escaped form is the same regex.
    return out.replace("\ufffd", "\\uFFFD")


if __name__ == "__main__":
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(to_body(src.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"wrote {dst} ({dst.stat().st_size // 1024} KB)")
