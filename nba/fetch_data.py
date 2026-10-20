"""Download the cdn.nba.com play-by-play seasons from shufinskiy/nba_data.

Free, open dataset (github.com/shufinskiy/nba_data). One tar.xz per season, ~15-20 MB
compressed, ~200 MB as CSV. Season 2024 means 2024/25.

    python nba/fetch_data.py 2020 2021 2022 2023 2024 2025
"""
from __future__ import annotations

import sys
import tarfile
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parent / "data" / "raw"
URL = "https://raw.githubusercontent.com/shufinskiy/nba_data/main/datasets/cdnnba_{season}.tar.xz"


def fetch(season: int) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    csv = RAW / f"cdnnba_{season}.csv"
    if csv.exists():
        return csv
    archive = RAW / f"cdnnba_{season}.tar.xz"
    if not archive.exists():
        urllib.request.urlretrieve(URL.format(season=season), archive)
    with tarfile.open(archive) as tar:
        tar.extractall(RAW, filter="data")
    if not csv.exists():
        raise FileNotFoundError(f"{archive} did not contain {csv.name}")
    return csv


if __name__ == "__main__":
    for s in sys.argv[1:] or ["2020", "2021", "2022", "2023", "2024", "2025"]:
        print(fetch(int(s)))
