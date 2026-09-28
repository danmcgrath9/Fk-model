"""Are lightly raced winners, especially 3-year-olds first-up, underrated? Read-only, no Form
King calls.

    python scripts/debut_winner_study.py [--state VIC] [--history history]

The question (founder, 28 Sep 2026, on Cavill Avenue): a horse that wins its only start as a
2-year-old and is put away usually comes back a better horse at three. Does the form price
know that, and does the market?

Every resulted race is priced out of sample by the form price's recipe (config/form_price.json:
its features, ridge and target), fitted five times, each time on the other four date blocks.
Runners are then grouped by age, starts, wins and whether they are first-up, and for each
group the ACTUAL winners are set against the winners each price EXPECTED (the sum of its
chances). A ratio above 1 means the group wins more often than that price says: the price
underrates it. One unit on every runner in the group is settled at the opening price and at
Betfair SP, so the gap can be read in money as well.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import load_settings  # noqa: E402
from fk import backtest as B  # noqa: E402
from fk import fields as F  # noqa: E402
from fit_form_only import TARGETS, fit_np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FOLDS = 5


def load(state: str, history_dir: Path):
    """The races, as the back-test builds them, and each runner's entry keyed by race and horse,
    for the age, the career record and the run in the campaign."""
    from backtest import races_from_rows
    from fk import history as H
    from fk.db import Db
    db = Db(load_settings().database_url)
    rows = list(db.resulted_races(state))
    in_db = {row["race_id"] for row in rows}
    rows += list(H.resulted_races(history_dir, state, skip=in_db))
    entries = {row["race_id"]: {F.horse_id(e): e for e in row["entries"]} for row in rows}
    races, _ = races_from_rows(rows)
    races = [r for r in races if B.winner_chances(r.runners) and B.bsp_chances(r.runners)]
    races.sort(key=lambda r: (r.date, r.race_id))
    return races, entries


def career(e: dict) -> tuple[int, int] | None:
    rec = B._form_record(F.entry_form_record(e).get("careerForm"))
    return rec


def profile(e: dict) -> dict:
    ctx = F.entry_context(e)
    rec = career(e)
    starts, wins = (rec if rec else (None, None))
    prep = ctx.get("runInPrep")
    days = F.entry_days_since_last_run(e)
    first_up = prep == 1 or (prep is None and days is not None and days >= 84)
    return {"age": ctx.get("age"), "starts": starts, "wins": wins, "first_up": first_up}


GROUPS = [
    ("every runner", lambda p: True),
    ("3yo, 1 start, 1 win, first-up  (the Cavill Avenue profile)",
     lambda p: p["age"] == 3 and p["starts"] == 1 and p["wins"] == 1 and p["first_up"]),
    ("3yo, 1 to 3 starts, a win, first-up",
     lambda p: p["age"] == 3 and p["starts"] and 1 <= p["starts"] <= 3 and (p["wins"] or 0) >= 1 and p["first_up"]),
    ("3yo, 1 to 3 starts, a win, NOT first-up",
     lambda p: p["age"] == 3 and p["starts"] and 1 <= p["starts"] <= 3 and (p["wins"] or 0) >= 1 and not p["first_up"]),
    ("any age, 1 to 3 starts, a win, first-up",
     lambda p: p["starts"] and 1 <= p["starts"] <= 3 and (p["wins"] or 0) >= 1 and p["first_up"]),
    ("4yo+, 1 to 3 starts, a win, first-up",
     lambda p: (p["age"] or 0) >= 4 and p["starts"] and 1 <= p["starts"] <= 3 and (p["wins"] or 0) >= 1 and p["first_up"]),
    ("3yo, 1 to 3 starts, no win, first-up",
     lambda p: p["age"] == 3 and p["starts"] and 1 <= p["starts"] <= 3 and (p["wins"] or 0) == 0 and p["first_up"]),
    ("every 3yo first-up", lambda p: p["age"] == 3 and p["first_up"]),
    ("2yo, 1 start, 1 win", lambda p: p["age"] == 2 and p["starts"] == 1 and p["wins"] == 1),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--history", default=str(ROOT / "history"))
    a = ap.parse_args()
    cfg = json.loads((ROOT / "config" / "form_price.json").read_text())
    target = TARGETS[cfg.get("fitted_to", "bsp")]
    races, entries = load(a.state, Path(a.history))
    n = len(races)
    blocks = [races[i * n // FOLDS:(i + 1) * n // FOLDS] for i in range(FOLDS)]
    print(f"{n} resulted races ({races[0].date} to {races[-1].date}), each priced by the form price "
          f"({cfg['model']}, fitted to {cfg.get('fitted_to', 'bsp')}) fitted on the other {FOLDS - 1} date blocks.\n")

    rows = []   # (profile, form p, open p, bsp p, won, open price, bsp)
    for k, block in enumerate(blocks):
        train = [r for j, b in enumerate(blocks) if j != k for r in b]
        beta = fit_np(train, cfg["features"], cfg["ridge"], target=target)
        for race in block:
            fp = B.predict(beta, race.runners)
            op = B.market_probs([race])[0]
            bp = B.bsp_chances(race.runners)
            for r, f, o, b in zip(race.runners, fp, op, bp):
                e = entries.get(race.race_id, {}).get(r.horse_id)
                if e is None:
                    continue
                rows.append((profile(e), f, o, b, r.finish == 1, r.raw.get("open"), r.bsp or r.sp))

    print("A/E = actual winners / winners that price expected. Above 1: the group wins MORE than the price says "
          "(the price underrates it). Profit: one unit on every runner in the group.\n")
    print("| group | runners | winners | A/E form price | A/E opening market | A/E BSP | profit at open | profit at BSP |")
    print("|---|---|---|---|---|---|---|---|")
    for name, test in GROUPS:
        g = [x for x in rows if test(x[0])]
        if not g:
            print(f"| {name} | 0 | | | | | | |")
            continue
        wins = sum(x[4] for x in g)
        ef, eo, eb = (sum(x[i] for x in g) for i in (1, 2, 3))
        at_open = [x for x in g if x[5] and x[5] > 1]
        po = (sum(x[5] for x in at_open if x[4]) - len(at_open)) / len(at_open) if at_open else float("nan")
        at_bsp = [x for x in g if x[6] and x[6] > 1]
        pb = (sum(x[6] for x in at_bsp if x[4]) - len(at_bsp)) / len(at_bsp) if at_bsp else float("nan")
        se = math.sqrt(wins) / wins if wins else float("nan")   # rough relative margin on A/E
        print(f"| {name} | {len(g)} | {wins} | {wins / ef:.2f} | {wins / eo:.2f} | {wins / eb:.2f} | "
              f"{po:+.1%} | {pb:+.1%} |")
        if len(g) < 200 and name != "every runner":
            print(f"|  (margin of luck on A/E about ±{se:.0%}) | | | | | | | |")


if __name__ == "__main__":
    main()
