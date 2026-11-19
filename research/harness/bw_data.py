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
            "horse_bw": as_int(ru.get("betfair_id")), "horse_name": (ru.get("name") or "").strip().upper() or None,
            "bw_date": race.get("date"), "bw_start": st,
            "bw_track": (race.get("track") or "").upper(), "race_name": race.get("name"),
            "race_number": as_int(race.get("number")), "bw_state": race.get("location"),
            "bw_distance": as_int(race.get("distance")), "class": race.get("class"),
            "track_condition": race.get("track_condition"), "number": num, "barrier": as_int(ru.get("barrier")),
            "scratched": bool(ru.get("scratched")), "emergency": bool(ru.get("emergency")),
            "driver": (ru.get("rider") or "").strip().upper() or None,
            "trainer": (ru.get("trainer") or "").strip().upper() or None,
            "bw_pos": pos.get(num) if pos else np.nan, "bw_has_results": bool(pos),
            "tab_open": tab[0][0] if tab else np.nan,
            "tab_open_hours": (st - o_at).total_seconds() / 3600 if tab and not pd.isna(st) else np.nan,
            "tab_last": before[-1][0] if before else np.nan, "tab_n": len(tab),
            "tab_now": (((ru.get("books") or {}).get("Tab") or {}).get("last") or [None])[0]})
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
            "bw_has_results", "tab_open", "tab_open_hours", "tab_last", "tab_n", "horse_name", "race_number"] + [
            c for c in BWH if c in k]
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


def prior_totals(df, keys, cols):
    """Per row: how many rows with the same key, and the sums of `cols` over them, among races that STARTED EARLIER
    than this row's race. Totals are built per (key, start) first, so nothing from the same race, or from another
    race starting at the same moment, is ever counted. (Test 8's first run summed row by row in start order, and a
    key every runner in a race shares, such as Betwatch's harness barrier field, or a trainer with two runners in one
    race, then carried that race's own result into the rows sorted after the winner.)"""
    keys = [keys] if isinstance(keys, str) else list(keys)
    o = df[df[keys].notna().all(axis=1)]
    t = o.assign(_n=1, **{c: o[c].fillna(0) for c in cols}).groupby(keys + ["start"], sort=True)[["_n"] + cols].sum()
    before = t.groupby(level=list(range(len(keys))), sort=False).cumsum() - t     # strictly earlier starts only
    out = o[keys + ["start"]].join(before, on=keys + ["start"])
    return out.drop(columns=keys + ["start"]).rename(columns={"_n": "runs"})


def _shrunk_form(df, key, k_resid=30):
    """For each row, from earlier races with the same key only: runs, wins, and wins against what BSP expected, shrunk
    toward zero with k_resid pseudo-runs (a driver with 3 drives says almost nothing)."""
    t = prior_totals(df, key, ["won", "perf"])
    out = pd.DataFrame(index=t.index)
    out[f"{key}_runs"] = t.runs
    out[f"{key}_win_rate"] = (t.won + 1) / (t.runs + 10)
    out[f"{key}_resid"] = t.perf / (t.runs + k_resid)
    return out


def add_people(df):
    """Driver, trainer and driver x trainer form; whether the horse's driver changed since its last start; barrier
    form at this track and gait. Earlier races only: totals over races that started before this one (prior_totals)."""
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
    t = prior_totals(df, ["TRACK", "trot", "barrier"], ["won", "p_bsp"])
    df.loc[t.index, "bar_ae"] = (t.won + 5) / (t.p_bsp + 5)
    df.loc[t.index, "bar_runs"] = t.runs
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


# --- Test 9 (18 Nov 2026, founder: "a model that beats TAB without its prices, then if we price TAB in can we win") ---

BWH = ["bwh_runs", "bwh_days", "bwh_last_pos", "bwh_last_pos_rel", "bwh_pos_ewm", "bwh_win_rate", "bwh_place_rate",
       "bwh_last_tab_mr", "bwh_tab_mr_ewm", "bwh_tab_mr_best5", "bwh_tabperf_ewm", "bwh_last_move", "bwh_move_ewm",
       "bwh_class_change", "bwh_hcp_change", "handicap", "handicap_vs_min"]


def add_bw_history(bw):
    """Each horse's record from Betwatch alone, earlier races only (a horse is never in two races at once, so a shift
    within the horse's own start-ordered runs is strict). Covers every Betwatch race, including the ~11% Betfair's files
    lack. Keyed by Betfair selection id, or by name where Betwatch gives no id.
    - finishing positions: last, last as a share of the field, smoothed; win and top-three rates (shrunk);
    - PAST TAB prices: the horse's rating at TAB's last price before each earlier start, log(chance x field), last and
      smoothed and best of five; how it ran against that price (won minus chance), smoothed; how its TAB price moved
      from first to last in earlier races (log first / last: positive = it firmed), last and smoothed;
    - class change (the number in today's class against last start's) and handicap metres (Betwatch's harness
      'barrier' field: 0 for most, the same for the whole field in most races) against its last start and the race.
    No price from the race being priced is used."""
    b = bw[~bw.scratched].copy()
    b["hkey"] = b.horse_bw.map(lambda x: f"id{int(x)}" if pd.notna(x) else None)
    b["hkey"] = b.hkey.fillna(b.horse_name.map(lambda n: f"nm{n}" if n else None))
    b = b[b.hkey.notna() & b.bw_start.notna()].copy()
    b["field_bw"] = b.groupby("bw_race").bw_race.transform("size")
    b["pos_rel"] = b.bw_pos / b.field_bw
    b["won_bw"] = (b.bw_pos == 1).astype(float).where(b.bw_pos.notna())
    b["placed_bw"] = (b.bw_pos <= 3).astype(float).where(b.bw_pos.notna())
    inv = (1 / b.tab_last).where(b.tab_last > 1)
    full = inv.notna().groupby(b.bw_race).transform("all")
    b["p_tl"] = (inv / inv.groupby(b.bw_race).transform("sum")).where(full)
    b["tab_mr"] = np.log(b.p_tl * b.field_bw)
    b["tabperf"] = b.won_bw - b.p_tl
    b["move"] = np.log(b.tab_open / b.tab_last).where((b.tab_open > 1) & (b.tab_last > 1))
    b["class_num_bw"] = pd.to_numeric(b["class"].astype("string").str.extract(r"(\d+)", expand=False), errors="coerce")
    b = b.sort_values(["hkey", "bw_start", "bw_race"])
    g = b.groupby("hkey", sort=False)
    ewm = lambda c: g[c].transform(lambda x: x.shift(1).ewm(alpha=0.3, ignore_na=True).mean())
    b["bwh_runs"] = g.cumcount()
    b["bwh_days"] = (b.bw_start - g.bw_start.shift(1)).dt.total_seconds() / 86400
    b["bwh_last_pos"], b["bwh_last_pos_rel"] = g.bw_pos.shift(1), g.pos_rel.shift(1)
    b["bwh_pos_ewm"] = ewm("pos_rel")
    wins = g.won_bw.transform(lambda x: x.fillna(0).cumsum()) - b.won_bw.fillna(0)
    places = g.placed_bw.transform(lambda x: x.fillna(0).cumsum()) - b.placed_bw.fillna(0)
    b["bwh_win_rate"] = (wins + 0.1) / (b.bwh_runs + 1)
    b["bwh_place_rate"] = (places + 0.3) / (b.bwh_runs + 1)
    b["bwh_last_tab_mr"], b["bwh_tab_mr_ewm"] = g.tab_mr.shift(1), ewm("tab_mr")
    b["bwh_tab_mr_best5"] = g.tab_mr.transform(lambda x: x.shift(1).rolling(5, min_periods=1).max())
    b["bwh_tabperf_ewm"] = ewm("tabperf")
    b["bwh_last_move"], b["bwh_move_ewm"] = g.move.shift(1), ewm("move")
    b["bwh_class_change"] = b.class_num_bw - g.class_num_bw.shift(1)
    b["handicap"] = b.barrier
    b["bwh_hcp_change"] = b.barrier - g.barrier.shift(1)
    b["handicap_vs_min"] = b.barrier - b.groupby("bw_race").barrier.transform("min")
    out = bw.copy()
    for c in BWH:
        out.loc[b.index, c] = b[c]
    return out


def windowed_form(df, key, days):
    """Runs and wins for this key in the `days` before this race's start (earlier starts only), shrunk: a stable or
    driver in form now, which a career strike rate dilutes."""
    o = df[df[key].notna()]
    t = o.assign(_n=1, _w=o.won).groupby([key, "start"], sort=True)[["_n", "_w"]].sum().reset_index()
    t[["cn", "cw"]] = t.groupby(key, sort=False)[["_n", "_w"]].cumsum().to_numpy()
    res = []
    for _, gk in t.groupby(key, sort=False):
        st = gk.start.to_numpy()
        lo = np.searchsorted(st, st - np.timedelta64(days, "D"), side="left")   # first start inside the window
        cn, cw = gk.cn.to_numpy(), gk.cw.to_numpy()
        n0, w0 = np.where(lo > 0, cn[lo - 1], 0), np.where(lo > 0, cw[lo - 1], 0)
        res.append(pd.DataFrame({"n": cn - gk["_n"].to_numpy() - n0, "w": cw - gk["_w"].to_numpy() - w0},
                                index=gk.index))
    r = pd.concat(res)
    t["n"], t["w"] = r.n, r.w
    m = o[[key, "start"]].merge(t[[key, "start", "n", "w"]], on=[key, "start"], how="left")
    m.index = o.index
    return m.n, (m.w + 0.5) / (m.n + 5)


REL = ["driver_win_rate", "trainer_win_rate", "driver_resid", "trainer_resid", "mr_ewm", "p_place_ewm",
       "bwh_tab_mr_ewm", "bwh_pos_ewm", "bwh_win_rate", "bwh_place_rate", "trainer60_rate", "driver60_rate"]


def add_form_plus(df):
    """Recent stable and driver form, then every key rating against the race: minus the race's mean, and its rank (1 =
    best). A rating means most beside the ratings it races against."""
    df = df.copy()
    for key, name in (("trainer", "trainer60"), ("driver", "driver60")):
        n, r = windowed_form(df, key, 60)
        df[f"{name}_runs"], df[f"{name}_rate"] = n, r
    for c in REL:
        if c not in df:
            continue
        x = df[c].astype(float)
        df[f"{c}_vs_race"] = x - x.groupby(df.race).transform("mean")
        better_low = c == "bwh_pos_ewm"                     # a lower finishing share is better
        df[f"{c}_rank"] = x.groupby(df.race).rank(ascending=better_low, method="min")
    return df


FORM_PLUS = (BWH + ["trainer60_runs", "trainer60_rate", "driver60_runs", "driver60_rate"]
             + [f"{c}_vs_race" for c in REL] + [f"{c}_rank" for c in REL])
