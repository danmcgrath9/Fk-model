"""Betwatch harness history joined onto Betfair's free files (18 Nov 2026, founder: "Option 3").

Betwatch (pulled by greyhound/betwatch.py into the Actions cache, never committed: own use only, never shared) adds
what Betfair's files do not carry: driver, trainer, barrier, race class, track condition, and TAB's price changes
with times. Betfair adds BSP, the result and three years more of each horse's history.

load_betwatch(dir) -> one row per Betwatch runner:
  bw_race, race (Betfair win market id as Betfair's files store it: the digits after "1."), horse (Betfair selection
  id), date, start, track, state, distance, class, track_condition, number, barrier, scratched, emergency, driver,
  trainer, bw_pos (finishing position from Betwatch's own results, where it can be read), tab_open (TAB's first
  recorded price), tab_open_hours (how long before the scheduled start), tab_last (TAB's last price before the
  start), tab_n (TAB price changes).
  TAB's "first" price is the first one Betwatch picked up that day (Betwatch, 13 Nov): usually near the open, not
  guaranteed to be it.

join(bf, bw) -> Betfair rows (hx_data.load) with the Betwatch columns added on (race, horse), plus a dict of counts
  saying how much joined. Nothing is guessed: an unmapped or unmatched runner keeps NaN.

add_people(df) -> point-in-time driver, trainer and barrier form, from earlier races only.
"""
import gzip, json, os, re
from datetime import datetime, timezone
import numpy as np, pandas as pd


def bf_market(x):
    """Betwatch's Betfair win market id ("1.234567890") as Betfair's files store it (234567890), or None."""
    if x is None:
        return None
    s = str(x).strip()
    if "." in s:
        a, b = s.split(".", 1)
        s = b if a == "1" else ""
    return int(s) if s.isdigit() else None


def as_int(x):
    try:
        return int(str(x).strip())
    except (TypeError, ValueError):
        return None


def positions(results):
    """Runner number -> finishing position from Betwatch's `results`. Read: a list per position of runner numbers
    ([[3], [5, 7], [1]]: a dead heat for second), a flat list of numbers ([3, 5, 1]), or a string "3,5,1" / "3-5-1".
    Anything else returns {} (counted by the caller, never guessed)."""
    if results is None:
        return {}
    if isinstance(results, str):
        parts = [p for p in re.split(r"[,\-\s/]+", results.strip()) if p]
        return {n: i + 1 for i, p in enumerate(parts) if (n := as_int(p)) is not None}
    if isinstance(results, list):
        out = {}
        for i, pos in enumerate(results):
            for n in (pos if isinstance(pos, list) else [pos]):
                n = as_int(n)
                if n is None:
                    return {}
                out.setdefault(n, i + 1)
        return out
    return {}


def _ts(s):
    """An ISO time as an aware Timestamp (UTC when no zone is given), or NaT. Plain datetime parsing: pd.to_datetime
    per price change made the join take 16 minutes on four years of flucs."""
    if not s:
        return pd.NaT
    try:
        t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return pd.NaT
    return pd.Timestamp(t if t.tzinfo else t.replace(tzinfo=timezone.utc))


def runner_rows(race):
    """One compacted Betwatch race (greyhound/betwatch.compact) as runner rows."""
    st = _ts(race.get("start"))
    pos = positions(race.get("results"))
    out = []
    for ru in race.get("runners") or []:
        tab = ((ru.get("books") or {}).get("Tab") or {}).get("flucs") or []
        before = [f for f in tab if pd.isna(st) or _ts(f[1]) <= st]
        o_at = _ts(tab[0][1]) if tab else pd.NaT
        num = as_int(ru.get("number"))
        out.append({
            "bw_race": race.get("id"), "race_bw_bf": bf_market(race.get("betfair_win")),
            "horse_bw": as_int(ru.get("betfair_id")), "bw_date": race.get("date"), "bw_start": st,
            "bw_track": (race.get("track") or "").upper(), "bw_state": race.get("location"),
            "bw_distance": as_int(race.get("distance")), "class": race.get("class"),
            "track_condition": race.get("track_condition"), "number": num, "barrier": as_int(ru.get("barrier")),
            "scratched": bool(ru.get("scratched")), "emergency": bool(ru.get("emergency")),
            "driver": (ru.get("rider") or "").strip().upper() or None,
            "trainer": (ru.get("trainer") or "").strip().upper() or None,
            "bw_pos": pos.get(num) if pos else np.nan, "bw_has_results": bool(pos),
            "tab_open": tab[0][0] if tab else np.nan,
            "tab_open_hours": (st - o_at).total_seconds() / 3600 if tab and not pd.isna(st) else np.nan,
            "tab_last": before[-1][0] if before else np.nan, "tab_n": len(tab)})
    return out


def load_betwatch(d):
    rows, months, incomplete = [], 0, []
    for name in sorted(os.listdir(d)):
        if not (name.startswith("betwatch_") and name.endswith(".json.gz")):
            continue
        m = json.load(gzip.open(os.path.join(d, name), "rt", encoding="utf-8"))
        months += 1
        if not m.get("complete"):
            incomplete.append(m.get("month"))
        for r in m.get("races") or []:
            rows += runner_rows(r)
    bw = pd.DataFrame(rows)
    bw.attrs.update(months=months, incomplete=incomplete)
    return bw


def join(bf, bw):
    """Betwatch columns onto Betfair rows by (race, horse). Returns (frame, counts)."""
    live = bw[~bw.scratched]
    c = {"bw_races": bw.bw_race.nunique(), "bw_runners": len(live),
         "bw_races_mapped": live.loc[live.race_bw_bf.notna(), "bw_race"].nunique(),
         "bw_runners_with_bf_id": int(live.horse_bw.notna().sum()),
         "bw_races_with_results": live.loc[live.bw_has_results, "bw_race"].nunique()}
    k = live[live.race_bw_bf.notna() & live.horse_bw.notna()].copy()
    k["race"], k["horse"] = k.race_bw_bf.astype("int64"), k.horse_bw.astype("int64")
    k = k.drop_duplicates(["race", "horse"])
    cols = ["bw_race", "class", "track_condition", "number", "barrier", "emergency", "driver", "trainer", "bw_pos",
            "bw_has_results", "tab_open", "tab_open_hours", "tab_last", "tab_n"]
    df = bf.merge(k[["race", "horse"] + cols], on=["race", "horse"], how="left")
    span = (bf.date >= pd.Timestamp(bw.bw_date.min())) & (bf.date <= pd.Timestamp(bw.bw_date.max()))
    au = span & (bf.STATE_CODE != "NZ")
    c["bf_au_runners_in_span"] = int(au.sum())
    c["bf_au_runners_joined"] = int((au & df.bw_race.notna()).sum())
    c["bf_au_races_in_span"] = int(bf.loc[au, "race"].nunique())
    c["bf_au_races_joined"] = int(df.loc[au & df.bw_race.notna(), "race"].nunique())
    j = df[df.bw_race.notna() & df.bw_has_results.fillna(False).astype(bool)]
    c["winner_checks"] = int((j.won == 1).sum())
    c["winner_agree"] = int(((j.won == 1) & (j.bw_pos == 1)).sum())
    c["tab_number_agree"] = float((df.number == df.TAB_NUMBER)[df.bw_race.notna()].mean())
    return df, c


def _shrunk_form(df, key, k_resid=30):
    """For each row, from earlier rows with the same key only: runs, wins, and wins against what BSP expected, shrunk
    toward zero with k_resid pseudo-runs (a driver with 3 drives says almost nothing)."""
    o = df[df[key].notna()].sort_values(["start", "race"])
    g = o.groupby(key, sort=False)
    runs = g.cumcount()
    wins = g.won.cumsum() - o.won
    resid = g.perf.transform(lambda x: x.fillna(0).cumsum()) - o.perf.fillna(0)
    out = pd.DataFrame(index=o.index)
    out[f"{key}_runs"] = runs
    out[f"{key}_win_rate"] = (wins + 1) / (runs + 10)
    out[f"{key}_resid"] = resid / (runs + k_resid)
    return out


def add_people(df):
    """Driver, trainer and driver x trainer form; whether the horse's driver changed since its last start; barrier
    form at this track and gait. Earlier races only (cumulative sums less the row itself, in start order)."""
    df = df.copy()
    for c in ("barrier", "number", "tab_open", "tab_last", "tab_open_hours", "tab_n", "bw_pos"):
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["emergency"] = df.emergency.map({True: 1.0, False: 0.0}) if "emergency" in df else np.nan   # not joined: NaN
    df["perf"] = (df.won - df.p_bsp).where(df.p_bsp.notna())
    df["combo"] = (df.driver + " | " + df.trainer).where(df.driver.notna() & df.trainer.notna())
    df["dr_track"] = (df.driver + " | " + df.TRACK).where(df.driver.notna())
    for key in ("driver", "trainer", "combo", "dr_track"):
        f = _shrunk_form(df, key)
        for c in f:
            df[c] = f[c]
    o = df.sort_values(["horse", "start", "race"])
    prev_driver = o.groupby("horse", sort=False).driver.shift(1)
    ch = (o.driver != prev_driver).astype(float).where(o.driver.notna() & prev_driver.notna())
    df.loc[o.index, "driver_change"] = ch
    df.loc[o.index, "prev_driver_resid"] = o.groupby("horse", sort=False).driver_resid.shift(1)
    df["driver_up"] = df.driver_resid - df.prev_driver_resid
    df["barrier_rel"] = df.barrier / df.field.where(df.field > 0)
    o = df[df.barrier.notna()].sort_values(["start", "race"])
    k = o.groupby([o.TRACK, o.trot, o.barrier], sort=False)
    runs = k.cumcount()
    wins = k.won.cumsum() - o.won
    exp = k.p_bsp.transform(lambda x: x.fillna(0).cumsum()) - o.p_bsp.fillna(0)
    df.loc[o.index, "bar_ae"] = (wins + 5) / (exp + 5)
    df.loc[o.index, "bar_runs"] = runs
    cls = df["class"].astype("string")
    df["class_num"] = pd.to_numeric(cls.str.extract(r"(\d+)", expand=False), errors="coerce")
    top = cls.value_counts().head(60).index
    df["class_cat"] = cls.where(cls.isin(top), "other").fillna("none")
    df["cond"] = df.track_condition.astype("string").str.split().str[0].str.upper().fillna("none")
    # TAB's first price as a chance, renormalised over the runners that have one (only where every runner has one)
    inv = (1 / df.tab_open).where(df.tab_open > 1)
    full = inv.notna().groupby(df.race).transform("all")
    df["p_tab_open"] = (inv / inv.groupby(df.race).transform("sum")).where(full)
    inv = (1 / df.tab_last).where(df.tab_last > 1)
    full = inv.notna().groupby(df.race).transform("all")
    df["p_tab_last"] = (inv / inv.groupby(df.race).transform("sum")).where(full)
    return df


PEOPLE = ["driver_runs", "driver_win_rate", "driver_resid", "trainer_runs", "trainer_win_rate", "trainer_resid",
          "combo_runs", "combo_resid", "dr_track_runs", "dr_track_resid", "driver_change", "driver_up", "barrier",
          "barrier_rel", "bar_ae", "bar_runs", "class_num", "emergency"]
PEOPLE_CATS = ["class_cat", "cond"]
