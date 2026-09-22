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
from fk import projection as P

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "config" / "rated_price.json"
REPORT_PATH = ROOT / "docs" / "BACKTEST.md"
MIN_RACES = 40   # below this a fit is a coincidence, not a model


def load_races(state: str) -> tuple[list[B.Race], dict[str, P.ProjRace]]:
    """The logit races and, keyed by race id, the projection inputs for the same races."""
    from fk.db import Db
    db = Db(load_settings().database_url)
    races, proj = [], {}
    for row in db.resulted_races(state):
        runners = [r for r in (B.runner_from_entry(e, row.get("distance_m"), row.get("lws")) for e in row["entries"]) if r is not None]
        if len(runners) < 2:
            continue
        B.race_features(runners)
        B.shape_features(runners, B.positions_from_speedmap(row.get("speedmap")), P.tempo_score(row.get("tempo")))
        race = B.Race(row["race_id"], row["date"], row["track"], runners)
        races.append(race)
        proj[race.race_id] = proj_race(race, row["entries"], row.get("speedmap"), row.get("tempo"))
    return races, proj


def proj_race(race: B.Race, entries: list[dict], speedmap: list[dict] | None, tempo: dict | None) -> P.ProjRace:
    positions = {r["horse_id"]: r.get("predicted_position") for r in (speedmap or []) if r.get("horse_id")}
    active = [e for e in entries if not B.F.entry_scratched(e)]
    inputs = [i for i in (P.inputs_from_entry(e, positions.get(B.F.horse_id(e)), len(active)) for e in active) if i is not None]
    q = B.bsp_chances(race.runners) or []
    bsp = {r.horse_id: qi for r, qi in zip(race.runners, q)}
    winner = next((r.horse_id for r in race.runners if r.finish == 1), None)
    return P.ProjRace(race.race_id, inputs, P.tempo_score(tempo), bsp, winner)


def proj_probs(proj: dict[str, P.ProjRace], races: list[B.Race], params: P.Params) -> list[list[float]]:
    """The projection model's chances in the logit races' runner order, so B.score applies."""
    out = []
    for race in races:
        probs = P.race_probs(proj[race.race_id], params)
        have = [probs.get(r.horse_id) for r in race.runners]
        floor = 1e-6
        vals = [v if v is not None else floor for v in have]
        s = sum(vals)
        out.append([v / s for v in vals])
    return out


def run(races: list[B.Race], proj: dict[str, P.ProjRace] | None = None) -> tuple[dict, str]:
    proj = proj or {}
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
    # The projection-and-simulation model: parameters tuned on the training races, scored out of sample.
    proj_ok = all(r.race_id in proj for r in with_bsp)
    proj_rows = []
    if proj_ok:
        params_tr = P.fit_params([proj[r.race_id] for r in train])
        ins = B.score(proj_probs(proj, train, params_tr), train)
        out = B.score(proj_probs(proj, test, params_tr), test)
        proj_rows.append(("projection_sim", None, ins, out))
    form_rows = [r for r in rows if not (set(r[1]) & B.NON_DEPLOYABLE)] + proj_rows
    best = min(form_rows, key=lambda r: r[3].kl_to_bsp)
    chosen_name, chosen_feats = best[0], best[1]
    if chosen_name == "projection_sim":
        final_params = P.fit_params([proj[r.race_id] for r in with_bsp])
        final_probs = proj_probs(proj, with_bsp, final_params)
        final_beta = None
    else:
        final_beta = B.fit(with_bsp, chosen_feats)             # deployed: refitted on every race
        final_probs = [B.predict(final_beta, r.runners) for r in with_bsp]
        final_params = None
    final_score = B.score(final_probs, with_bsp)
    calib = B.calibration(final_probs, with_bsp)
    # The projection (the founder's method) is shown on the page whether or not it prices,
    # so its parameters are always fitted on every race and saved.
    projection_params = None
    if proj_ok:
        projection_params = vars(final_params) if final_params is not None else vars(P.fit_params([proj[r.race_id] for r in with_bsp]))

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
    for name, feats, i, o in rows + proj_rows:
        mark = " **(deployed)**" if name == chosen_name else ""
        lines.append(f"| {name}{mark} | {i.kl_to_bsp:.4f} / {o.kl_to_bsp:.4f} | {i.log_loss:.4f} / {o.log_loss:.4f} | {i.winner_top_rated:.1%} / {o.winner_top_rated:.1%} |")
    lines += ["", f"Deployed: **{chosen_name}**, the form-only model closest to BSP out of sample, refitted on all {len(with_bsp)} races.", ""]
    if final_beta is not None:
        lines += ["## Coefficients of the deployed model", ""] + [f"- {k}: {v:+.4f}" for k, v in final_beta.items()]
    else:
        lines += ["## Parameters of the deployed projection model", ""] + [f"- {k}: {v}" for k, v in vars(final_params).items()]
        lines += ["", "projection_sim = the founder's method: a projected figure per runner (recency-weighted recent ratings, anchored at "
                  "the last run when rising; scope for lightly raced horses and the trend; tempo x settling position; last-600m vs "
                  "class weighted up in a slow race) and the race run with each figure drawn around its projection; every weight "
                  "above was tuned against BSP."]
    if proj_rows and final_params is None:
        lines += ["", "projection_sim parameters on the training races: " + ", ".join(f"{k} {v}" for k, v in vars(params_tr).items())]
    if proj_ok:
        total = sum(len(proj[r.race_id].inputs) for r in with_bsp)
        unrated = sum(1 for r in with_bsp for i in proj[r.race_id].inputs if not i.ratings)
        lines += ["", f"Runners with no rated run (projected at the field mean less the unrated gap): {unrated} of {total}."]
    lines += ["", "Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, "
              "peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the "
              "career peak and the 12-month peak; speed_rel, speed_best_rel = points below the race\'s best of Form King\'s speed "
              f"figure (100 = class par) read over the last {B.RECENT_RUNS} races newest-weighted, and of the best one; "
              "finish_speed_rel = the same over finishing speed (last 600 as a share of the run to the 600); last600_rel, "
              "to600_rel = the last 600m and the run to it against the class standard, in lengths; "
              "settle_share, pos800_share = where the horse settles and where it sits with 800m to run, as a share of its "
              "own field (0 = on the lead, 1 = last) read over its recent races and centred on today's field; pos_gain, "
              "late_gain = positions made up from settling and from the 400m to the post, on the same share; "
              "style_x_tempo = that settling share against the expected tempo, so a backmarker in a slow-run race reads "
              "negative; map_vs_habit = how far today's speedmap asks the horse to race from where it usually does; "
              "wfa_rel, wfa_best_rel = points below the best of the latest and the best "
              "WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean "
              f"rating of runs within {B.DISTANCE_BAND_M}m of today's trip; dist_win = the record at the distance as a shrunk "
              "win rate, against the race mean; last_vs_lws, best_vs_lws = the latest and the best rated run against the race's "
              "Likely Winning Standard (class); trend_slope = rating points per run over the last six runs; starts_log = log of "
              "career starts against the race mean (scope); open_logit = log of the opening-market chance (comparison only, never "
              "deployed, so Value keeps meaning disagreement with the market).",
              "", "## Calibration of the deployed model", "", "| rated chance | runners | mean rated | share that won |", "|---|---|---|---|"]
    for bucket, n, mean, won in calib:
        lines.append(f"| {bucket} | {n} | {mean:.1%} | {won:.1%} |")
    # The plans, replayed over every stored race out of sample (5 date blocks, each priced
    # by a fit on the other four), at the opening price and again at BSP.
    replay_feats = chosen_feats if chosen_feats else B.MODEL_SETS["all_form_plus_class"]
    replay = B.plan_replay(with_bsp, replay_feats)
    lines += ["", f"## The plans, replayed over {replay['races']} races the fit never saw", "",
              "Five blocks by date, each priced by a model fitted on the other four; bets at the OPENING price and settled at "
              "Betfair SP (the live book's rule), then the same bets at BSP itself. A plan that only pays at the opening price "
              "is living on the market firming after it, which a real bet placed late does not get.", "",
              "| plan | bets | winners | staked | returned | profit | return | at BSP: profit | return |", "|---|---|---|---|---|---|---|---|---|"]
    from fk import paper as PB
    for plan in PB.PLANS:
        a = replay["at_open"].get(plan); b = replay["at_bsp"].get(plan)
        if not a:
            continue
        b_profit = f"{b.profit:+.1f}" if b else "n/a"
        b_roi = f"{b.roi:+.1%}" if b and b.roi is not None else "n/a"
        lines.append(f"| {plan} | {a.bets} | {a.winners} | {a.staked:.1f} | {a.returned:.1f} | {a.profit:+.1f} | {a.roi:+.1%} | {b_profit} | {b_roi} |")
    model = {
        "fitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "races": len(with_bsp), "runners": final_score.runners, "from": dates[0], "to": dates[-1],
        "model": chosen_name, "features": chosen_feats, "beta": final_beta,
        "params": vars(final_params) if final_params is not None else None,
        "projection_params": projection_params,
        "plan_replay": {side: {plan: vars(summ) for plan, summ in replay[side].items()} for side in ("at_open", "at_bsp")},
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
    races, proj = load_races(a.state)
    print(f"{len(races)} resulted races loaded")
    model, report = run(races, proj)
    print(report)
    if a.dry:
        return
    MODEL_PATH.parent.mkdir(exist_ok=True)
    MODEL_PATH.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"wrote {MODEL_PATH} and {REPORT_PATH}")


if __name__ == "__main__":
    main()
