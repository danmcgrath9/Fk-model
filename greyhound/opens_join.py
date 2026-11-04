"""Join our recorded opening prices (greyhound/opens.py rows, written by betmatic/greyhound_opens.py) to the Topaz
runs table, for Benter's stage 2 with the open (MODELS_RESEARCH.md item 1, the largest expected gain on the list).

A run is matched on the Sydney date, the venue (BetMatic's competition name and Topaz's track name, both reduced to
letters, with the two names a track goes by folded together), the race number and the rug number (BetMatic's
selection number; the box when no rug is recorded). ONLY A KNOWN OPEN COUNTS: a row whose `open_known` is false is a
later price that happened to be the first we saw (the gallops lesson in opens.py), and it is dropped here, so
`open_price` is NaN rather than wrong. The market chance `p_open` exists only for a race where every runner carries
an open, because a stage-2 blend needs the whole book. Pure: no network, no clock.
"""
from __future__ import annotations

import csv
import gzip
from pathlib import Path

import numpy as np
import pandas as pd

from greyhound.opens import norm

ALIASES = {"MEADOWS": "THEMEADOWS", "SANDOWN": "SANDOWNPARK"}


def venue_key(name) -> str:
    k = norm(name)
    return ALIASES.get(k, k)


def load_opens(directory) -> pd.DataFrame:
    rows = []
    for f in sorted(Path(directory).glob("opens-*.csv.gz")):
        with gzip.open(f, "rt", encoding="utf-8", newline="") as fh:
            rows += list(csv.DictReader(fh))
    return pd.DataFrame(rows)


def open_prices(opens: pd.DataFrame, bookie: str = "TAB") -> pd.DataFrame:
    """One row per (date, venue_key, race, runner) with the bookmaker's KNOWN opening price; nothing else."""
    if not len(opens):
        return pd.DataFrame(columns=["date", "venue_key", "race", "runner", "open_price"])
    o = opens[opens.bookie.astype(str).str.upper() == bookie.upper()].copy()
    known = o.open_known.map(lambda v: str(v).strip().lower() == "true")
    price = pd.to_numeric(o.first_price, errors="coerce")
    o = o[known & (price > 1)].assign(open_price=price[known & (price > 1)])
    out = pd.DataFrame({"date": o.date.astype(str), "venue_key": o.venue.map(venue_key),
                        "race": pd.to_numeric(o.race, errors="coerce").astype("Int64"),
                        "runner": pd.to_numeric(o.runner, errors="coerce").astype("Int64"), "open_price": o.open_price})
    return out.dropna(subset=["race", "runner"]).drop_duplicates(["date", "venue_key", "race", "runner"], keep="first")


def join_opens(runs: pd.DataFrame, opens: pd.DataFrame, bookie: str = "TAB") -> tuple[pd.DataFrame, list[str]]:
    """Adds open_price (the known open, NaN where none) and p_open (the open's chance, normalised over the race, only
    when every runner in the race has an open). Needs date, track_name, race_number and rug or box on `runs`."""
    op = open_prices(opens, bookie)
    r = runs.copy()
    num = r.rug if "rug" in r else r.box
    num = num.where(num.notna(), r.box) if "rug" in r else num
    key = pd.DataFrame({"date": pd.to_datetime(r.date).dt.strftime("%Y-%m-%d"), "venue_key": r.track_name.map(venue_key),
                        "race": pd.to_numeric(r.race_number, errors="coerce").astype("Int64"),
                        "runner": pd.to_numeric(num, errors="coerce").astype("Int64")}, index=r.index)
    merged = key.merge(op, on=["date", "venue_key", "race", "runner"], how="left")
    r["open_price"] = merged.open_price.values.astype(float)
    inv = 1.0 / r.open_price
    full = r.open_price.notna().groupby(r.race_id).transform("all")
    r["p_open"] = np.where(full, inv / inv.groupby(r.race_id).transform("sum"), np.nan)
    return r, ["open_price", "p_open"]
