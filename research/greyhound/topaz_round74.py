"""Round 74: the edge TAB cannot limit, at midday (18 Nov 2026, founder: "they wont let big limits on that"; "Yep run
it")

Test 91 found the model's edge lives at TAB's first price. TAB limits accounts that win, and a bet at TAB's open is the
one it protects itself against most. Greyhound Racing Victoria's minimum bet limit makes an approved operator lay a
fixed-odds win bet on a Victorian greyhound race up to a set amount, once per runner per customer per race, however the
account has done. Its conditions apply to bets placed after midday where the meeting's first race starts at 2pm or
later (GRV's wagering FAQ). The amounts, and the rule for meetings that start before 2pm, are not confirmed here. Stated
before the run, on Test 88's fit (corr_r70), February 2025 on, bets with a corrected BSP:

  - when TAB opens: TAB's first price by Melbourne clock time and hours before the race; the share of races at meetings
    whose first race starts at 2pm or later (where the limit applies after midday)
  - where the 2-point bets at TAB's open fall: at such a meeting and after midday (the limit already applies), at such
    a meeting and before midday, or at a meeting that starts before 2pm (rule not confirmed)
  - at such meetings, the first moment the limit applies: TAB's price at midday, or its first price when TAB opens after
    midday, with the deduction for the dogs scratched after that moment. The 2-point margin, fair price under $15, a
    quarter of Kelly at one scale (TAB's open's 2-point bets' mean stake from February 2025 is one unit), against
    TAB's open on the same races:
      * the model as it stood at TAB's open
      * the model moved by TAB's own move since its open (the model's chance times TAB's chance at midday over its
        chance at the open, the race summed back to the model's total)
  - by half, by three months, and since the live tracker began (14 November 2026; realised only, Betfair's files
    reach a month later)
  - what the minimum would let a bet win: each bet staked to win $500, or $1,000 at a metropolitan meeting (Sandown on
    a Thursday night, The Meadows on a Saturday night, both from 6pm); expected dollars a month by the corrected BSP,
    and realised. The amounts are one source's, from before GRV changed the conditions on 1 November 2024

    python research/greyhound/topaz_round74.py DIR LABEL    (as round 73)

Counts, sums and rates only: no race, dog or price is printed.
"""
import gzip
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gbm_v0                     # noqa: E402
import topaz_round32 as R32       # noqa: E402
import topaz_round58 as R58       # noqa: E402
import topaz_round62 as R62       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round67 as R67       # noqa: E402
import topaz_round68 as R68       # noqa: E402
import topaz_round73 as R73       # noqa: E402

MEL = ZoneInfo("Australia/Melbourne")
NOON = 12
LATE_FIRST_RACE = 14              # the limit applies after midday where the meeting's first race starts at 2pm or later
METRO = (("SANDOWN", 3), ("MEADOWS", 5))   # (track name contains, weekday Monday = 0) from 6pm
METRO_FROM = 18
TO_WIN = {"metro": 1000.0, "other": 500.0}
MARGIN = 0.02
LIVE = "2026-11-14"


def clock(ts: float, tz=MEL) -> float:
    """The Melbourne clock hour of an epoch time, with minutes as a fraction; NaN when missing."""
    if ts is None or not np.isfinite(ts):
        return np.nan
    d = datetime.fromtimestamp(ts, tz)
    return d.hour + d.minute / 60


def hhmm(h: float) -> str:
    """A clock hour with a fraction as HH:MM."""
    hh, mi = divmod(int(round(h * 60)), 60)
    return f"{hh % 24:02d}:{mi:02d}"


def noon_of(day: str, tz=MEL) -> float:
    """Epoch seconds of midday in Melbourne on a race date (YYYY-MM-DD); NaN when unreadable."""
    try:
        y, m, d = (int(v) for v in str(day)[:10].split("-"))
    except ValueError:
        return np.nan
    return datetime(y, m, d, NOON, 0, tzinfo=tz).timestamp()


def is_metro(track: str, first_start: float) -> bool:
    if not track or not np.isfinite(first_start):
        return False
    d = datetime.fromtimestamp(first_start, MEL)
    up = str(track).upper()
    return any(k in up and d.weekday() == wd for k, wd in METRO) and d.hour >= METRO_FROM


def race_rows(r: dict, first_start: float) -> list:
    """The runners that ran in one race: TAB's open, the first moment the limit applies (midday, or TAB's open when it
    opens after midday), TAB's price then, and the deduction for the dogs scratched after that moment."""
    start = R32.ts(r.get("start"))
    runners = []
    for ru in r.get("runners", []):
        fl = sorted(((float(p), R32.ts(t)) for p, t in ((ru.get("books") or {}).get("Tab") or {}).get("flucs") or []
                     if p and float(p) > 1 and not np.isnan(R32.ts(t))), key=lambda f: f[1])
        if not np.isnan(start):
            fl = [f for f in fl if f[1] <= start]
        st = R32.ts(ru.get("scratched")) if ru.get("scratched") else np.inf
        runners.append((ru, fl, np.inf if np.isnan(st) else st))
    firsts = [fl[0][1] for _, fl, _ in runners if fl]
    if not firsts:
        return []
    open_t = min(firsts)
    late = np.isfinite(first_start) and clock(first_start) >= LATE_FIRST_RACE
    bt = max(open_t, noon_of(r.get("date")))
    in_time = late and np.isfinite(bt) and (np.isnan(start) or bt < start)
    cents = 0
    if in_time:
        for _, fl, st in runners:
            if np.isfinite(st) and st > bt and fl:
                ps = R32.price_at(fl, st)
                cents += R32.table_cents(R32.price_at(fl, bt) if np.isnan(ps) else ps)
    ded = min(R32.MAX_CENTS, cents) / 100
    metro = bool(late and is_metro(r.get("track"), first_start))
    rows = []
    for ru, fl, st in runners:
        if np.isfinite(st) or not fl:
            continue
        p = R32.price_at(fl, bt) if in_time else np.nan
        rows.append({"date": r.get("date"), "dog_raw": ru.get("name"), "bwl_open": open_t, "bwl_start": start,
                     "bwl_late": bool(late), "bwl_metro": metro, "lim_t": bt if in_time else np.nan,
                     "lim_price": p, "lim_ded": ded})
    return rows


def load_limits(bdir: str) -> pd.DataFrame:
    """Every runner that ran, from the Betwatch month files, with the limit's moment and TAB's price then."""
    rows = []
    for f in sorted(Path(bdir).glob("betwatch_VIC_G_*.json.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            races = json.load(fh).get("races", [])
        first = {}
        for r in races:
            s = R32.ts(r.get("start"))
            k = (r.get("date"), r.get("track"))
            if np.isfinite(s):
                first[k] = min(first.get(k, np.inf), s)
        for r in races:
            rows.extend(race_rows(r, first.get((r.get("date"), r.get("track")), np.nan)))
    bw = pd.DataFrame(rows)
    if bw.empty:
        return bw
    bw["date"] = pd.to_datetime(bw.date, errors="coerce")
    bw["_dn"] = gbm_v0.norm_name(bw.dog_raw.fillna(""))
    return bw.drop(columns="dog_raw").drop_duplicates(["date", "_dn"], keep=False)


def moved_chance(p: np.ndarray, open_book: np.ndarray, lim_book: np.ndarray, race: np.ndarray) -> np.ndarray:
    """The model's chance moved by TAB's own move: p x (TAB's chance then / TAB's chance at its open), each TAB chance
    a share of the runners that ran, and the race summed back to the model's own total."""
    g = pd.Series(open_book).groupby(race)
    ob = open_book / g.transform("sum").values
    lb = lim_book / pd.Series(lim_book).groupby(race).transform("sum").values
    with np.errstate(divide="ignore", invalid="ignore"):
        raw = p * lb / ob
    tot = pd.Series(p).groupby(race).transform("sum").values
    rs = pd.Series(raw).groupby(race).transform("sum").values
    with np.errstate(divide="ignore", invalid="ignore"):
        return raw * tot / rs


def to_win_stakes(paid: np.ndarray, metro: np.ndarray) -> np.ndarray:
    """Dollars staked so each bet wins the limit: $1,000 at a metropolitan meeting, $500 elsewhere."""
    amt = np.where(metro, TO_WIN["metro"], TO_WIN["other"])
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(paid > 1, amt / (paid - 1), 0.0)


def realised_row(t: pd.DataFrame, m: np.ndarray, paid: np.ndarray, u: np.ndarray) -> str:
    n = int(m.sum())
    if not n:
        return "0 | | "
    won = t.won.values[m].astype(float)
    r = u[m] * np.where(won == 1, paid[m] - 1, -1.0)
    return f"{n:,} | {u[m].sum():,.0f} | {r.sum():+,.1f}"


def main(d, label):
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 74, the edge TAB cannot limit, at midday\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x, _, _, _ = R62.field(d, t0)
    if not R67.read_saved(x, "r70", "c_f"):
        print("Test 88's fit (corr_r70) is not in the walk cache: nothing to test")
        return 1
    t = x[x.is_ran.astype(bool).values].reset_index(drop=True)
    bw = load_limits(bdir)
    n0 = len(t)
    t = t.assign(_dn=gbm_v0.norm_name(t.dog_name.fillna(""))).merge(bw, on=["date", "_dn"], how="left").drop(
        columns="_dn")
    assert len(t) == n0, "the limit prices duplicated runners"
    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    since = R63.R36.in_period(t, R63.SINCE, None)
    race = t.race_id.values
    print(f"Runners that ran at TAB's first price: {len(t):,} in {t.race_id.nunique():,} races, to "
          f"{t.date.max():%d %b %Y}. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    # 1. When TAB opens
    r1 = t[since].drop_duplicates("race_id")
    r1 = r1[np.isfinite(r1.bwl_open.values.astype(float))]
    oh = np.array([clock(v) for v in r1.bwl_open.values])
    lead = (r1.bwl_start - r1.bwl_open).values / 3600
    late = r1.bwl_late.fillna(False).astype(bool).values
    print("## 1. When TAB opens, races since February 2025\n")
    print(f"Races with TAB's open and start time: {int(np.isfinite(oh).sum()):,}. At a meeting whose first race starts "
          f"at 2pm or later: {late.mean():.0%} ({int(late.sum()):,}).\n")
    print("| races | TAB opens, Melbourne clock (10th / 25th / median / 75th / 90th percentile) | hours before the race "
          "(median) | TAB opens after midday |\n|---|---|---|---|")
    for nm, k in (("all", np.ones(len(r1), bool)), ("meetings from 2pm", late), ("meetings before 2pm", ~late)):
        h = oh[k & np.isfinite(oh)]
        if not len(h):
            continue
        q = np.percentile(h, [10, 25, 50, 75, 90])
        hh = " / ".join(hhmm(v) for v in q)
        print(f"| {nm} | {hh} | {np.nanmedian(lead[k]):.1f} | {(h >= NOON).mean():.0%} |")

    # 2. Where the 2-point bets at TAB's open fall
    pm = R67.model_chance(t, "c_f")
    tab_paid = R68.paid_price(t)
    m_tab = R68.margin_bets(t, pm, MARGIN)
    raw = R73.raw_kelly(pm, tab_paid)
    scale = raw[m_tab & since].mean()
    if not np.isfinite(scale) or scale <= 0:
        print("No 2-point bets at TAB's open since February 2025: nothing to test")
        return 1
    u_tab = raw / scale
    m_tab &= u_tab > 0
    timed = np.isfinite(t.bwl_open.values.astype(float))
    lt = t.bwl_late.fillna(False).astype(bool).values & timed
    after = lt & (np.array([clock(v) for v in t.bwl_open.values]) >= NOON)
    groups = [("meeting from 2pm, TAB opens after midday: the limit already applies", lt & after),
              ("meeting from 2pm, TAB opens before midday", lt & ~after),
              ("meeting before 2pm: rule not confirmed", timed & ~lt),
              ("no opening time in the price history", ~timed)]
    periods = [("Feb 2025 on", R63.SINCE, None)] + R63.HALVES
    head = ("bets | units staked | corrected BSP per unit staked (SE) | corrected BSP units | realised units | "
            "luck in the realised units (SD) | deepest fall, realised | losing months")
    print(f"\n## 2. Where TAB's open's 2-point bets fall (a quarter of Kelly at one scale)\n\n| where | period | {head} |\n|"
          + "---|" * 10)
    for g, k in groups:
        for lab, lo, hi in periods[:1]:
            per = R63.R36.in_period(t, lo, hi)
            print(f"| {g} | {lab} | " + R73.kelly_row(t, tq, m_tab & k & per, tab_paid, u_tab) + " |")

    # 3. At the limit's first moment, at meetings from 2pm
    lp = t.lim_price.values.astype(float)
    have = pd.Series(np.isfinite(lp) & (lp > 1)).groupby(race).transform("all").values & lt
    tl = t.assign(price=np.where(have, lp, np.nan), ded=t.lim_ded.fillna(0).values)
    lim_paid = R68.paid_price(tl)
    lim_book = np.where(have, 1 / np.where(lp > 1, lp, np.nan), np.nan)
    pmv = np.where(have, moved_chance(pm, t.p_book.values.astype(float), lim_book, race), np.nan)
    models = {"the model at TAB's open": pm, "the model moved by TAB's move": pmv}
    rows = [("TAB's open, the same races", m_tab & have, tab_paid, u_tab)]
    for nm, p in models.items():
        u = R73.raw_kelly(p, lim_paid) / scale
        m = R68.margin_bets(tl, p, MARGIN) & have & (u > 0)
        rows.append((f"the limit's moment, {nm}", m, lim_paid, u))
    print(f"\n## 3. At meetings from 2pm, the first moment the limit applies ({int(have.sum()):,} runners in "
          f"{pd.unique(race[have]).size:,} races; {(time.monotonic() - t0) / 60:.0f} minutes in)\n")
    print(f"| price | period | {head} |\n|" + "---|" * 10)
    for nm, m, paid, u in rows:
        for lab, lo, hi in periods:
            per = R63.R36.in_period(t, lo, hi)
            print(f"| {nm} | {lab} | " + R73.kelly_row(t, tq, m & per, paid, u) + " |")

    print("\n## 4. By three months, at meetings from 2pm: corrected BSP units / realised units\n")
    print("| three months | " + " | ".join(r[0] for r in rows) + " |\n|" + "---|" * (len(rows) + 1))
    for bname, lo, hi in R68.blocks(R63.SINCE, None):
        per = R63.R36.in_period(t, lo, hi)
        cells = []
        for _, m, paid, u in rows:
            s = R68.staked(tq, m & per, paid, u)
            cells.append(f"{s['units']:+,.1f} / {s['real']:+,.1f}" if s["n"] else "no BSP yet")
        print(f"| {bname} | " + " | ".join(cells) + " |")

    live = R63.R36.in_period(t, LIVE, None)
    print(f"\n## 5. Since the live tracker began ({LIVE}), realised only: bets | units staked | realised units\n")
    print("| price | bets | units staked | realised units |\n|---|---|---|---|")
    print(f"| TAB's open, every meeting | " + realised_row(t, m_tab & live, tab_paid, u_tab) + " |")
    for nm, m, paid, u in rows:
        print(f"| {nm} | " + realised_row(t, m & live, paid, u) + " |")

    print("\n## 6. What the minimum would let a bet win: each bet staked to win $1,000 at a metropolitan meeting and "
          "$500 elsewhere (amounts not confirmed), Feb 2025 on\n")
    print("| price | bets | of them metropolitan | dollars staked a month | expected dollars a month, corrected BSP | "
          "realised dollars a month | luck in the realised dollars a month (SD) |\n|---|---|---|---|---|---|---|")
    mo = R67.months_in(t, since & have)
    metro = t.bwl_metro.fillna(False).astype(bool).values
    y = tq.p_bsp.notna().values
    for nm, m, paid, _ in rows:
        k = m & since & y
        if not k.any():
            continue
        s = to_win_stakes(paid, metro)
        q = tq.p_bsp.values.astype(float)
        ev = s[k] * (paid[k] * q[k] - 1)
        won = t.won.values[k].astype(float)
        real = s[k] * np.where(won == 1, paid[k] - 1, -1.0)
        se = np.sqrt((s[k] ** 2 * paid[k] ** 2 * q[k] * (1 - q[k])).sum())
        print(f"| {nm} | {int(k.sum()):,} | {int((k & metro).sum()):,} | {s[k].sum() / mo:,.0f} | "
              f"{ev.sum() / mo:+,.0f} | {real.sum() / mo:+,.0f} | {se / mo:,.0f} |")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 74")
