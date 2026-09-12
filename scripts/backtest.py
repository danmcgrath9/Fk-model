"""Fit the rated price to Betfair SP over every resulted race stored, score it against the
winners, and write the model the report uses (config/rated_price.json) plus a readable
report (docs/BACKTEST.md). No Form King calls: it reads the database only.

    python scripts/backtest.py            # fit and write
    python scripts/backtest.py --dry      # fit and print, write nothing
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from _common import load_settings
from fk import backtest as B

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "config" / "rated_price.json"
REPORT_PATH = ROOT / "docs" / "BACKTEST.md"
MIN_RACES = 40   # below this a fit is a coincidence, not a model


def load_races(state: str) -> list[B.Race]:
    from fk.db import Db
    db = Db(load_settings().database_url)
    races = []
    for row in db.resulted_races(state):
        runners = [r for r in (B.runner_from_entry(e, row.get("distance_m")) for e in row["entries"]) if r is not None]
        if len(runners) < 2:
            continue
        B.race_features(runners)
        races.append(B.Race(row["race_id"], row["date"], row["track"], runners))
    return races


def run(races: list[B.Race]) -> tuple[dict, str]:
    with_bsp = [r for r in races if B.bsp_chances(r.runners) is not None and any(x.finish == 1 for x in r.runners)]
    if len(with_bsp) < MIN_RACES:
        raise SystemExit(f"only {len(with_bsp)} resulted races with BSPs stored; {MIN_RACES} needed before a fit means anything. "
                         "Pull more past days (fk backtest pull) first.")
    with_bsp.sort(key=lambda r: (r.date, r.race_id))
    dates = [r.date for r in with_bsp]
    # Out of sample: fit on the first 70% of races by date, score on the last 30%, so a
    # model with more features has to earn them on races it never saw.
    cut = int(len(with_bsp) * 0.7)
    train, test = with_bsp[:cut], with_bsp[cut:]
    rows = []
    for name, feats in B.MODEL_SETS.items():
        beta_tr = B.fit(train, feats)
        ins = B.score([B.predict(beta_tr, r.runners) for r in train], train)
        out = B.score([B.predict(beta_tr, r.runners) for r in test], test)
        rows.append((name, feats, ins, out))
    yard = {"bsp_itself": (B.score(B.bsp_probs(train), train), B.score(B.bsp_probs(test), test)),
            "opening_market": (B.score(B.market_probs(train), train), B.score(B.market_probs(test), test))}
    form_rows = [r for r in rows if B.MARKET_FEATURE not in r[1]]
    best = min(form_rows, key=lambda r: r[3].kl_to_bsp)
    chosen_name, chosen_feats = best[0], best[1]
    final_beta = B.fit(with_bsp, chosen_feats)             # deployed: refitted on every race
    final_score = B.score([B.predict(final_beta, r.runners) for r in with_bsp], with_bsp)
    calib = B.calibration([B.predict(final_beta, r.runners) for r in with_bsp], with_bsp)

    lines = ["# Back-test against Betfair SP", "",
             f"Fitted {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} over {len(with_bsp)} resulted races "
             f"({final_score.runners} runners), {dates[0]} to {dates[-1]}. Out of sample = fitted on the first {len(train)} "
             f"races by date, scored on the last {len(test)}.", "",
             "Each model is a conditional logit fitted to minimise the cross-entropy against the BSP-implied chances. "
             "'KL to BSP' is how far it sits from BSP (0 = BSP itself); 'log loss' is scored on the actual winners (lower "
             "is better); 'top pick won' is the share of races the model's highest-rated runner won.", "",
             "| model | KL to BSP (in / out) | log loss vs winners (in / out) | top pick won (in / out) |", "|---|---|---|---|"]
    for name, (i, o) in yard.items():
        lines.append(f"| {name} | {i.kl_to_bsp:.4f} / {o.kl_to_bsp:.4f} | {i.log_loss:.4f} / {o.log_loss:.4f} | {i.winner_top_rated:.1%} / {o.winner_top_rated:.1%} |")
    for name, feats, i, o in rows:
        mark = " **(deployed)**" if name == chosen_name else ""
        lines.append(f"| {name}{mark} | {i.kl_to_bsp:.4f} / {o.kl_to_bsp:.4f} | {i.log_loss:.4f} / {o.log_loss:.4f} | {i.winner_top_rated:.1%} / {o.winner_top_rated:.1%} |")
    lines += ["", f"Deployed: **{chosen_name}**, the form-only model closest to BSP out of sample, refitted on all {len(with_bsp)} races.", "",
              "## Coefficients of the deployed model", ""]
    lines += [f"- {k}: {v:+.4f}" for k, v in final_beta.items()]
    lines += ["", "Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, "
              "peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the "
              "career peak and the 12-month peak; wfa_rel, wfa_best_rel = points below the best of the latest and the best "
              "WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean "
              f"rating of runs within {B.DISTANCE_BAND_M}m of today's trip; dist_win = the record at the distance as a shrunk "
              "win rate, against the race mean; open_logit = log of the opening-market chance (comparison only, never deployed, "
              "so Value keeps meaning disagreement with the market).",
              "", "## Calibration of the deployed model", "", "| rated chance | runners | mean rated | share that won |", "|---|---|---|---|"]
    for bucket, n, mean, won in calib:
        lines.append(f"| {bucket} | {n} | {mean:.1%} | {won:.1%} |")
    model = {
        "fitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "races": len(with_bsp), "runners": final_score.runners, "from": dates[0], "to": dates[-1],
        "model": chosen_name, "features": chosen_feats, "beta": final_beta,
        "scores": {"deployed_in_sample": vars(final_score),
                   **{f"{name}_out_of_sample": vars(o) for name, _, _, o in rows},
                   **{f"{name}_out_of_sample": vars(o) for name, (_, o) in yard.items()}},
    }
    return model, "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    races = load_races(a.state)
    print(f"{len(races)} resulted races loaded")
    model, report = run(races)
    print(report)
    if a.dry:
        return
    MODEL_PATH.parent.mkdir(exist_ok=True)
    MODEL_PATH.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"wrote {MODEL_PATH} and {REPORT_PATH}")


if __name__ == "__main__":
    main()
