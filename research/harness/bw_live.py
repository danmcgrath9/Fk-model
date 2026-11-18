"""Today's harness picks at TAB's first price, from Betwatch alone (19 Nov 2026, founder: "so who would we have been
on today?").

    python research/harness/bw_live.py BETWATCH_DIR --pub PUBKEY_B64 [--day YYYY-MM-DD]

Betfair's free files stop at the end of last month, so the live price is built from Betwatch only: the pure form
inputs of Test 9 (no input built from any price) re-made from Betwatch's own results (each horse's record, driver,
trainer, 60-day form, draw at the track, class, handicap, each against the field), then stage 2 with TAB's first
price, exactly as Test 9. Fitted on races to 30 Jun 2025; stage 2 fitted on Jul-Dec 2025; scored on 2026 to yesterday
(log loss against TAB's first price, paper bets at TAB's first price, closing-line value) before today is priced.

Today's races (and any day after the cached months) are fetched from Betwatch with BETWATCH_API_KEY. The picks name
horses and carry Betwatch prices, so they are SEALED to the given public key (greyhound/sealed.py): the public log
carries counts, scores and ciphertext only. Paper picks: nothing is bet.
"""
import argparse, base64, json, os, sys, tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hx_model import fit, winner_ll, renorm
from bw_data import (load_betwatch, runner_rows, add_bw_history, prior_totals, windowed_form)

SYD = ZoneInfo("Australia/Sydney")
TRAIN_END, VALID_END, TEST_START = "2025-07-01", "2026-01-01", "2026-01-01"
EDGE = 0.10
CATS = ["TRACK", "class_cat", "cond", "state"]
REL = ["driver_win_rate", "trainer_win_rate", "driver60_rate", "trainer60_rate", "bwh_pos_ewm", "bwh_win_rate",
       "bwh_place_rate", "horse_track_rate", "draw_win_rate"]
BASE = ["DISTANCE", "trot", "TAB_NUMBER", "tab_rel", "field", "handicap", "handicap_vs_min", "class_num",
        "bwh_class_change", "bwh_hcp_change", "bwh_runs", "bwh_days", "bwh_last_pos", "bwh_last_pos_rel", "bwh_pos_ewm",
        "bwh_win_rate", "bwh_place_rate", "driver_runs", "driver_win_rate", "trainer_runs", "trainer_win_rate",
        "combo_runs", "combo_win_rate", "dr_track_runs", "dr_track_win_rate", "driver60_runs", "driver60_rate",
        "trainer60_runs", "trainer60_rate", "draw_runs", "draw_win_rate", "horse_track_runs", "horse_track_rate",
        "driver_change", "emergency"]
FEATS = BASE + [f"{c}_vs_race" for c in REL] + [f"{c}_rank" for c in REL]


def fetch_recent(cache_bw, day):
    """Races on the days after the cached months, up to and including `day`, from the API."""
    from greyhound import betwatch as B
    last = pd.Timestamp(cache_bw.bw_date.max()).date()
    rows, d = [], last + timedelta(days=1)
    s = B._session() if d <= day else None
    while d <= day:
        races = B.fetch_day(s, d.isoformat(), ("Harness",), B.AU_STATES)
        for r in races:
            rows += runner_rows(B.compact(r))
        print(f"fetched {d}: {len(races)} races")
        d += timedelta(days=1)
    return pd.DataFrame(rows)


def frame(bw, today):
    """Betwatch runner rows -> one row per starter with pure-form inputs, earlier races only."""
    bw = add_bw_history(bw)
    df = bw[~bw.scratched & bw.bw_start.notna()].copy()
    df["race"] = df.bw_race
    df["start"] = df.bw_start.dt.tz_convert(None)          # naive UTC: the window sums need plain datetimes
    df["date"] = df.bw_start.dt.tz_convert(SYD).dt.tz_localize(None).dt.normalize()
    df["today"] = df.date.dt.date == today
    df["won"] = (df.bw_pos == 1).astype(int)
    df["field"] = df.groupby("race").race.transform("size")
    df["TRACK"], df["DISTANCE"], df["TAB_NUMBER"] = df.bw_track, df.bw_distance, df.number
    df["state"] = df.bw_state.fillna("none")
    df["trot"] = df.race_name.astype("string").str.upper().str.contains("TROT").fillna(False).astype(int)
    df["tab_rel"] = df.TAB_NUMBER / df.field
    df["emergency"] = df.emergency.astype(float)
    df["hkey"] = df.horse_bw.map(lambda x: f"id{int(x)}" if pd.notna(x) else None).fillna(
        df.horse_name.map(lambda n: f"nm{n}" if n else None))
    df["combo"] = (df.driver + " | " + df.trainer).where(df.driver.notna() & df.trainer.notna())
    df["dr_track"] = (df.driver + " | " + df.TRACK).where(df.driver.notna())
    df["h_track"] = (df.hkey + " | " + df.TRACK).where(df.hkey.notna())
    df["draw_key"] = df.TRACK + "|" + df.trot.astype(str) + "|" + df.TAB_NUMBER.astype("string")
    df["res"] = df.bw_has_results.astype(bool)
    # Records come from races with results only. Today's rows still need their records computed, so they join the
    # input with ONE shared start after every past race: totals count strictly earlier starts, so today's races
    # (no results yet) never count as runs for anyone, each other included.
    hist = df.copy()
    hist.loc[hist.today, "start"] = hist.loc[~hist.today, "start"].max() + pd.Timedelta(minutes=1)
    hist.loc[~hist.res, "won"] = 0
    for key, name in (("driver", "driver"), ("trainer", "trainer"), ("combo", "combo"), ("dr_track", "dr_track"),
                      ("h_track", "horse_track"), ("draw_key", "draw")):
        t = prior_totals(hist[hist.res | hist.today], key, ["won"])
        df.loc[t.index, f"{name}_runs"] = t.runs
        df.loc[t.index, f"{name}_win_rate" if name not in ("horse_track",) else "horse_track_rate"] = \
            (t.won + 1) / (t.runs + 10)
    for key, name in (("trainer", "trainer60"), ("driver", "driver60")):
        h2 = hist[hist.res | hist.today]
        n, r = windowed_form(h2, key, 60)
        df.loc[n.index, f"{name}_runs"], df.loc[r.index, f"{name}_rate"] = n, r
    o = df.sort_values(["hkey", "start"])
    prev = o.groupby("hkey", sort=False).driver.shift(1)
    df.loc[o.index, "driver_change"] = (o.driver != prev).astype(float).where(o.driver.notna() & prev.notna())
    cls = df["class"].astype("string")
    df["class_num"] = pd.to_numeric(cls.str.extract(r"(\d+)", expand=False), errors="coerce")
    top = cls.value_counts().head(60).index
    df["class_cat"] = cls.where(cls.isin(top), "other").fillna("none")
    df["cond"] = df.track_condition.astype("string").str.split().str[0].str.upper().fillna("none")
    for c in REL:
        x = df[c].astype(float)
        df[f"{c}_vs_race"] = x - x.groupby(df.race).transform("mean")
        df[f"{c}_rank"] = x.groupby(df.race).rank(ascending=(c == "bwh_pos_ewm"), method="min")
    inv = (1 / df.tab_open).where(df.tab_open > 1)
    full = inv.notna().groupby(df.race).transform("all")
    df["p_tab_open"] = (inv / inv.groupby(df.race).transform("sum")).where(full)
    for c in CATS:
        df[c] = df[c].astype("category")
    return df


def stage2_fit(v):
    grid = np.arange(0, 1.51, 0.05)
    return min(((a, b) for a in grid for b in grid if a + b > 0), key=lambda ab: winner_ll(
        renorm(np.exp(ab[0] * np.log(v.p_model) + ab[1] * np.log(v.p_tab_open)), v.race), v.won, v.race))


def apply2(d, a, b):
    return renorm(np.exp(a * np.log(d.p_model) + b * np.log(d.p_tab_open)), d.race)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cache"); ap.add_argument("--pub", required=True); ap.add_argument("--day", default="")
    a = ap.parse_args()
    today = date.fromisoformat(a.day) if a.day else datetime.now(SYD).date()
    bw = load_betwatch(a.cache)
    recent = fetch_recent(bw, today)
    bw = pd.concat([bw, recent], ignore_index=True).drop_duplicates(["bw_race", "number"], keep="last")
    t0 = bw[pd.to_datetime(bw.bw_date).dt.date == today]
    t0 = t0[~t0.scratched]
    print(f"today's runners not scratched: {len(t0)}; with a TAB price change logged {t0.tab_open.notna().sum()}; "
          f"with a current TAB price {pd.to_numeric(t0.tab_now, errors='coerce').gt(1).sum()}")
    # Today only: where Betwatch has logged no TAB price change yet, TAB's current price is the first price seen.
    now_px = pd.to_numeric(bw.tab_now, errors="coerce").where(lambda x: x > 1)
    is_today = pd.to_datetime(bw.bw_date).dt.date == today
    bw.loc[is_today, "tab_open"] = bw.loc[is_today, "tab_open"].fillna(now_px[is_today])
    bw.loc[is_today, "tab_last"] = bw.loc[is_today, "tab_last"].fillna(now_px[is_today])
    df = frame(bw, today)
    past = df[~df.today & df.res]
    g = past.groupby("race")
    past = past[(g.won.transform("sum") == 1) & (past.field >= 4) & g.p_tab_open.transform(lambda s: s.notna().all())
                & (past.date >= "2023-01-01")]
    tr, va = past[past.date < TRAIN_END], past[(past.date >= TRAIN_END) & (past.date < VALID_END)]
    te = past[past.date >= TEST_START]
    td = df[df.today & df.groupby("race").p_tab_open.transform(lambda s: s.notna().all()) & (df.field >= 4)].copy()
    print(f"# Harness picks for {today}: Betwatch-only pure form + TAB's first price\n")
    print(f"races: train {tr.race.nunique():,}, validation {va.race.nunique():,}, scored 2026 {te.race.nunique():,} "
          f"(to {te.date.max():%Y-%m-%d}); today {df[df.today].race.nunique()} races, {td.race.nunique()} with a TAB "
          f"first price on every runner; trot races {past.groupby('race').trot.first().mean():.1%}\n")
    va_, te_, m, _ = fit(tr, va, te, FEATS, CATS)
    sa, sb = stage2_fit(va_)
    te_["p_s2"] = apply2(te_, sa, sb)
    te_["p_equal"] = 1 / te_.field
    print(f"stage 2: log p = {sa:.2f} log(form) + {sb:.2f} log(TAB first)\n")
    print("## 2026 so far (never seen in fitting)\n\n| price | winner log loss | beats TAB first? |\n|---|---|---|")
    lt = winner_ll(te_.p_tab_open, te_.won, te_.race)
    for n, c in (("equal", "p_equal"), ("pure form", "p_model"), ("TAB first", "p_tab_open"), ("stage 2", "p_s2")):
        l = winner_ll(te_[c], te_.won, te_.race)
        print(f"| {n} | {l:.4f} | {'' if c == 'p_tab_open' else 'yes' if l < lt else 'no'} |")
    b = te_[(te_.p_s2 * te_.tab_open >= 1 + EDGE) & (te_.tab_last > 1)]
    ret = np.where(b.won == 1, b.tab_open - 1, -1.0)
    print(f"\npaper bets at TAB's first price, edge {EDGE:.0%}: {len(b):,} bets, {int(b.won.sum())} winners, ROI "
          f"{ret.mean():+.1%}; TAB price shortened after {(b.tab_last < b.tab_open).mean():.0%} of them (every runner "
          f"{(te_.tab_last < te_.tab_open).mean():.0%}); ROI at TAB's last price "
          f"{np.where(b.won == 1, b.tab_last - 1, -1.0).mean():+.1%}")
    by_m = b.assign(r=ret, mo=b.date.dt.strftime("%Y-%m")).groupby("mo").agg(bets=("r", "size"), roi=("r", "mean"))
    print("\n| month | bets | ROI at TAB first |\n|---|---|---|")
    for mo, r in by_m.iterrows():
        print(f"| {mo} | {int(r.bets)} | {r.roi:+.1%} |")

    if len(td):
        td["p_model"] = renorm(m.predict_proba(td[FEATS + CATS], num_iteration=m.best_iteration_)[:, 1], td.race)
        td["p_s2"] = apply2(td, sa, sb)
        td["edge"] = td.p_s2 * td.tab_open - 1
        picks = td[td.edge >= EDGE].sort_values("start")
        near = td[td.edge < EDGE].sort_values("edge", ascending=False).head(10)   # closest, NOT bets
        print(f"\ntoday: {len(picks)} paper picks at an edge of {EDGE:.0%} or more, in {picks.race.nunique()} races "
              f"(sealed below)")
        rows = [{"start_sydney": r.start.tz_localize("UTC").tz_convert(SYD).strftime("%H:%M"), "track": r.TRACK, "race": r.race_number,
                 "no": int(r.number), "horse": r.horse_name, "driver": r.driver, "trainer": r.trainer,
                 "tab_first": r.tab_open, "tab_first_hours_before": round(r.tab_open_hours, 1),
                 "tab_latest": r.tab_last, "form_chance": round(r.p_model, 4), "stage2_chance": round(r.p_s2, 4),
                 "fair_price": round(1 / r.p_s2, 2), "edge": round(r.edge, 3)} for r in picks.itertuples()]
        near_rows = [{"start_sydney": r.start.tz_localize("UTC").tz_convert(SYD).strftime("%H:%M"), "track": r.TRACK,
                      "race": r.race_number, "no": int(r.number), "horse": r.horse_name, "tab_first": r.tab_open,
                      "tab_latest": r.tab_last, "fair_price": round(1 / r.p_s2, 2), "edge": round(r.edge, 3)}
                     for r in near.itertuples()]
        from greyhound import sealed
        with tempfile.NamedTemporaryFile("wb", suffix=".pem", delete=False) as fh:
            fh.write(base64.b64decode(a.pub)); pk = fh.name
        lines, sha = sealed.seal(json.dumps({"day": str(today), "picks": rows, "closest_not_bets": near_rows}).encode(), Path(pk))
        print(f"sha256 {sha}")
        print("\n".join(lines))
    else:
        print("\ntoday: no race with a TAB first price on every runner yet")


if __name__ == "__main__":
    main()
