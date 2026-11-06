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
   tonight's card, with each runner's reasons: the model's per-input contributions (LightGBM pred_contrib) relative
   to the race, summed into families (ratings, Elo, the box, GRV's preview, ...).
4. The card for PRICE_TRACK (default SANDOWN; comma separated) and the paper bets across the whole card are SEALED
   (greyhound/sealed.py): this log is public and GRV's per-runner values are personal use, so the log carries only
   counts and ciphertext. research/greyhound/card_page.py turns the unsealed payload into the race page.
Nothing is bet. The prices are the founder's to read.
"""
import gzip
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402
from greyhound.preview import SYDNEY  # noqa: E402
from greyhound.sealed import seal  # noqa: E402
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


FAMILIES = [  # (label, test on the input's base name); first match wins, so the specific ones come first
    ("GRV's preview", lambda c: c.startswith("pv_")),
    ("GRV's tips", lambda c: c in ("tip_rank", "tip_top", "race_tips", "analyst_len", "has_suggested")),
    ("who beat whom (Elo)", lambda c: c in ("elo", "margin_elo")),
    ("box and the draw", lambda c: c.startswith("box") or c in ("speed_rank_x_box", "leader_x_box") or "vacan" in c),
    ("early speed and the map", lambda c: c.startswith(("style_", "map_", "split_pos", "pir"))),
    ("time and split ratings", lambda c: "rating" in c or c in ("form_trend", "grade_prior", "runs_band", "runs_track")),
    ("trainer", lambda c: c.startswith("trainer")),
    ("breeding", lambda c: c.startswith(("sire", "dam"))),
    ("market history", lambda c: c.startswith("mkt_")),
    ("class of the race", lambda c: "class" in c or c in ("race_prize_log", "grade", "prize", "career_prize")),
    ("the track's character", lambda c: c.startswith("trk_") or c in ("dog_type_surprise", "dog_type_runs",
                                                                     "dog_other_surprise")),
    ("record and recent form", lambda c: c.startswith(("dog_", "finish", "last5", "total_form")) or c == "runs"),
    ("fitness, age and weight", lambda c: c in ("days_since", "age_days", "weight", "weight_change", "dist_change")),
    ("track and trip", lambda c: c in ("track", "distance", "field", "same_track")),
]


def family(col: str) -> str:
    base = col[:-4] if col.endswith("_rel") else col
    return next((name for name, test in FAMILIES if test(base)), "other")


def bet_window(p_model: float, lo: float = 8.0, hi: float = 13.0, edge: float = 0.5):
    """Test 12's rule (an edge of 50% or more, at $8-$13, chosen out of sample and held walk-forward): the price window
    a bet needs, or None when our price makes the window empty. Edge = our chance x price - 1."""
    need = (1 + edge) / p_model
    lo_ok = max(lo, need)
    return (round(lo_ok, 2), hi) if lo_ok <= hi else None


def card_payload(card, contrib, fam, book, day, n_fit, tracks) -> dict:
    """Everything the page needs, for the tracks asked for, plus the paper bets across the whole card."""
    names = sorted(set(fam))
    code = {n: i for i, n in enumerate(names)}
    rel = pd.DataFrame(contrib, index=card.index)
    rel = rel - rel.groupby(card.race_id.values).transform("mean")
    onehot = np.zeros((len(fam), len(names)))
    onehot[np.arange(len(fam)), [code[f] for f in fam]] = 1.0
    by_fam = pd.DataFrame(rel.values @ onehot, index=card.index)          # runner x family, relative to the race
    races, edges, seen = [], [], set()
    order = ["start_time", "race_id"] if "start_time" in card else ["race_id"]
    for rid, g in card.sort_values(order).groupby("race_id", sort=False):
        r0 = g.iloc[0]
        venue = txt(r0.get("track_name")) or txt(r0.track)
        for _, x in g.iterrows():
            w = bet_window(x.p_model)
            if w and w[0] <= x.grv_price <= w[1]:
                edges.append([venue, txt(r0.get("race_number")), txt(x.box), txt(x.dog_name), round(float(x.p_model), 4),
                              float(x.grv_price)])
        if tracks and not any(t in venue.upper() for t in tracks):
            continue
        seen.add(venue)
        rows = []
        for i, x in g.sort_values("our_price").iterrows():
            f = by_fam.loc[i]
            top = [[int(k), int(round(100 * (np.exp(v) - 1)))] for k, v in f.reindex(f.abs().sort_values(ascending=False).index).items()][:5]
            tip = x.get("tip_rank", np.nan)
            rows.append([txt(x.box), txt(x.dog_name), round(float(x.p_model), 4), float(x.grv_price),
                         txt(x.get("topaz_rating")), 0 if pd.isna(tip) else int(tip), int(bool(x.get("is_best_bet"))),
                         txt(x.get("last5")), [c for c in top if c[1] != 0],
                         # the speed map (founder, 5 Nov: "Was it always going to lead"): rank in the field on past
                         # first splits, share of its last 10 runs it led at the first point, quicker beginners inside
                         num_or_none(x.get("map_speed_rank")), num_or_none(x.get("style_led_rate"), 3),
                         num_or_none(x.get("map_quicker_inside"))])
        races.append({"t": venue, "n": txt(r0.get("race_number")), "s": txt(r0.get("start_time")), "d": int(r0.distance),
                      "g": txt(r0.grade), "b": round(float(book.loc[g.index[0]]), 3), "r": rows})
    return {"day": day, "fit": int(n_fit), "rounds": int(W.ROUNDS_A), "fam": names, "tracks": sorted(seen),
            "races": races, "edges": edges}


BLEND = (0.51, 0.66)      # Test 27: the blend refitted each month on the six before ran ours 0.38-0.64, SP 0.55-0.77


def rule_bets(card: pd.DataFrame) -> tuple:
    """Test 27's tested rule on the card, with GRV's pre-race price standing in for the SP: the blend of our chance
    with GRV's (its book taken out), a bet when GRV's price is at least 1.3x the blended price with the blended price
    $2-$15, Kelly x75 on the chance halfway between the blend and GRV's, cap 4. Returns ([[venue, race, box, dog,
    our chance, blended chance, GRV's price, units], ...], the blend weights)."""
    import topaz_round9 as R9
    env = os.environ.get("PRICE_BLEND", "")
    w = tuple(float(x) for x in env.split(",")) if env else BLEND
    c = card[card.grv_price > 1].copy()
    if c.empty:
        return [], list(w)
    c["p_grv"] = c.grv_pct / c.groupby("race_id").grv_pct.transform("sum")
    score = w[0] * np.log(c.p_model.clip(1e-12)) + w[1] * np.log(c.p_grv.clip(1e-12))
    c["p_blend"] = V1.race_softmax(score.values, c.race_id.values)
    m, o, u = R9.horse_bets(c, c.p_blend.values, c.p_grv.values, c.grv_price.values.astype(float), 0.0, 1.3, (2, 15))
    out = []
    for (_, x), units in zip(c[m].iterrows(), u[m]):
        out.append([txt(x.get("track_name")) or txt(x.track), txt(x.get("race_number")), txt(x.box), txt(x.dog_name),
                    round(float(x.p_model), 4), round(float(x.p_blend), 4), float(x.grv_price), round(float(units), 2)])
    return out, list(w)


def num_or_none(v, nd: int = 0):
    """A number for the payload, or None when missing (JSON has no NaN)."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return round(float(v), nd) if nd else int(round(float(v)))


def txt(v) -> str:
    """A value for printing: NaN and None are blank (a NaN is truthy, so `x or y` does not do this)."""
    return "" if v is None or (isinstance(v, float) and np.isnan(v)) else str(v)


def pick(d: dict, names):
    for n in names:
        if n in d and d[n] not in (None, ""):
            return d[n]
    return None


def fetch_day(client: TopazClient, day: str, workers: int = 8):
    """Tonight's runs in the bulk feed's shape, plus the race records, plus the field names seen."""
    races = [r for r in (client._get("race/upcoming", params={"from": f"{day} 00:00"}) or []) if isinstance(r, dict)]
    races = [r for r in races if str(pick(r, RACE_ALIASES["meetingDate"]) or day)[:10] == day]
    rows, names = [], {"race": set(), "run": set(), "form": set()}
    # every race's two calls at once, under the client's shared per-minute cap (GRV allows about 80 a minute); the
    # rows are still assembled in /race/upcoming's order
    from concurrent.futures import ThreadPoolExecutor
    paths = [p for r in races for p in (f"race/{r.get('raceId')}/runs", f"race/{r.get('raceId')}/runs/form")]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        got = dict(zip(paths, ex.map(lambda p: client._get(p) or [], paths)))
    for r in races:
        rid = r.get("raceId")
        names["race"].update(r.keys())
        runs = [u for u in got[f"race/{rid}/runs"] if isinstance(u, dict)]
        form = [u for u in got[f"race/{rid}/runs/form"] if isinstance(u, dict)]
        by_run = {u.get("runId"): u for u in form if u.get("runId") is not None}
        by_dog = {u.get("dogId"): u for u in form if u.get("dogId") is not None}
        if not runs:
            runs = form
        for u in runs:
            names["run"].update(u.keys())
            if u.get("boxNumber") in (None, "") or u.get("scratched") is True:
                continue                            # a reserve (no box) or a scratching does not run
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


def history_files(cache: Path, since: str = "") -> list:
    """The cached month files to build from: all of them, or those from month `since` (YYYY-MM) on. A file whose name
    carries no month (an 'upcoming' file) is always kept."""
    out = []
    for f in sorted(cache.glob("*.json.gz")):
        m = re.search(r"_(\d{4}-\d{2})\.json\.gz$", f.name)
        if since and m and m.group(1) < since:
            continue
        out.append(f)
    return out


def stage(cache: Path, rows, races, day: str, since: str = "") -> Path:
    """A temp directory holding links to the cached files (from month `since` on, when given) plus the day's rows, so
    load_topaz sees them together."""
    tmp = Path(tempfile.mkdtemp(prefix="topaz_today_"))
    for f in history_files(cache, since):
        (tmp / f.name).symlink_to(f.resolve())
    with gzip.open(tmp / "runs_VIC_upcoming.json.gz", "wt", encoding="utf-8") as fh:
        json.dump(rows, fh)
    with gzip.open(tmp / "races_VIC_upcoming.json.gz", "wt", encoding="utf-8") as fh:
        json.dump(races, fh)
    return tmp


MODEL_DIR = Path(os.environ.get("MODEL_DIR", "greyhound/cache/model"))


def train(d, label) -> int:
    """PRICE_MODE=train: fit the BSP-chance model on every resulted race and save it with the inputs it was fitted on,
    so the nightly price run only builds and predicts (founder, 5 Nov 2026: "train it every week overnight")."""
    import lightgbm as lgb  # noqa: F401  (the booster's save/load)
    os.environ.pop("WALK_LEAD_MODEL", None)     # the training rows' lead chance is always forward-chained, never in-sample
    df, num, rel, note = W.build_full(d)
    X = T.features(df, num, rel)
    today = pd.Timestamp.now(tz=SYDNEY).normalize().tz_localize(None)
    rec = 0.5 ** ((((today - df.date).dt.days) / 365.25).values / 3.0)
    bst = W.fit_fixed(X, df.p_mkt.values.astype(float), df.race_id, rec * W.label_weight(df), W.ROUNDS_A)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    bst.save_model(str(MODEL_DIR / "model.txt"))
    meta = {"cols": list(X.columns), "num": num, "rel": rel, "rounds": int(W.ROUNDS_A), "fit_races": int(df.race_id.nunique()),
            "last_day": f"{df.date.max():%Y-%m-%d}", "trained": pd.Timestamp.now(tz=SYDNEY).isoformat(timespec="minutes")}
    (MODEL_DIR / "meta.json").write_text(json.dumps(meta))
    if "p_lead" in num:
        lb, lcols = W.fit_lead_all(df, num, rel)
        lb.save_model(str(MODEL_DIR / "lead.txt"))
        (MODEL_DIR / "lead.txt.json").write_text(json.dumps({"cols": lcols}))
        note += f"\nlead model saved: {len(lcols)} inputs, {W.LEAD_ROUNDS} rounds on every one-leader race"
    else:
        for f in ("lead.txt", "lead.txt.json"):
            (MODEL_DIR / f).unlink(missing_ok=True)       # a stale lead model must not outlive the model it went with
    print(f"# {label}: trained\n\n{note}\nfitted on {meta['fit_races']:,} races to {meta['last_day']}, {meta['rounds']:,} rounds, "
          f"{len(meta['cols'])} inputs; saved to {MODEL_DIR}")
    return 0


def load_model():
    """The saved model and its meta, or (None, None)."""
    mf, jf = MODEL_DIR / "model.txt", MODEL_DIR / "meta.json"
    if not (mf.exists() and jf.exists()):
        return None, None
    import lightgbm as lgb
    return lgb.Booster(model_file=str(mf)), json.loads(jf.read_text())


def align(X: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Tonight's inputs in the saved model's order; an input tonight's build lacks (a preview word that fell out of
    the top 60) is blank, one the model never saw is dropped; categories stay categories."""
    out = X.reindex(columns=cols)
    for c in V1.CAT:
        if c in out:
            out[c] = out[c].astype("category")
    return out


def build_day(cache: Path, rows, races, day: str, since: str = ""):
    """build_full over the cached history (from `since` on) plus the day's rows; (df, num, rel, note, staged dir)."""
    tmp = stage(cache, rows, races, day, since)
    if os.environ.get("RACES_DIR"):
        os.environ["RACES_DIR"] = str(tmp)        # today's records beside the history's
    df, num, rel, note = W.build_full(str(tmp), keep_unresulted=True)
    return df, num, rel, note, tmp


def compare_prices(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    """Two builds' chances for the same card (race_id, dog, p_model each): how far apart, and do they pick the same dog."""
    m = a[["race_id", "dog", "p_model"]].merge(b[["race_id", "dog", "p_model"]], on=["race_id", "dog"], suffixes=("_a", "_b"))
    if m.empty:
        return dict(n=0, races=0, mean_abs=np.nan, max_abs=np.nan, top_same=0, corr=np.nan)
    d = (m.p_model_a - m.p_model_b).abs()
    top = m.groupby("race_id").apply(lambda g: g.dog.values[g.p_model_a.values.argmax()] == g.dog.values[g.p_model_b.values.argmax()])
    la, lb = np.log(m.p_model_a.clip(1e-9)), np.log(m.p_model_b.clip(1e-9))
    return dict(n=len(m), races=int(m.race_id.nunique()), mean_abs=float(d.mean()), max_abs=float(d.max()),
                top_same=int(top.sum()), corr=float(np.corrcoef(la, lb)[0, 1]) if len(m) > 1 else np.nan)


def main(d, label):
    if os.environ.get("PRICE_MODE", "").strip().lower() == "train":
        return train(d, label)
    day = os.environ.get("PRICE_DAY") or pd.Timestamp.now(tz=SYDNEY).strftime("%Y-%m-%d")
    client = TopazClient(max_per_minute=float(os.environ.get("TOPAZ_PER_MINUTE", "72") or 72))
    t_fetch = time.time()
    rows, races, names = fetch_day(client, day)
    print(f"# {label}: the model's prices for {day}\n")
    print(f"{len(races)} VIC races on {day} from /race/upcoming, {len(rows)} runners, {client.calls} calls in "
          f"{time.time() - t_fetch:,.0f}s")
    for k in ("race", "run", "form"):
        print(f"  {k} fields: {', '.join(names[k])}")
    missing = [c for c in NEED if rows and c not in rows[0]]
    if not rows or missing:
        print(f"\nCannot price: {'no runners' if not rows else 'the run rows lack ' + ', '.join(missing)}")
        return 1
    cache = Path(d)
    since = os.environ.get("PRICE_HISTORY_FROM", "").strip()
    since = "" if since.lower() == "all" else since      # "all": every cached month, 2013 on
    bst, meta = load_model()
    t0 = time.time()
    df, num, rel, note, tmp = build_day(cache, rows, races, day, since)
    today = df.date == pd.Timestamp(day)
    print(f"\n{note}\nbuilt from {since or 'the first cached month'} in {time.time() - t0:,.0f}s: {df.race_id.nunique():,} races; "
          f"tonight's card after the build: {df[today].race_id.nunique()} races, "
          f"{int(today.sum())} runners (a race drops out if a runner has no pre-race price or the field is under 4)\n")
    if not today.any():
        return 1
    tr = (~today).values
    X = T.features(df, num, rel)
    cmp_from = os.environ.get("PRICE_COMPARE_FROM", "").strip()
    if cmp_from and bst is not None:
        t1 = time.time()
        d2, n2, r2, _, _ = build_day(cache, rows, races, day, cmp_from)
        b2 = time.time() - t1
        t2 = d2.date == pd.Timestamp(day)
        pa = V1.race_softmax(bst.predict(align(X[today.values], meta["cols"]), raw_score=True), df.race_id.values[today.values])
        X2 = align(T.features(d2[t2], n2, r2), meta["cols"])
        pb = V1.race_softmax(bst.predict(X2, raw_score=True), d2.race_id.values[t2.values])
        c = compare_prices(df[today].assign(p_model=pa), d2[t2].assign(p_model=pb))
        print(f"history check: built from {cmp_from} in {b2:,.0f}s; {c['n']} runners in both builds; chance differs by "
              f"{c['mean_abs']:.2%} on average, {c['max_abs']:.2%} at most; the same top pick in {c['top_same']} of {c['races']} "
              f"races; correlation of log chances {c['corr']:.4f}\n")
    if bst is not None:
        X = align(X, meta["cols"])
        n_fit, how = meta["fit_races"], f"the saved model (trained {meta['trained']} on races to {meta['last_day']})"
    else:
        start = pd.Timestamp(day)
        rec = 0.5 ** ((((start - df.date[tr]).dt.days) / 365.25).values / 3.0)
        bst = W.fit_fixed(X[tr], df.p_mkt.values[tr].astype(float), df.race_id[tr], rec * W.label_weight(df[tr]), W.ROUNDS_A)
        n_fit, how = df.race_id[tr].nunique(), "a model fitted in this run (no saved model)"
    print(f"priced with {how}")
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
    contrib = bst.predict(X[today.values], pred_contrib=True)[:, :-1]          # per input, on the race-softmax scale
    fam = [family(c) for c in X.columns]
    print(f"fitted on {n_fit:,} races; the model's prices sum to 100% a race; "
          f"GRV's pre-race prices sum to {card.groupby('race_id').grv_pct.sum().median():.0%} a race (median book)")
    payload = card_payload(card, contrib, fam, book, day, n_fit,
                           [t.strip().upper() for t in os.environ.get("PRICE_TRACK", "SANDOWN").split(",") if t.strip()])
    payload["bets"], payload["blend"] = rule_bets(card)
    plain = json.dumps(payload, separators=(",", ":")).encode()
    lines, sha = seal(plain)
    print(f"tonight's card is sealed (GRV's values are personal use and this log is public): {len(payload['races'])} races "
          f"at {', '.join(payload['tracks']) or 'no track'}, {sum(len(r['r']) for r in payload['races'])} runners, "
          f"{len(payload['bets'])} rule bets across the card; {len(plain):,} bytes, sha256 {sha}; "
          f"{time.time() - t_fetch:,.0f}s from the first call")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz today"))
    except TopazError as e:
        print(f"Topaz refused or failed: {e}")
        sys.exit(1)
