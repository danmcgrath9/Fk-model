"""Get Horse Form for the last-start race-mates whose next run we cannot see (11 Nov 2026, founder: "Everything
except the field watcher": full histories for every horse's last-start race-mates, so the form-line test can be
redone properly). The horses come from scripts/racemates.py: OPEN race-mates, the ones closing the most open
slots first. Each fetch stores the horse's full race career in fk.past_events (the writer the daily pull uses).

    python scripts/horse_batch.py --key live --yes [--max 290] [--history history] [--dry-run]

2 credits a horse at numBenchmarks=5. Unattended, the per-run cap (FK_MAX_CREDITS_PER_RUN) and the balance floor
(FK_MIN_BALANCE) trim the batch before the first paid call. Run it again for the next horses: a fetched horse is
settled (its stored runs now reach today), so it never comes back.

What it does NOT touch: fk.horses (profile_fetched_at stays as it was, so a horse never profiled still gets its
first-sight ten-run profile the day it appears on a Victorian card) and the training data (the dataset is built from
each race card's own form as it stood on race day, never from fk.past_events)."""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import bootstrap, confirm, make_client  # noqa: E402
from daily_pull import store_past_events  # noqa: E402
from fk import fields as F  # noqa: E402
from fk import ops  # noqa: E402
from fk.db import Db  # noqa: E402
from fk.estimate import estimate  # noqa: E402
from fk.guard import credit_cap, fit_under_cap, time_budget_seconds  # noqa: E402
from fk.pace import run_batch  # noqa: E402
import racemates as RM  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", choices=["test", "live"], default="test")
    ap.add_argument("--max", type=int, default=290)
    ap.add_argument("--history", default="history")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    runs, fields, horizon, runners = RM.load(a.history)
    RM.index_partial(runs, fields)
    rows, benefit = RM.analyse(runs, fields, horizon, runners)
    ranked = benefit.most_common()
    print(f"open race-mate slots {sum(benefit.values())} across {len(ranked)} horses ({time.time() - t0:.0f}s)")
    pick = [h for h, _ in ranked[:a.max]]
    if not pick:
        print("nothing open"); return
    print(f"this batch: {len(pick)} horses closing {sum(n for _, n in ranked[:a.max])} slots; "
          f"next after it closes {ranked[a.max][1] if len(ranked) > a.max else 0}")

    settings, spec, costs, ledger = bootstrap(a.key)
    db = Db(settings.database_url)
    client = make_client(a.key, settings, spec, costs, ledger, allow_live=False)
    live = client.key_kind == "live"
    plans = [(h, client.plan(ops.HORSE_FORM, horseId=h, numBenchmarks=5, racesOnly=False)) for h in pick]
    if a.yes and live:
        n_fit = fit_under_cap([p.credits for _, p in plans], ledger.balance(), cap=credit_cap())
        if n_fit < len(plans):
            print(f"credit cap: {n_fit} of {len(plans)} this run")
            plans = plans[:n_fit]
    est = estimate([p for _, p in plans])
    print(est.render(ledger.balance() if live else None))
    if a.dry_run or not plans:
        print("dry run: nothing fetched"); return
    if not confirm(f"Get Horse Form for {len(plans)} horses?", a.yes, estimated=est.total, balance=ledger.balance(), live=live):
        sys.exit("stopped")
    client.allow_live = True
    try:
        batch = run_batch(plans, lambda item: client.execute(item[1]), workers=4, per_second=1.0, budget_seconds=time_budget_seconds())
    finally:
        client.allow_live = False
    events = 0
    for (h, _), payload in batch.done:
        ev = F.horse_form_past_events(payload)
        store_past_events(db, h, ev, datetime.now(timezone.utc))
        events += len(ev)
    db.commit()
    for (h, p), e in batch.failed:
        print(f"FAILED {h}: {getattr(e, 'status', '')} {str(e)[:120]}")
    print(f"fetched {len(batch.done)}, failed {len(batch.failed)}, left for the next run {len(batch.skipped)}; "
          f"{events} past events stored")
    print(f"ledger balance {ledger.balance()}")


if __name__ == "__main__":
    main()
