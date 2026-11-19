"""Racing Queensland's harness sectionals as per-horse speed records (19 Nov 2026).

parse_file(path) -> one row per runner of one meeting file (YYYYMMDD_Track_H.csv): date and track from the file name,
race number (the file's own column where it has one, else counted from the rows that separate races: rows with no
horse), finishing rank, TAB number, horse, and per section the time in seconds and the metres actually travelled.
Times are written "m:ss.ss" or "ss.ss"; both become seconds.

run_features(runs) -> per run: speeds in metres a second (distance travelled / time) for the last half, the last
quarter, the first half and the lead time; top speed; each speed against the race's mean for that section; metres
travelled beyond the shortest route anyone took in the race (how wide it raced); position at the first and third
quarter as a share of the field.

horse_history(runs) -> each horse's record from its EARLIER sectional runs only (shift within the horse's own
date-and-race-ordered runs): last value, smoothed value (EWMA, alpha 0.4) and best of five for the speeds and
relatives, and runs with sectionals. Keyed by horse name (Racing Queensland gives no id) and joined to Betwatch by
date, track, race number and name.
"""
import io, os, re
import numpy as np, pandas as pd

SECTIONS = {"lead": "LeadTime", "first_half": "FirstHalf", "mid_half": "MiddleHalf", "last_half": "LastHalf",
            "q4": "4thQuarter", "last_mile": "LastMile"}
REL = ["v_last_half", "v_q4", "v_first_half", "v_lead", "top_speed"]


def secs(v):
    """'1:58.34' -> 118.34, '27.85' -> 27.85; anything else NaN."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return np.nan
    s = str(v).strip()
    m = re.fullmatch(r"(\d+):(\d{1,2}(?:\.\d+)?)", s)
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    return float(s) if re.fullmatch(r"\d+(?:\.\d+)?", s) else np.nan   # '+9' (a margin) is not a time


def norm_track(t):
    return re.sub(r"[^A-Z]", "", str(t).upper())


def norm_name(n):
    return re.sub(r"[^A-Z0-9]", "", str(n).upper()) if isinstance(n, str) and n.strip() else None


def parse_file(path):
    base = os.path.basename(path)
    m = re.match(r"(\d{8})_(.+)_H\.csv$", base)
    if not m:
        return pd.DataFrame()
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    head = next((i for i, l in enumerate(lines) if "Horse" in l.split(",")), None)   # some files open with a title
    if head is None:
        return pd.DataFrame()
    try:
        df = pd.read_csv(io.StringIO("\n".join(lines[head:])), dtype=str)
    except pd.errors.ParserError:
        return pd.DataFrame()
    df.columns = [c.strip() for c in df.columns]
    if "Horse" not in df:
        return pd.DataFrame()
    sep = df.Horse.isna() | (df.Horse.astype(str).str.strip() == "")
    counted = sep.cumsum()                                   # each separator row opens the next race
    if not sep.iloc[0]:
        counted = counted + 1
    race = pd.to_numeric(df["Race Number"], errors="coerce") if "Race Number" in df else pd.Series(np.nan, df.index)
    out = pd.DataFrame({"date": pd.Timestamp(m.group(1)), "track": norm_track(m.group(2).replace("_", " ")),
                        "race_number": race.fillna(counted).astype(float), "rank": pd.to_numeric(df.get("Rank"),
                        errors="coerce"), "tab": pd.to_numeric(df.get("TAB"), errors="coerce"),
                        "name": df.Horse.map(norm_name),
                        "top_speed": pd.to_numeric(df.get("TopSpeed"), errors="coerce"),
                        "dist_travelled": pd.to_numeric(df.get("DistanceTravelled"), errors="coerce"),
                        "q1_rank": pd.to_numeric(df.get("1stQuarterRANK"), errors="coerce"),
                        "q3_rank": pd.to_numeric(df.get("3rdQuarterRANK"), errors="coerce")})
    for k, col in SECTIONS.items():
        t = df[f"{col}ST"].map(secs) if f"{col}ST" in df else pd.Series(np.nan, df.index)
        d = pd.to_numeric(df[f"{col}DT"], errors="coerce") if f"{col}DT" in df else pd.Series(np.nan, df.index)
        out[f"t_{k}"], out[f"d_{k}"] = t, d
    return out[~sep & out.name.notna()].reset_index(drop=True)


def load_dir(d):
    names = [f for f in sorted(os.listdir(d)) if f.endswith(".csv")]
    parts = [parse_file(os.path.join(d, f)) for f in names]
    print(f"RQ files read: {sum(1 for p in parts if len(p)):,} of {len(names):,} (the rest unreadable or empty)")
    parts = [p for p in parts if len(p)]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def run_features(r):
    r = r.copy()
    key = ["date", "track", "race_number"]
    for k in ("last_half", "q4", "first_half", "lead"):
        v = (r[f"d_{k}"] / r[f"t_{k}"]).where((r[f"t_{k}"] > 0) & (r[f"d_{k}"] > 0))
        r[f"v_{k}"] = v.where(v.between(5, 25))              # 18 to 90 km/h: anything else is a misread
    r["top_speed"] = r.top_speed.where(r.top_speed.between(20, 80))
    g = r.groupby(key)
    for c in REL:
        r[f"{c}_rel"] = r[c] - g[c].transform("mean")
    r["field_s"] = g.name.transform("size")
    r["extra_dist"] = r.dist_travelled - g.dist_travelled.transform("min")
    r["q1_pos"] = r.q1_rank / r.field_s
    r["q3_pos"] = r.q3_rank / r.field_s
    return r


RUN_FEATS = REL + [f"{c}_rel" for c in REL] + ["extra_dist", "q1_pos", "q3_pos"]


def horse_history(r):
    """Each horse's sectional record from its earlier runs only."""
    r = r.sort_values(["name", "date", "race_number"]).copy()
    g = r.groupby("name", sort=False)
    out = pd.DataFrame(index=r.index)
    out["sec_runs"] = g.cumcount()
    for c in RUN_FEATS:
        out[f"sec_last_{c}"] = g[c].shift(1)
        out[f"sec_ewm_{c}"] = g[c].transform(lambda x: x.shift(1).ewm(alpha=0.4, ignore_na=True).mean())
    for c in ("v_last_half", "v_q4", "v_lead", "top_speed", "v_last_half_rel", "v_lead_rel"):
        out[f"sec_best5_{c}"] = g[c].transform(lambda x: x.shift(1).rolling(5, min_periods=1).max())
    out["sec_days"] = (r.date - g.date.shift(1)).dt.days
    keep = r[["date", "track", "race_number", "name", "rank", "tab"]]
    return pd.concat([keep, out], axis=1)


SEC_FEATS = (["sec_runs", "sec_days"] + [f"sec_last_{c}" for c in RUN_FEATS] + [f"sec_ewm_{c}" for c in RUN_FEATS]
             + [f"sec_best5_{c}" for c in ("v_last_half", "v_q4", "v_lead", "top_speed", "v_last_half_rel",
                                           "v_lead_rel")])
