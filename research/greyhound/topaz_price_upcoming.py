"""Price TODAY'S Victorian races with the model, before they run (5 Nov 2026, founder: "With our model, what prices
would we have had Sandown Park race 1? Were they different than GRV rated?").

    python research/greyhound/topaz_price_upcoming.py DIR LABEL      (BETFAIR_DIR, RACES_DIR as for topaz_walk.py;
                                                                      TOPAZ_API_KEY; PRICE_DAY=YYYY-MM-DD, default today)

1. Topaz: /race/upcoming from the day's start, then /race/{id}/runs (the run rows, bulk-shaped) and
   /race/{id}/runs/form (GRV's comment, rating, isBestBet and pre-race startPrice) for each race, merged by run.
   Race-level fields missing from a run row are filled from the race record. The field NAMES seen are printed once.
2. The rows are written as runs_VIC_upcoming.json.gz beside a copy of the cached history (links, no data copied),
   today's race records as races_VIC_upcoming.json.gz, and topaz_walk.build_full() builds everything with
   keep_unresulted=True, so tonight's runners get every rating as at the end of yesterday.
3. The BSP-chance model (round 6's D1 inputs plus the tips when RACES_DIR is set) is fitted on every resulted race,
   recent years weighted more, WALK_ROUNDS_A rounds (3,000 default), exactly as a walk-forward refit, and prices
   tonight's card: one table per race, our price beside GRV's pre-race price, rating, tip and best-bet flag, and
   which runners Test 12's rule (edge of 50% or more at $8-$13 against GRV's pre-race price) would take.
Nothing is bet. The prices are the founder's to read.
"""
import gzip
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402
from greyhound.preview import SYDNEY  # noqa: E402
from greyhound.topaz import TopazClient, TopazError  # noqa: E402

NEED = ["raceId", "meetingId", "meetingDate", "trackCode", "distanceInMetres", "incomingGrade", "dogId", "boxNumber",
        "place", "resultTime", "resultMargin", "firstSplitTime", "scratched"]
RACE_ALIASES = {"meetingId": ["meetingId"], "meetingDate": ["meetingDate", "raceDate", "date"],
                "trackCode": ["trackCode"], "trackName": ["trackName", "track"],
                "distanceInMetres": ["distanceInMetres", "distance", "raceDistance"],
                "incomingGrade": ["incomingGrade", "grade", "raceGrade", "gradeCode"],
                "raceNumber": ["raceNumber", "number"], "raceStartTime": ["raceStartTime", "raceStart", "startTime"]}
# the pre-race run rows (field names printed by the first run, 5 Nov 2026) use `track` for the name and `distance`
# for the metres where the bulk feed uses trackName and distanceInMetres
RUN_ALIASES = {"trackName": ["trackName", "track"], "distanceInMetres": ["distanceInMetres", "distance"]}


def txt(v) -> str:
    """A value for printing: NaN and None are blank (a NaN is truthy, so `x or y` does not do this)."""
    return "" if v is None or (isinstance(v, float) and np.isnan(v)) else str(v)


def pick(d: dict, names):
    for n in names:
        if n in d and d[n] not in (None, ""):
            return d[n]
    return None


def fetch_day(client: TopazClient, day: str):
    """Tonight's runs in the bulk feed's shape, plus the race records, plus the field names seen."""
    races = [r for r in (client._get("race/upcoming", params={"from": f"{day} 00:00"}) or []) if isinstance(r, dict)]
    races = [r for r in races if str(pick(r, RACE_ALIASES["meetingDate"]) or day)[:10] == day]
    rows, names = [], {"race": set(), "run": set(), "form": set()}
    for r in races:
        rid = r.get("raceId")
        names["race"].update(r.keys())
        runs = [u for u in (client._get(f"race/{rid}/runs") or []) if isinstance(u, dict)]
        form = [u for u in (client._get(f"race/{rid}/runs/form") or []) if isinstance(u, dict)]
        by_run = {u.get("runId"): u for u in form if u.get("runId") is not None}
        by_dog = {u.get("dogId"): u for u in form if u.get("dogId") is not None}
        if not runs:
            runs = form
        for u in runs:
            names["run"].update(u.keys())
            f = by_run.get(u.get("runId")) or by_dog.get(u.get("dogId")) or {}
            names["form"].update(f.keys())
            row = dict(u)
            for k, v in f.items():
                if row.get(k) in (None, "") and v not in (None, ""):
                    row[k] = v
            for k, aliases in RUN_ALIASES.items():
                if row.get(k) in (None, ""):
                    row[k] = pick(row, aliases)
            for k, aliases in RACE_ALIASES.items():
                if row.get(k) in (None, ""):
                    row[k] = pick(r, aliases)
            row.setdefault("raceId", rid)
            for k in ("place", "resultTime", "resultMargin", "firstSplitTime"):
                row[k] = None                       # no result yet, whatever a stale field says
            row.setdefault("scratched", False)
            rows.append(row)
    return rows, races, {k: sorted(v) for k, v in names.items()}


def stage(cache: Path, rows, races, day: str) -> Path:
    """A temp directory holding links to the cached files plus the day's rows, so load_topaz sees them together."""
    tmp = Path(tempfile.mkdtemp(prefix="topaz_today_"))
    for f in cache.glob("*.json.gz"):
        (tmp / f.name).symlink_to(f.resolve())
    with gzip.open(tmp / "runs_VIC_upcoming.json.gz", "wt", encoding="utf-8") as fh:
        json.dump(rows, fh)
    with gzip.open(tmp / "races_VIC_upcoming.json.gz", "wt", encoding="utf-8") as fh:
        json.dump(races, fh)
    return tmp


def main(d, label):
    day = os.environ.get("PRICE_DAY") or pd.Timestamp.now(tz=SYDNEY).strftime("%Y-%m-%d")
    client = TopazClient(pause=1.0)
    rows, races, names = fetch_day(client, day)
    print(f"# {label}: the model's prices for {day}\n")
    print(f"{len(races)} VIC races on {day} from /race/upcoming, {len(rows)} runners, {client.calls} calls")
    for k in ("race", "run", "form"):
        print(f"  {k} fields: {', '.join(names[k])}")
    missing = [c for c in NEED if rows and c not in rows[0]]
    if not rows or missing:
        print(f"\nCannot price: {'no runners' if not rows else 'the run rows lack ' + ', '.join(missing)}")
        return 1
    cache = Path(d)
    tmp = stage(cache, rows, races, day)
    if os.environ.get("RACES_DIR"):
        os.environ["RACES_DIR"] = str(tmp)        # today's records beside the history's
    df, num, rel, note = W.build_full(str(tmp), keep_unresulted=True)
    today = df.date == pd.Timestamp(day)
    print(f"\n{note}\nbuilt: {df.race_id.nunique():,} races; tonight's card after the build: {df[today].race_id.nunique()} races, "
          f"{int(today.sum())} runners (a race drops out if a runner has no pre-race price or the field is under 4)\n")
    if not today.any():
        return 1
    tr = (~today).values
    X = T.features(df, num, rel)
    start = pd.Timestamp(day)
    rec = 0.5 ** ((((start - df.date[tr]).dt.days) / 365.25).values / 3.0)
    bst = W.fit_fixed(X[tr], df.p_mkt.values[tr].astype(float), df.race_id[tr], rec, W.ROUNDS_A)
    p = V1.race_softmax(bst.predict(X[today.values], raw_score=True), df.race_id.values[today.values])
    card = df[today].copy()
    card["p_model"] = p
    card["our_price"] = 1 / card.p_model
    grv = card.start_price.astype(float)
    card["grv_price"] = grv
    card["grv_pct"] = 1 / grv
    card["edge"] = card.p_model * grv - 1
    book = card.groupby("race_id").grv_pct.transform("sum")
    card["grv_fair"] = grv * book                       # GRV's price with its book taken out, so the two columns compare
    print(f"fitted on {df.race_id[tr].nunique():,} races, {W.ROUNDS_A} rounds; the model's prices sum to 100% a race; "
          f"GRV's pre-race prices sum to {card.groupby('race_id').grv_pct.sum().median():.0%} a race (median book)\n")
    order = ["start_time", "race_id"] if "start_time" in card else ["race_id"]
    for rid, g in card.sort_values(order).groupby("race_id", sort=False):
        g = g.sort_values("our_price")
        r0 = g.iloc[0]
        venue = txt(r0.get("track_name")) or txt(r0.track)
        start = txt(r0.get("start_time"))
        print(f"## {venue} R{txt(r0.get('race_number'))} {start[11:16] if len(start) >= 16 else start} "
              f"{int(r0.distance)}m {txt(r0.grade)} (GRV's book {book.loc[g.index[0]]:.0%})\n")
        print("| box | dog | our price | our % | GRV pre-race price | GRV price at a 100% book | GRV rating | tip | best bet | Test 12 bet |")
        print("|---|---|---|---|---|---|---|---|---|---|")
        for _, x in g.iterrows():
            bet = "YES" if (x.edge >= 0.5 and 8 <= x.grv_price <= 13) else ""
            tip = "" if pd.isna(x.get("tip_rank", np.nan)) or x.get("tip_rank", 0) == 0 else f"#{int(x.tip_rank)}"
            box = "" if pd.isna(x.box) else int(x.box)
            print(f"| {box} | {txt(x.get('dog_name'))} | ${x.our_price:.2f} | {x.p_model:.1%} | ${x.grv_price:.2f} | "
                  f"${x.grv_fair:.2f} | {txt(x.get('topaz_rating'))} | {tip} | {'yes' if x.get('is_best_bet') else ''} | {bet} |")
        print()
    picks = card[(card.edge >= 0.5) & (card.grv_price.between(8, 13))]
    print(f"Test 12's rule against GRV's pre-race price would take {len(picks)} runner(s) tonight: "
          + ("; ".join(f"{txt(x.get('track_name')) or txt(x.track)} R{txt(x.get('race_number'))} box {txt(x.box)} "
                       f"{txt(x.get('dog_name'))} (ours ${x.our_price:.2f}, GRV ${x.grv_price:.2f})"
                       for _, x in picks.iterrows()) or "none"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz today"))
    except TopazError as e:
        print(f"Topaz refused or failed: {e}")
        sys.exit(1)
