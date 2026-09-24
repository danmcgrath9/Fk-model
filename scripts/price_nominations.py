"""Price a NOMINATION list on the form-only price, before acceptances. Read-only.

    python scripts/price_nominations.py --file data/nominations/X.txt --distance 1200 --date 2026-09-30

A nomination has no barrier, weight, rider or Form King race form yet, so each horse is
rated off its most recent Form King entry we hold (the database first, then the history
files), with the figures that belong to that OTHER race cleared: barrier, weight, rider,
days since the last run, run in the campaign, weight-for-age difference and the intent
flags all take the field average. A horse we hold nothing on is listed unpriced rather than
guessed at (it may be unraced, or have raced where we have not pulled). The prices are
across every priced nomination, so they shorten when the field is cut.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fk import backtest as B  # noqa: E402
from fk import fields as F  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
# Raw figures that describe the race the stored entry was for, not the one being priced.
OTHER_RACE = ["barrier", "weight_rel", "days_log", "run_in_prep", "wfa_diff", "jockey_win", "jt_combo_win", "exp", "open",
              "trainer_only", "jockey_only", "apprentice_claim", "dual_acceptor", "emergency"]


def key(name: str) -> str:
    """'Prolocutor (NZ)' and "He's On Point" -> 'prolocutor', 'hesonpoint'."""
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\(.*?\)", "", name.lower()))


def latest_entries(names: list[str], history_dir: Path | None) -> dict[str, tuple[str, dict]]:
    """{name key: (date, entry raw)} for the newest stored entry of each nominated horse."""
    want = {key(n) for n in names}
    found: dict[str, tuple[str, dict]] = {}

    def offer(k, date, raw):
        if k in want and (k not in found or date > found[k][0]):
            found[k] = (date, raw)
    try:
        from _common import load_settings
        from fk.db import Db
        db = Db(load_settings().database_url)
        for name, date, raw in db.conn.execute(
                """select h.name, m.meeting_date::text, e.raw
                   from fk.entries e join fk.horses h using (horse_id) join fk.races r using (race_id)
                        join fk.meetings m using (meeting_id)
                   where regexp_replace(regexp_replace(lower(h.name), '\\(.*?\\)', '', 'g'), '[^a-z0-9]', '', 'g') = any(%s)""",
                (sorted(want),)):
            offer(key(name), date, raw)
    except Exception as ex:  # noqa: BLE001
        print(f"database skipped: {type(ex).__name__}: {ex}")
    if history_dir and history_dir.exists():
        from fk import history as H
        for p in H.files(history_dir):
            for b in H.read_file(p):
                for e in b.get("entries") or []:
                    offer(key(F.horse_name(e) or ""), str(b.get("date") or p.name[:10]), e)
    return found


def _record(runs: list[dict]) -> str:
    """Form King's record string, 'starts: wins-seconds-thirds-other'."""
    fin = [r.get("finish") for r in runs]
    w, s2, t = sum(f == 1 for f in fin), sum(f == 2 for f in fin), sum(f == 3 for f in fin)
    return f"{len(fin)}: {w}-{s2}-{t}-{len(fin) - w - s2 - t}"


def refreshed(entry: dict, fresh_events: list[dict], race_date: str | None, distance: int | None, track: str | None) -> dict:
    """The stored entry brought up to date with a fresh Get Horse Form: its past events
    replaced by the full career list (runs before race_date only), the career, distance
    and track records and the peak ratings recomputed from those runs, and the official
    handicap rating taken from the latest run. When the horse has RACED since the stored
    entry, that entry's Neural rating predates runs we now hold, so it is dropped (the
    field average stands in) rather than pricing a winner off its pre-race rating."""
    from fk.trend import rating_series
    events = [p for p in fresh_events if (F.past_event_date(p) or "") < (race_date or "9999")]
    old_dates = {F.past_event_date(p) for p in F.entry_past_events(entry)}
    runs = sorted([F.run_ratings(p) for p in events if F.past_event_date(p)], key=lambda r: r["date"])
    races = [r for r in runs if not r.get("trial") and r.get("finish")]
    new_races = [r for r in races if r["date"] not in old_dates]
    out = {**entry, "pastEvents": events}
    form = dict(entry.get("form") or {})
    form["careerForm"] = _record(races)
    if distance:
        form["distanceForm"] = _record([r for r in races if r.get("distance") and abs(float(r["distance"]) - distance) <= 50])
    if track:
        form["trackForm"] = _record([r for r in races if (r.get("track") or "").lower().startswith(track.lower())])
    out["form"] = form
    series = [v for v in rating_series(runs) if v is not None]
    ratings = dict(entry.get("ratings") or {})
    if series:
        ratings["peak"] = max([series[-1], *(v for v in [ratings.get("peak")] if v is not None), *series])
        recent = [v for r, v in zip([r for r in runs if not r.get("trial")], rating_series(runs)) if v is not None
                  and race_date and r["date"] >= f"{int(race_date[:4]) - 1}{race_date[4:]}"]
        if recent:
            ratings["peak12m"] = max(recent)
    if new_races:
        ratings["neural"] = None
    out["ratings"] = ratings
    ohr = next((p.get("benchmarkRating") for p in sorted(events, key=lambda p: F.past_event_date(p) or "", reverse=True)
                if p.get("benchmarkRating")), None)
    if ohr:
        out["benchmarkRating"] = ohr
    return out


def fetch_fresh(horse_ids: list[str], key: str) -> dict[str, list[dict]]:
    """One Get Horse Form per horse (2 credits at five benchmarked runs), stored the way the
    daily pull stores them. Guarded by the credit cap and the balance floor."""
    from datetime import datetime, timezone
    from _common import bootstrap, confirm, make_client
    from daily_pull import store_past_events
    from fk import ops
    from fk.db import Db
    settings, spec, costs, ledger = bootstrap(key)
    db = Db(settings.database_url)
    client = make_client(key, settings, spec, costs, ledger, allow_live=False)
    held = {}
    for h, raw in db.conn.execute("select horse_id, raw from fk.horses where horse_id = any(%s) and profile_fetched_at > now() - interval '12 hours'",
                                  (horse_ids,)):
        if raw and F.horse_form_past_events(raw):
            held[h] = F.horse_form_past_events(raw)
    if held:
        print(f"{len(held)} horses already fetched in the last 12 hours, not paid for again")
    horse_ids = [h for h in horse_ids if h not in held]
    plans = [(h, client.plan(ops.HORSE_FORM, horseId=h, numBenchmarks=5, racesOnly=False)) for h in horse_ids]
    total = sum(p.credits for _, p in plans)
    if not confirm(f"Get Horse Form for {len(plans)} horses ({total} credits)?", True, estimated=total,
                   balance=ledger.balance(), live=client.key_kind == "live"):
        raise SystemExit("stopped by the credit guard")
    out, payloads = {}, {}
    client.allow_live = True
    try:
        for h, plan in plans:
            payload = client.execute(plan)
            out[h] = F.horse_form_past_events(payload)
            payloads[h] = payload
    finally:
        client.allow_live = False
    # Stored so the next run need not pay again; the horse row goes in first (a horse held
    # only in the history files has none, and past_events needs one). A failed store never
    # costs the price: the fetched form is already in hand.
    try:
        at = datetime.now(timezone.utc)
        for h, payload in payloads.items():
            db.upsert("horses", ["horse_id"], dict(horse_id=h, name=F.horse_form_name(payload) or h, profile_depth=5,
                                                   profile_fetched_at=at, raw=payload, fetched_at=at))
        db.commit()
        for h, events in out.items():
            store_past_events(db, h, events, at)
        db.commit()
    except Exception as ex:  # noqa: BLE001
        print(f"fresh form not stored ({type(ex).__name__}: {str(ex)[:160]}); pricing with it anyway")
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
    print(f"fresh horse form for {len(out)} horses, {total} credits; balance {ledger.balance()}")
    return {**held, **out}


def price(names: list[str], found: dict, model: dict, distance: int | None, date: str | None, lws: float | None):
    from fk import projection as P
    runners, source = [], {}
    for n in names:
        k = key(n)
        r = None
        if k in found:
            r = B.runner_from_entry(found[k][1], distance, lws, date)
        if r is None:
            continue
        source[k] = f"latest entry {found[k][0]}"
        for f in OTHER_RACE:
            r.raw[f] = None
        r.horse_id, r.name = k, n
        runners.append(r)
    B.race_features(runners)
    B.shape_features(runners, {}, P.tempo_score(None))
    p = B.predict(model["beta"], runners)
    return sorted(((pi, r.name, source[r.horse_id]) for r, pi in zip(runners, p)), reverse=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--distance", type=int)
    ap.add_argument("--date")
    ap.add_argument("--lws", type=float)
    ap.add_argument("--history", default=str(ROOT / "history"))
    ap.add_argument("--track", help="today's track, for the track record")
    ap.add_argument("--refresh", choices=["test", "live"], help="pay for fresh horse form on every horse whose stored entry has run")
    ap.add_argument("--today", help="entries dated before this have run (default: today in Melbourne)")
    a = ap.parse_args()
    names = [ln.strip() for ln in Path(a.file).read_text(encoding="utf-8").splitlines() if ln.strip()]
    model = json.loads((ROOT / "config" / "form_price.json").read_text())
    found = latest_entries(names, Path(a.history))
    if a.refresh:
        # An entry for a race still to come already carries the horse's form up to now; only
        # an entry whose race has been RUN is out of date. Today is Melbourne's date.
        from _common import now_melbourne
        today = a.today or now_melbourne().date().isoformat()
        stale = {k: F.horse_id(e) for k, (d, e) in found.items() if d[:10] < today}
        fresh = fetch_fresh(sorted(set(stale.values())), a.refresh)
        for k, hid in stale.items():
            if fresh.get(hid):
                d, e = found[k]
                found[k] = (f"{d}, refreshed", refreshed(e, fresh[hid], a.date, a.distance, a.track))
    rows = price(names, found, model, a.distance, a.date, a.lws)
    print(f"{Path(a.file).stem}: {len(names)} nominations, {len(found)} with a Form King record; model {model['model']}\n")
    print("| rank | horse | Form $ | Take at | rated off |")
    print("|---|---|---|---|---|")
    for i, (pi, name, src) in enumerate(rows, 1):
        fp = 1 / pi
        print(f"| {i} | {name} | {fp:.2f} | {fp * 1.2:.2f} | {src} |")
    missing = [n for n in names if key(n) not in {key(r[1]) for r in rows}]
    if missing:
        print(f"\nNot priced, no Form King record held: {', '.join(missing)}")
    print("\nJSON " + json.dumps([{"horse": n, "prob": round(pi, 5), "source": s} for pi, n, s in rows]))


if __name__ == "__main__":
    main()
