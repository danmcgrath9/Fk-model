"""Racing Queensland's harness sectionals (19 Nov 2026, founder: "Just plug in").

Racing Queensland publishes a sectional CSV for every TAB harness meeting at
racingqueensland.com.au/industry/harness/harness-sectionals (Aug 2017 on; individual horse times, top speed, mile
rate, sectional times). Its Disclaimer and Copyright page (read 19 Nov 2026 through `fk read terms`): "The information
published on this website is intended to be used for personal use only and may not be used for commercial purposes
without the prior written consent of Racing Queensland", and, except as the Copyright Act permits, no part "may be
reproduced, re-used or redistributed for any purpose whatsoever, without the express prior written permission".
Our use is personal: the files live in this repository's Actions cache only, never in a commit, a release or an
artifact, and logs print counts and column names, never a horse or a time.

    python research/harness/rq_sectionals.py probe DIR        two files: column names, rows, dtypes
    python research/harness/rq_sectionals.py pull DIR [--max-minutes N]   every listed CSV not yet in DIR
"""
import argparse, io, os, re, sys, time
import urllib.request

BASE = "https://www.racingqueensland.com.au"
PAGE = BASE + "/industry/harness/harness-sectionals"
AGENT = "fk-model personal research (python urllib)"
PAUSE = 1.0


def get(url, tries=4):
    wait = 5
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:                       # noqa: BLE001 (retry any transport error, then stop loudly)
            if i == tries - 1:
                raise
            print(f"  retry {i + 1} after {type(e).__name__}, waiting {wait}s"); time.sleep(wait); wait *= 2


def listing():
    """Every CSV path on the page, newest first as listed: '/Sectional/YYYYMMDD_Track_H.csv'."""
    html = get(PAGE).decode("utf-8", "replace")
    return list(dict.fromkeys(re.findall(r"RacingFile\.ashx\?path=(/Sectional/[^\"'&<>\s]+?\.csv)", html)))


def fname(path):
    return path.rsplit("/", 1)[-1]


def probe(d):
    import pandas as pd
    os.makedirs(d, exist_ok=True)
    files = listing()
    years = {}
    for p in files:
        y = fname(p)[:4]; years[y] = years.get(y, 0) + 1
    print(f"# Racing Queensland harness sectionals: {len(files):,} CSV files listed\n")
    print("by year: " + ", ".join(f"{y} {n}" for y, n in sorted(years.items())) + "\n")
    for p in (files[0], files[len(files) // 2], files[-1]):
        raw = get(f"{BASE}/RacingFile.ashx?path={p}")
        df = pd.read_csv(io.BytesIO(raw))
        print(f"## a file from {fname(p)[:8]}: {len(df):,} rows, {df.shape[1]} columns, {len(raw):,} bytes\n")
        for c in df.columns:
            print(f"- {c}: {df[c].dtype}, {df[c].notna().mean():.0%} filled")
        print()
        time.sleep(PAUSE)
    return 0


def pull(d, max_minutes):
    os.makedirs(d, exist_ok=True)
    files = listing(); t0 = time.monotonic()
    have = set(os.listdir(d)); todo = [p for p in files if fname(p) not in have]
    print(f"# pull: {len(files):,} listed, {len(have):,} already held, {len(todo):,} to fetch")
    done = failed = 0
    for p in todo:
        if (time.monotonic() - t0) / 60 > max_minutes:
            print("time budget reached; the rest resumes next run"); break
        try:
            raw = get(f"{BASE}/RacingFile.ashx?path={p}")
        except Exception as e:                       # noqa: BLE001
            failed += 1; print(f"  failed {fname(p)[:8]}: {type(e).__name__}"); continue
        with open(os.path.join(d, fname(p)), "wb") as fh:
            fh.write(raw)
        done += 1
        if done % 200 == 0:
            print(f"  {done:,} fetched")
        time.sleep(PAUSE)
    print(f"fetched {done:,}, failed {failed}, now held {len(os.listdir(d)):,}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["probe", "pull"]); ap.add_argument("dir")
    ap.add_argument("--max-minutes", type=float, default=300)
    a = ap.parse_args()
    sys.exit(probe(a.dir) if a.mode == "probe" else pull(a.dir, a.max_minutes))
