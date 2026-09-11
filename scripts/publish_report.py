"""Upload reports/*.html to the private Supabase bucket and print phone links.

  python scripts/publish_report.py [--days 7] [--summary $GITHUB_STEP_SUMMARY]

Needs SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (the fk-model project's, never TrueK's).
Each file is uploaded to fk-reports/<file name> and a signed URL valid for --days is printed,
and appended as markdown to --summary when given (GitHub shows that on the run page).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests

BUCKET = "fk-reports"


def upload_and_sign(base_url: str, key: str, path: Path, days: int, session: requests.Session | None = None) -> str:
    s = session or requests.Session()
    headers = {"Authorization": f"Bearer {key}", "apikey": key}
    up = s.post(f"{base_url}/storage/v1/object/{BUCKET}/{path.name}", data=path.read_bytes(),
                headers={**headers, "Content-Type": "text/html; charset=utf-8", "x-upsert": "true"}, timeout=120)
    if up.status_code >= 300:
        raise RuntimeError(f"upload of {path.name} failed: HTTP {up.status_code} {up.text[:300]}")
    sg = s.post(f"{base_url}/storage/v1/object/sign/{BUCKET}/{path.name}", json={"expiresIn": days * 86400},
                headers=headers, timeout=60)
    if sg.status_code >= 300:
        raise RuntimeError(f"signing {path.name} failed: HTTP {sg.status_code} {sg.text[:300]}")
    signed = sg.json()["signedURL"]
    return f"{base_url}/storage/v1{signed}" if signed.startswith("/") else signed


def summary_markdown(links: list[tuple[str, str]], days: int, ledger_lines: list[str]) -> str:
    out = ["## Reports", ""]
    if links:
        out += [f"- [{name}]({url})" for name, url in links]
        out += ["", f"Links work for {days} days."]
    else:
        out.append("No report files were produced.")
    if ledger_lines:
        out += ["", "## Credits", "", "```", *ledger_lines, "```"]
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--dir", default=str(Path(__file__).resolve().parent.parent / "reports"))
    ap.add_argument("--summary", help="file to append markdown to (GitHub: $GITHUB_STEP_SUMMARY)")
    ap.add_argument("--ledger-lines", help="file whose lines go under a Credits heading")
    a = ap.parse_args()
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not base or not key:
        sys.exit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    files = sorted(Path(a.dir).glob("*.html"))
    links = []
    for f in files:
        url = upload_and_sign(base, key, f, a.days)
        links.append((f.name, url))
        print(f"{f.name}: {url}")
    ledger_lines = Path(a.ledger_lines).read_text().splitlines() if a.ledger_lines and Path(a.ledger_lines).exists() else []
    md = summary_markdown(links, a.days, ledger_lines)
    if a.summary:
        with open(a.summary, "a", encoding="utf-8") as fh:
            fh.write(md)
    else:
        print(md)


if __name__ == "__main__":
    main()
