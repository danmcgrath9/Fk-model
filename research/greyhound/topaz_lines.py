"""The running line, and today's draw against it (18 Nov 2026, founder: "if it draws 1, it can't win today, but was box
6 in that price ... make it as complicated as possible")

Every input here is known the night before: each is built from the dog's runs on EARLIER days (the same
end-of-previous-day rule as the rest of the form), and today's draw.

Per run, from Topaz (every run) and Isolynx (the tracked tracks):
  - the stewards' comment, split into its codes (letters only, so "CRD1" is "CRD"): every code on at least 0.5% of
    runs, up to MAX_TOKENS; the share of the dog's last 10 runs carrying each (tk_*), and how many codes a run carried
  - GRV's run-line code and jump code: the share of the last 10 runs with each (rlc_*, jpc_*)
  - the run-line code as metres from the rail: each code's mean distance from the rail on tracked runs, against
    dogs drawn in the same box at the same track and distance, from runs before SINCE only (line_code_m5, _m10)
  - on tracked runs, the dog's own distance from the rail against its box: on average, at the jump, at its closest,
    and at 100, 200 and 300 m where Isolynx gives it (iso_line_*, last 3 and 5 tracked runs)
  - where it settled at the first split against the box it came from (early_vs_box)

Today's race, from those and the draw (the occupied boxes in order; a vacant box is room):
  - the dog's line: tracked where it has 2 or more tracked runs, else its run-line code's metres
  - line rank against box rank (clash; positive = it wants to run wider than it is drawn, the founder's wide runner
    in box 1), and the same as a share of the field
  - the dogs either side: their lines and early speed against its own, the gap to them (vacant boxes), and whether
    they will come across it (converge_in, converge_out, squeeze)
  - how many quicker dogs drawn inside it run wider (crossers_in) and drawn outside it run closer to the rail
    (crossers_out), and how many quicker dogs want its lane (contention)
  - a slow beginner's clash: its early-speed rank in the field times its clash
"""
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_v2 as V2             # noqa: E402

SINCE = "2025-02-01"              # the code-to-metres map is built only from runs before this
TOKEN_MIN_SHARE = 0.005
MAX_TOKENS = 40
CODE_MIN_SHARE = 0.005
CODE_MIN_TRACKED = 200
LANE = 0.75                       # metres: two dogs whose lines are this close want the same lane
WIDER = 0.5                       # metres: a dog this much wider (or closer) than another will cross it
SPEED = "split_rating_mean5"      # the early-speed rating the map already uses (higher is quicker)


def slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(s)).strip("_")


def comment_tokens(s: pd.Series) -> pd.Series:
    """Each comment's codes, letters only and upper case: 'SAW,CRD1' -> ['SAW', 'CRD']."""
    return s.fillna("").astype(str).str.upper().str.findall(r"[A-Z]+")


def frequent(lists: pd.Series, min_share: float, cap: int) -> list:
    """The items on at least min_share of rows (each row counted once), most common first, at most cap."""
    sets = lists.map(lambda v: sorted(set(v)) if isinstance(v, list) else [])
    share = sets.explode().dropna().value_counts() / max(len(sets), 1)
    return list(share[share >= min_share].index[:cap])


def code_metres(runs: pd.DataFrame, codes: pd.Series, resid: pd.Series, before) -> dict:
    """Each run-line code's mean box-adjusted distance from the rail, on tracked runs before `before`, where at least
    CODE_MIN_TRACKED tracked runs carry it."""
    ok = resid.notna() & codes.ne("") & (runs.date < pd.Timestamp(before))
    g = resid[ok].groupby(codes[ok])
    n, m = g.size(), g.mean()
    return {c: float(m[c]) for c in m.index if n[c] >= CODE_MIN_TRACKED}


def iso_residuals(t: pd.DataFrame, before) -> pd.DataFrame:
    """Tracked runs with each rail distance against the median for dogs drawn in the same box at the same venue and
    distance, the medians from runs before `before` (a code that is stable across time, so later runs can use it)."""
    t = t.copy()
    early = t.date < pd.Timestamp(before)
    keys = ["venue", "distance", "box"]
    for m in [c for c in ("avg_rail", "jump_rail", "min_rail", "rail100", "rail200", "rail300") if c in t]:
        v = pd.to_numeric(t[m], errors="coerce")
        med = v[early].groupby([t.loc[early, k] for k in keys]).median().rename(f"_med_{m}")
        t = t.join(med, on=keys)
        t[f"r_{m}"] = v - t[f"_med_{m}"]
    return t


def tracked_history(df: pd.DataFrame, t: pd.DataFrame, cols: list) -> dict:
    """Each residual's mean over the dog's last 3 and last 5 tracked runs on EARLIER days, onto df's rows."""
    from greyhound.ratings import _asof
    out = {}
    t = t.dropna(subset=["date"]).copy()
    t["dog"] = t.dog.astype("Int64").astype(str)
    t = t.sort_values(["dog", "date"])
    for c in cols:
        x = t.dropna(subset=[c])
        if not len(x):
            continue
        gd = x.groupby("dog")[c]
        x = x.assign(_m3=gd.rolling(3, min_periods=1).mean().reset_index(level=0, drop=True),
                     _m5=gd.rolling(5, min_periods=1).mean().reset_index(level=0, drop=True))
        day = x.groupby(["dog", "date"])[["_m3", "_m5"]].last().reset_index()
        name = c.replace("r_", "iso_line_")
        out[f"{name}_m3"] = _asof(df[["dog", "date"]], day, ["dog"], "_m3")
        out[f"{name}_m5"] = _asof(df[["dog", "date"]], day, ["dog"], "_m5")
    cnt = t.dropna(subset=["r_avg_rail"]).groupby(["dog", "date"]).size().groupby(level=0).cumsum().reset_index(name="_n") \
        if "r_avg_rail" in t else None
    if cnt is not None and len(cnt):
        out["iso_line_runs"] = _asof(df[["dog", "date"]], cnt, ["dog"], "_n")
    return out


def race_map(df: pd.DataFrame) -> pd.DataFrame:
    """Today's draw against the lines: one row per runner, aligned with df."""
    keep = ["race_id", "box", "line_any", SPEED]
    x = df[keep].copy()
    x["_i"] = np.arange(len(df))
    x = x.sort_values(["race_id", "box"])
    g = x.groupby("race_id")
    n = g.box.transform("size").astype(float)
    x["box_rank"] = g.box.rank(method="first")
    x["line_rank"] = g.line_any.rank(method="average")
    x["speed_rank"] = g[SPEED].rank(ascending=False, method="average")
    x["clash"] = x.line_rank - x.box_rank
    x["clash_share"] = x.clash / (n - 1).clip(lower=1)
    for side, k in (("in", 1), ("out", -1)):
        x[f"nb_{side}_line"] = g.line_any.shift(k)
        x[f"nb_{side}_speed"] = g[SPEED].shift(k) - x[SPEED]
        nb_box = g.box.shift(k)
        x[f"nb_{side}_gap"] = (x.box - nb_box) * k
    x["nb_in_gap"] = x.nb_in_gap.fillna(x.box)                    # the rail inside the innermost dog
    x["nb_out_gap"] = x.nb_out_gap.fillna(9 - x.box)              # room outside the outermost
    x["converge_in"] = x.nb_in_line - x.line_any                  # the inside dog runs wider: it comes out across
    x["converge_out"] = x.line_any - x.nb_out_line                # the outside dog runs closer: it comes in across
    pos = lambda v: v.clip(lower=0).fillna(0)                    # noqa: E731
    x["squeeze"] = (pos(x.converge_in) * (x.nb_in_speed.fillna(-1) >= 0) / x.nb_in_gap.clip(lower=1)
                    + pos(x.converge_out) * (x.nb_out_speed.fillna(-1) >= 0) / x.nb_out_gap.clip(lower=1))
    x["slow_clash"] = (x.speed_rank / n) * x.clash.clip(lower=0)
    ci, co, ct = np.full(len(x), np.nan), np.full(len(x), np.nan), np.full(len(x), np.nan)
    b, ln, sp, rid = x.box.values, x.line_any.values, x[SPEED].values, x.race_id.values
    starts = np.r_[0, np.flatnonzero(rid[1:] != rid[:-1]) + 1, len(x)]
    for a, z in zip(starts[:-1], starts[1:]):
        bb, ll, ss = b[a:z], ln[a:z], sp[a:z]
        for j in range(z - a):
            if np.isnan(ll[j]) or np.isnan(ss[j]):
                continue
            quick = ss > ss[j]
            ci[a + j] = np.sum((bb < bb[j]) & quick & (ll > ll[j] + WIDER))
            co[a + j] = np.sum((bb > bb[j]) & quick & (ll < ll[j] - WIDER))
            ct[a + j] = np.sum(quick & (np.abs(ll - ll[j]) < LANE))
    x["crossers_in"], x["crossers_out"], x["contention"] = ci, co, ct
    cols = ["box_rank", "line_rank", "speed_rank", "clash", "clash_share", "nb_in_line", "nb_out_line",
            "nb_in_speed", "nb_out_speed", "nb_in_gap", "nb_out_gap", "converge_in", "converge_out", "squeeze",
            "slow_clash", "crossers_in", "crossers_out", "contention"]
    return x.sort_values("_i")[cols].reset_index(drop=True).set_index(df.index)


def add_lines(df: pd.DataFrame, iso_table: pd.DataFrame = None, since: str = SINCE) -> tuple:
    """(df with the running-line inputs, their names, a note of what was found)."""
    feats, notes = [], []
    toks = comment_tokens(df.get("comment", pd.Series("", index=df.index)))
    top = frequent(toks, TOKEN_MIN_SHARE, MAX_TOKENS)
    notes.append(f"stewards' codes on at least {TOKEN_MIN_SHARE:.1%} of runs: {len(top)} "
                 f"({', '.join(top[:25])}{'...' if len(top) > 25 else ''}); a comment on {toks.map(len).gt(0).mean():.0%} of runs")
    sets = toks.map(set)
    for tok in top:
        df["_c"] = sets.map(lambda s, k=tok: float(k in s))
        df[f"tk_{slug(tok)}"] = V2.history_mean(df, "_c", 10)
        feats.append(f"tk_{slug(tok)}")
    df["_c"] = toks.map(len).astype(float)
    df["tk_count"] = V2.history_mean(df, "_c", 10)
    feats.append("tk_count")
    for col, pre in (("run_line", "rlc"), ("jump", "jpc")):
        if col not in df:
            notes.append(f"no {col} column")
            continue
        codes = df[col].fillna("").astype(str).str.strip().str.upper()
        share = codes[codes != ""].value_counts(normalize=True)
        keep = list(share[share >= CODE_MIN_SHARE].index)
        notes.append(f"{col} codes on at least {CODE_MIN_SHARE:.1%} of coded runs: "
                     + ", ".join(f"{c} {share[c]:.0%}" for c in keep[:15]) + f"; coded on {(codes != '').mean():.0%} of runs")
        for c in keep:
            df["_c"] = (codes == c).astype(float).where(codes != "")
            df[f"{pre}_{slug(c)}"] = V2.history_mean(df, "_c", 10)
            feats.append(f"{pre}_{slug(c)}")
    if "split_pos" in df:
        df["_c"] = pd.to_numeric(df.split_pos, errors="coerce") - df.box.astype(float)
        df["early_vs_box"] = V2.history_mean(df, "_c", 10)
        feats.append("early_vs_box")
    df["line_any"] = np.nan
    if iso_table is not None and len(iso_table):
        t = iso_residuals(iso_table, since)
        rcols = [c for c in t if c.startswith("r_")]
        hist = tracked_history(df, t, rcols)
        for k, v in hist.items():
            df[k] = v
            feats.append(k)
        cov = {c: float(t[c].notna().mean()) for c in rcols}
        notes.append("tracked runs' rail distances found: " + ", ".join(f"{c[2:]} {v:.0%}" for c, v in cov.items()))
        if "run_line" in df and "r_avg_rail" in t:
            # a dog runs once a day, so a tracked run joins its Topaz run by dog and date
            tt = t.assign(dog=t.dog.astype("Int64").astype(str), date=pd.to_datetime(t.date).dt.normalize())
            tt = tt[["dog", "date", "r_avg_rail"]].dropna().drop_duplicates(["dog", "date"], keep=False)
            j = df[["dog", "date"]].assign(_i=np.arange(len(df)), dog=df.dog.astype(str),
                                           date=pd.to_datetime(df.date).dt.normalize()).merge(
                tt, on=["dog", "date"], how="left").sort_values("_i")
            codes = df.run_line.fillna("").astype(str).str.strip().str.upper()
            cm = code_metres(df, codes, pd.Series(j.r_avg_rail.values, index=df.index), since)
            notes.append("run-line codes in metres from the rail against their box (tracked runs before "
                         f"{since}): " + ", ".join(f"{c} {v:+.2f} m" for c, v in sorted(cm.items(), key=lambda kv: kv[1])))
            df["_c"] = codes.map(cm).astype(float)
            df["line_code_m5"] = V2.history_mean(df, "_c", 5)
            df["line_code_m10"] = V2.history_mean(df, "_c", 10)
            feats += ["line_code_m5", "line_code_m10"]
            iso_ok = df.get("iso_line_runs", pd.Series(0, index=df.index)).fillna(0) >= 2
            df["line_any"] = np.where(iso_ok & df.get("iso_line_avg_rail_m5", pd.Series(np.nan, index=df.index)).notna(),
                                      df.get("iso_line_avg_rail_m5"), df.line_code_m10)
    feats.append("line_any")
    notes.append(f"a running line for {df.line_any.notna().mean():.0%} of runners")
    if SPEED in df:
        m = race_map(df)
        for c in m:
            df[f"lm_{c}"] = m[c].values
            feats.append(f"lm_{c}")
    df = df.drop(columns=[c for c in ("_c",) if c in df])
    return df, feats, "\n".join(notes)
