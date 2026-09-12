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
        runners = [r for r in (B.runner_from_entry(e) for e in row["entries"]) if r is not None]
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
    dates = sorted(r.date for r in with_bsp)
    models = {
        "neural_only": ["neural_rel"],
        "form": B.FORM_FEATURES,
        "form_plus_open_market": B.FORM_FEATURES + [B.MARKET_FEATURE],
    }
    fitted = {name: B.fit(with_bsp, feats) for name, feats in models.items()}
    scored = {name: B.score([B.predict(beta, r.runners) for r in with_bsp], with_bsp) for name, beta in fitted.items()}
    scored["opening_market"] = B.score(B.market_probs(with_bsp), with_bsp)
    scored["bsp_itself"] = B.score(B.bsp_probs(with_bsp), with_bsp)
    calib = B.calibration([B.predict(fitted["form"], r.runners) for r in with_bsp], with_bsp)

    lines = [f"# Back-test against Betfair SP", "",
             f"Fitted {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} over {len(with_bsp)} resulted races "
             f"({scored['form'].runners} runners), {dates[0]} to {dates[-1]}.", "",
             "Each model is a conditional logit fitted to minimise the cross-entropy against the BSP-implied chances; "
             "'KL to BSP' is how far it sits from BSP (0 = BSP), 'log loss' is scored on the actual winners (lower is better), "
             "'top pick won' is the share of races the model's highest-rated runner won.", "",
             "| model | KL to BSP | log loss vs winners | top pick won |", "|---|---|---|---|"]
    for name in ("bsp_itself", "opening_market", "neural_only", "form", "form_plus_open_market"):
        s = scored[name]
        lines.append(f"| {name} | {s.kl_to_bsp:.4f} | {s.log_loss:.4f} | {s.winner_top_rated:.1%} |")
    lines += ["", "## Coefficients", ""]
    for name, beta in fitted.items():
        lines.append(f"- {name}: " + ", ".join(f"{k} {v:+.4f}" for k, v in beta.items()))
    lines += ["", "Features: neural_rel = Neural points / the race's top (top = 1); last_rel, peak_rel, peak12_rel = points below "
              "the race's best of the latest rated run, the career peak and the 12-month peak; open_logit = log of the "
              "opening-market chance. The report prices with the 'form' model, so Value still measures disagreement with the market.",
              "", "## Calibration of the form model", "", "| rated chance | runners | mean rated | share that won |", "|---|---|---|---|"]
    for bucket, n, mean, won in calib:
        lines.append(f"| {bucket} | {n} | {mean:.1%} | {won:.1%} |")
    model = {
        "fitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "races": len(with_bsp), "runners": scored["form"].runners, "from": dates[0], "to": dates[-1],
        "features": B.FORM_FEATURES, "beta": fitted["form"],
        "scores": {name: vars(s) for name, s in scored.items()},
        "all_models": fitted,
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
