"""Export every resulted race as a numeric dataset for modelling outside Actions. Read-only,
no Form King calls.

    python scripts/export_dataset.py [--state VIC] [--history history] [--out data/model_ds.npz]

One row per runner, grouped by race in date order:
  race_idx, race_id, date, track, distance, lws, going band, field size
  targets: bsp, sp, finish, and the opening price (for SCORING against the market only;
           it must never be a model input)
  X: every feature fk.backtest computes (runner.x) and every numeric raw value, plus the
     entry's own extras: age, sex, gear changes, every Form King record string as starts /
     wins / places, jockey and trainer figures, the speedmap row and the expected tempo
  P: the last 10 runs before the race date, [runner, run, field] (see PAST_FIELDS)
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import load_settings  # noqa: E402
from fk import backtest as B  # noqa: E402
from fk import fields as F  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
N_PAST = 10
PAST_FIELDS = ["days_before", "rating", "wfa", "wfaRat", "raceRating", "expected", "vsClass", "vsAllAvg", "vsTrack",
               "speedRating", "finishingSpeed", "last600", "to600", "distance", "going_band", "finish", "runners",
               "margin", "bsp", "sp", "settle", "pos800", "pos400", "barrier", "weight", "trial", "same_track",
               "prize", "field_strength", "prep", "track_speed"]
GOING_CODE = {"good": 1.0, "soft": 2.0, "heavy": 3.0, "synthetic": 4.0}
SEX_CODE = {"G": 1.0, "C": 2.0, "H": 3.0, "F": 4.0, "M": 5.0, "R": 6.0}


def num(v):
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def record(txt):
    """'12:3-2-1' -> (12, 3, 2, 1)."""
    try:
        s, rest = str(txt).split(":")
        w, p2, p3 = rest.split("-")
        return int(s), int(w), int(p2), int(p3)
    except (ValueError, AttributeError):
        return None


def entry_extras(e: dict, sm_row: dict | None, tempo: dict | None) -> dict:
    out = {}
    horse = e.get("horse") or {}
    out["age"] = num(horse.get("age"))
    out["calc_age"] = num(horse.get("calculatedAge"))
    out["sex"] = SEX_CODE.get(str(horse.get("type") or "")[:1].upper())
    gear = e.get("gear") or []
    out["gear_first_time"] = float(sum(1 for g in gear if isinstance(g, dict) and "FIRST" in str(g.get("change") or "")))
    out["gear_changes"] = float(sum(1 for g in gear if isinstance(g, dict) and g.get("change") and g.get("change") != "STAYING_ON"))
    out["blinkers_first"] = float(any(isinstance(g, dict) and "blinker" in str(g.get("gear") or "").lower()
                                      and "FIRST" in str(g.get("change") or "") for g in gear))
    for k in ("apprenticeClaim", "daysSinceLastRace", "daysSinceLastWin", "raceInPrep", "weight", "weightCarried",
              "ridingWeight", "barrier", "benchmarkRating", "averagePrizeMoney", "totalPrizeMoney", "wfaDiff"):
        out[k] = num(e.get(k))
    for k in ("dualAcceptor", "emergency", "firstStarter", "apprenticeJockey", "jockeysOnlyRideAtMeeting",
              "trainersOnlyRaceAtMeeting"):
        out[k] = 1.0 if e.get(k) else 0.0
    rat = e.get("ratings") or {}
    for k in ("neural", "peak", "peak12m"):          # exp is market-derived: never exported
        out[f"rating_{k}"] = num(rat.get(k))
    form = e.get("form") or {}
    for k, v in form.items():
        if isinstance(v, str):
            rec = record(v)
            if rec:
                out[f"f_{k}_s"], out[f"f_{k}_w"], out[f"f_{k}_p"] = float(rec[0]), float(rec[1]), float(rec[2] + rec[3])
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out[f"f_{k}"] = float(v)
        elif isinstance(v, dict):
            for kk, vv in v.items():
                rec = record(vv)
                if rec:
                    out[f"f_{k}_{kk}_s"], out[f"f_{k}_{kk}_w"] = float(rec[0]), float(rec[1])
    for who in ("jockeyForm", "trainerForm"):
        d = e.get(who) or {}
        for k, v in d.items():
            n = num(v)
            if n is not None and not isinstance(v, bool):
                out[f"{who}_{k}"] = n
            rec = record(v) if isinstance(v, str) else None
            if rec:
                out[f"{who}_{k}_s"], out[f"{who}_{k}_w"] = float(rec[0]), float(rec[1])
    tsg = e.get("trackSpeedGoingForm") or {}
    for kk, vv in tsg.items():
        rec = record(vv)
        if rec:
            out[f"tsg_{kk}_s"], out[f"tsg_{kk}_w"] = float(rec[0]), float(rec[1])
    sm_row = sm_row or {}
    for k in ("early_speed", "pir", "median_vs_benchmark", "predicted_position"):
        out[f"sm_{k}"] = num(sm_row.get(k))
    tempo = tempo or {}
    out["tempo_min"], out["tempo_max"] = num(tempo.get("min")), num(tempo.get("max"))
    return out


# Every benchmarked section of each past run, in lengths against the class par, the leader
# and the field (positive = faster). Kept apart from P (in S, named by SEC_FIELDS) so the
# models already trained on P see exactly the inputs they were trained on.
SEC_KEYS = ["S-8", "12-10", "10-8", "8-6", "6-4", "4-2", "2-F", "8-4", "S-6", "6-F", "4-F", "8-F"]
SEC_METRICS = ["vsClass", "vsLeader", "vsField"]
SEC_FIELDS = [f"{k}|{m}" for k in SEC_KEYS for m in SEC_METRICS]


def past_sections(e: dict, race_date: str) -> np.ndarray:
    """The same last N_PAST runs past_runs reads, newest first: [run, SEC_FIELDS]."""
    arr = np.full((N_PAST, len(SEC_FIELDS)), np.nan, dtype=np.float32)
    runs = []
    for p in F.entry_past_events(e):
        if str(p.get("scratched")).lower() == "true" or p.get("scratched") is True:
            continue
        d = F.past_event_date(p)
        if not d or d >= race_date:
            continue
        runs.append((d, p))
    runs.sort(key=lambda t: t[0], reverse=True)
    for i, (_, p) in enumerate(runs[:N_PAST]):
        b = F.past_event_benchmark(p) or {}
        secs = b.get("sections") if isinstance(b.get("sections"), dict) else {}
        for j, name in enumerate(SEC_FIELDS):
            k, m = name.split("|")
            v = num((secs.get(k) or {}).get(m)) if isinstance(secs.get(k), dict) else None
            if v is not None:
                arr[i, j] = v
    return arr


def past_ids(e: dict, race_date: str) -> tuple[list[str], list[str]]:
    """(race ids, jockey names) of the same last N_PAST runs past_runs reads, newest first."""
    runs = []
    for p in F.entry_past_events(e):
        if str(p.get("scratched")).lower() == "true" or p.get("scratched") is True:
            continue
        d = F.past_event_date(p)
        if not d or d >= race_date:
            continue
        runs.append((d, p))
    runs.sort(key=lambda t: t[0], reverse=True)
    ids = [str(p.get("raceId") or "") for _, p in runs[:N_PAST]]
    jk = [str(p.get("jockey") or "") for _, p in runs[:N_PAST]]
    return ids + [""] * (N_PAST - len(ids)), jk + [""] * (N_PAST - len(jk))


def past_runs(e: dict, race_date: str, track: str) -> np.ndarray:
    arr = np.full((N_PAST, len(PAST_FIELDS)), np.nan, dtype=np.float32)
    runs = []
    for p in F.entry_past_events(e):
        if str(p.get("scratched")).lower() == "true" or p.get("scratched") is True:
            continue
        d = F.past_event_date(p)
        if not d or d >= race_date:
            continue
        runs.append((d, p))
    runs.sort(key=lambda t: t[0], reverse=True)
    from datetime import date
    rd = date.fromisoformat(race_date[:10])
    for i, (d, p) in enumerate(runs[:N_PAST]):
        r = F.run_ratings(p)
        pos = r.get("positions") or [None] * 8
        rating = next((r[k] for k in ("adjToday", "atWeights", "wfaRat", "wfa") if r.get(k) is not None), None)
        vals = {"days_before": (rd - date.fromisoformat(d[:10])).days, "rating": rating,
                "going_band": GOING_CODE.get(B.going_band(p.get("going"))), "margin": num(p.get("margin")),
                "bsp": num(p.get("bsp")), "sp": num(p.get("startingPrice")), "settle": pos[0] if len(pos) > 0 else None,
                "pos800": pos[3] if len(pos) > 3 else None, "pos400": pos[5] if len(pos) > 5 else None,
                "barrier": num(p.get("barrier")), "weight": num(p.get("weight")), "trial": 1.0 if r.get("trial") else 0.0,
                "same_track": 1.0 if (r.get("track") or "").lower() == (track or "").lower() else 0.0,
                "prize": num(p.get("totalPrizemoney")), "field_strength": num(p.get("fieldStrength")),
                "prep": num(p.get("raceInPrep")), "track_speed": num(p.get("trackSpeed"))}
        for k in ("wfa", "wfaRat", "raceRating", "expected", "vsClass", "vsAllAvg", "vsTrack", "speedRating",
                  "finishingSpeed", "last600", "to600", "distance", "finish", "runners"):
            vals[k] = r.get(k)
        for j, f in enumerate(PAST_FIELDS):
            v = num(vals.get(f))
            if v is not None and not (f in ("bsp", "sp") and v <= 1.0) and not (f in ("finish", "runners") and v <= 0):
                arr[i, j] = v
    return arr


def upcoming_rows(db, day: str, track: str | None, state: str) -> list[dict]:
    """Rows shaped like Db.resulted_races for the races on `day` (not yet run), optionally one track."""
    races = db.conn.execute(
        """select r.race_id, m.meeting_date, m.track, r.distance_m, (r.raw->>'lws')::numeric,
                  sm.runners, sm.raw->'expectedTempo',
                  nullif(trim(concat(r.raw->>'going', ' ', r.raw->>'goingNumber')), ''), r.race_number
           from fk.races r join fk.meetings m using (meeting_id)
                left join fk.speedmaps sm on sm.race_id = r.race_id
           where m.meeting_date = %s and m.state = %s and (%s::text is null or m.track ilike %s)
           order by r.race_number""", (day, state, track, track)).fetchall()
    out = []
    for r in races:
        ents = [x[0] for x in db.conn.execute("select e.raw from fk.entries e where e.race_id = %s order by e.barrier nulls last", (r[0],))]
        out.append({"race_id": r[0], "date": str(r[1]), "track": r[2], "distance_m": r[3],
                    "lws": float(r[4]) if r[4] is not None else None, "entries": ents, "speedmap": r[5], "tempo": r[6],
                    "going": r[7], "race_number": r[8]})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--history", default=str(ROOT / "history"))
    ap.add_argument("--out", default=str(ROOT / "data" / "model_ds.npz"))
    ap.add_argument("--date", help="export the races on this day instead (not yet run), for pricing")
    ap.add_argument("--track", help="with --date: only this track")
    a = ap.parse_args()
    from backtest import races_from_rows
    from fk import history as H
    from fk.db import Db
    db = Db(load_settings().database_url)
    if a.date:
        rows = upcoming_rows(db, a.date, a.track, a.state)
    else:
        rows = list(db.resulted_races(a.state))
        in_db = {r["race_id"] for r in rows}
        rows += list(H.resulted_races(Path(a.history), a.state, skip=in_db))
        B.fill_going(rows)
    try:
        pre = set(db.races_pulled_before_the_jump(a.state))
    except Exception as ex:  # noqa: BLE001
        print(f"pulled-before-the-jump flag unavailable: {ex}")
        pre = set()
    by_id = {r["race_id"]: r for r in rows}
    races, _ = races_from_rows(rows)
    if not a.date:
        races = [r for r in races if B.bsp_chances(r.runners) and B.winner_chances(r.runners)]
    races.sort(key=lambda r: (r.date, r.race_id))
    print(f"{len(races)} races" + ("" if a.date else " with BSP and a winner"), flush=True)

    recs, pasts, meta, secs = [], [], [], []
    past_race_ids, past_jockeys, jockeys, trainers = [], [], [], []
    sires, dam_sires, locs = [], [], []
    xkeys, extra_keys = set(), set()
    for ri, race in enumerate(races):
        row = by_id[race.race_id]
        ent = {F.horse_id(e): e for e in row["entries"]}
        sm = {s.get("horse_id"): s for s in (row.get("speedmap") or []) if isinstance(s, dict)}
        for r in race.runners:
            e = ent.get(r.horse_id) or {}
            raw = {f"raw_{k}": num(v) for k, v in r.raw.items() if not isinstance(v, (list, dict))}
            ex = entry_extras(e, sm.get(r.horse_id), row.get("tempo"))
            xkeys |= set(r.x)
            extra_keys |= set(raw) | set(ex)
            recs.append((ri, r, raw, ex))
            pasts.append(past_runs(e, str(race.date)[:10], race.track))
            secs.append(past_sections(e, str(race.date)[:10]))
            ids, jk = past_ids(e, str(race.date)[:10])
            past_race_ids.append(ids); past_jockeys.append(jk); jockeys.append(str(e.get("jockey") or ""))
            trainers.append(str(e.get("trainer") or ""))
            h = e.get("horse") or {}
            sires.append(str(h.get("sire") or "")); dam_sires.append(str(h.get("sireOfDam") or ""))
            locs.append(str(h.get("trainingLocation") or ""))
        meta.append((race.race_id, str(race.date)[:10], race.track or "", float(getattr(race, "distance_m", None) or np.nan),
                     num(getattr(race, "lws", None)) or np.nan, GOING_CODE.get(B.going_band(row.get("going"))) or np.nan,
                     len(race.runners)))
    barred = {"open_logit", "market_prob", "market_x_neural", "first_starter_x_market", "exp_rel", "raw_open", "raw_exp"}
    xcols = sorted(k for k in xkeys if k not in barred and not k.startswith("collateral"))
    ecols = sorted(k for k in extra_keys if k not in barred and "collateral" not in k)
    X = np.full((len(recs), len(xcols) + len(ecols)), np.nan, dtype=np.float32)
    for i, (_, r, raw, ex) in enumerate(recs):
        for j, k in enumerate(xcols):
            v = r.x.get(k)
            if v is not None:
                X[i, j] = v
        for j, k in enumerate(ecols):
            v = raw.get(k, ex.get(k))
            if v is not None:
                X[i, len(xcols) + j] = v
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out, X=X, cols=np.array(xcols + ecols), P=np.stack(pasts), past_fields=np.array(PAST_FIELDS),
        S=np.stack(secs) if secs else np.zeros((0, N_PAST, len(SEC_FIELDS)), np.float32), sec_fields=np.array(SEC_FIELDS),
        race_idx=np.array([t[0] for t in recs], dtype=np.int32),
        horse_id=np.array([t[1].horse_id for t in recs]), name=np.array([t[1].name for t in recs]),
        bsp=np.array([t[1].bsp or np.nan for t in recs], dtype=np.float64),
        sp=np.array([t[1].sp or np.nan for t in recs], dtype=np.float64),
        finish=np.array([t[1].finish or 0 for t in recs], dtype=np.int32),
        open=np.array([num(t[1].raw.get("open")) or np.nan for t in recs], dtype=np.float64),
        race_id=np.array([m[0] for m in meta]), date=np.array([m[1] for m in meta]), track=np.array([m[2] for m in meta]),
        distance=np.array([m[3] for m in meta]), lws=np.array([m[4] for m in meta]), going=np.array([m[5] for m in meta]),
        field=np.array([m[6] for m in meta], dtype=np.int32),
        pre_jump=np.array([(m[0] in pre) or bool(a.date) for m in meta]),
        race_number=np.array([by_id[m[0]].get("race_number") or 0 for m in meta], dtype=np.int32),
        past_race_ids=np.array(past_race_ids), past_jockeys=np.array(past_jockeys),
        jockey=np.array(jockeys), trainer=np.array(trainers),
        sire=np.array(sires), dam_sire=np.array(dam_sires), training_location=np.array(locs),
    )
    print(f"wrote {out}: {X.shape[0]} runners, {X.shape[1]} columns ({len(xcols)} model features), "
          f"{len(meta)} races, past runs {np.stack(pasts).shape}; {out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
