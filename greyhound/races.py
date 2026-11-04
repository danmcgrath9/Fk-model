"""GRV's race records from the pull's races_<STATE>_<YYYY-MM>.json.gz: the analyst's tips and comment for the race,
which the bulk runs do not carry (4 Nov 2026; MODELS_RESEARCH.md item 5, "expert prices as inputs").

A tip is matched to a runner by dog id, by box number (a value from 1 to 8) or by dog name, whichever the record
uses; Test 15's compare says which. The features are legitimate for a bet at the open only because the preview,
tips included, is published the evening before (Test 15); the compare of 5 Nov says whether the tips are the same
after the race.
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd


def load_races(directory) -> pd.DataFrame:
    rows = []
    for f in sorted(Path(directory).glob("races_*_*.json.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for r in json.load(fh):
                if not isinstance(r, dict) or r.get("raceId") is None:
                    continue
                tips = [r.get(f"tip{i}") for i in range(1, 5)]
                rows.append({"race_id": r["raceId"], "tips": [t for t in tips if t not in (None, "", 0)],
                             "analyst_len": len(str(r.get("analystComment") or "").strip()),
                             "has_suggested": float(bool(str(r.get("suggestedBet") or "").strip()))})
    t = pd.DataFrame(rows, columns=["race_id", "tips", "analyst_len", "has_suggested"])
    return t.drop_duplicates("race_id", keep="last").reset_index(drop=True)


def _matches(tip, dog, box, name) -> bool:
    t = str(tip).strip()
    if t == str(dog):
        return True
    if t.isdigit() and 1 <= int(t) <= 8 and int(t) == box:
        return True
    return t.upper() == str(name or "").strip().upper() if not t.isdigit() else False


def tip_features(df: pd.DataFrame, races: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Per runner: tip_rank (1-4 for the analyst's first to fourth tip, 0 for a runner in a tipped race that was not
    tipped, NaN for a race with no tips record), race_tips (how many tips the race carries), analyst_len,
    has_suggested. Nothing from the runner's own result."""
    r = races.set_index("race_id")
    tips = df.race_id.map(r.tips) if len(r) else pd.Series([np.nan] * len(df), index=df.index)
    rank = np.full(len(df), np.nan)
    n_tips = np.full(len(df), np.nan)
    name = df.dog_name.values if "dog_name" in df else [None] * len(df)
    for i, (ts, dog, box) in enumerate(zip(tips.values, df.dog.values, df.box.values)):
        if not isinstance(ts, list):
            continue
        n_tips[i] = len(ts)
        rank[i] = 0.0
        for k, t in enumerate(ts, 1):
            if _matches(t, dog, box, name[i]):
                rank[i] = float(k)
                break
    out = df.copy()
    out["tip_rank"] = rank
    out["race_tips"] = n_tips
    out["analyst_len"] = df.race_id.map(r.analyst_len) if len(r) else np.nan
    out["has_suggested"] = df.race_id.map(r.has_suggested) if len(r) else np.nan
    out["tip_top"] = (out.tip_rank == 1).astype(float).where(out.tip_rank.notna())
    return out, ["tip_rank", "race_tips", "analyst_len", "has_suggested", "tip_top"]
