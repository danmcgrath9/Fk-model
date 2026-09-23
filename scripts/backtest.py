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
# The sets still fitted to the winners as well as to BSP, as a standing check that the
# winners target keeps losing; if it ever stops losing, widen this.
WINNER_CHECK_SETS = {"all_form_plus_open_market", "market_kitchen_sink"}


def load_races(state: str, history_dir: Path | None = None) -> tuple[list[B.Race], dict[str, P.ProjRace]]:
    """The logit races and, keyed by race id, the projection inputs for the same races:
    every resulted race in the database, then every one in the history files (fk/history.py)
    that the database does not hold."""
    from fk import history as H
    from fk.db import Db
    db = Db(load_settings().database_url)
    rows = db.resulted_races(state)
    in_db = {row["race_id"] for row in rows}
    races, proj = races_from_rows(rows)
    file_races, file_proj = races_from_rows(H.resulted_races(history_dir, state, skip=in_db))
    print(f"{len(races)} resulted races from the database, {len(file_races)} more from the history files")
    races += file_races
    proj.update(file_proj)
    # the out-of-sample split is by date, so the two sources are put in one date order
    races.sort(key=lambda r: (r.date, r.track, r.race_id))
    return races, proj


def races_from_rows(rows) -> tuple[list[B.Race], dict[str, P.ProjRace]]:
    """Rows shaped like Db.resulted_races (a history file's lines are the same shape)."""
    races, proj = [], {}
    for row in rows:
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
    # Every feature set is fitted BOTH ways: to the market's closing price and to the actual
    # winner. Fitting to BSP is low variance but its best attainable model is the market
    # itself, which by construction has no edge; fitting to winners is noisier and leaves
    # room to disagree with the market and be right.
    rows = []
    for name, feats in B.MODEL_SETS.items():
        # Fitting to the winners has lost to fitting to BSP on every set in every run so far,
        # by overfitting: one winner per race is too little signal. It stays on two sets as a
        # standing check, and off the rest, which halves a run that would otherwise outgrow
        # its time limit as the history grows.
        targets = [(B.bsp_chances, "")]
        if name in WINNER_CHECK_SETS:
            targets.append((B.winner_chances, " @winners"))
        for target, suffix in targets:
            # The ridge is chosen by cross-validation inside the training races, so the test
            # block stays untouched by every choice the model makes about itself.
            beta_tr, ridge = B.fit_cv(train, feats, target=target)
            ins = B.score([B.predict(beta_tr, r.runners) for r in train], train)
            out = B.score([B.predict(beta_tr, r.runners) for r in test], test)
            rows.append((name + suffix, feats, ins, out, target, ridge))
    yard = {"bsp_itself": (B.score(B.bsp_probs(train), train), B.score(B.bsp_probs(test), test)),
            "opening_market": (B.score(B.market_probs(train), train), B.score(B.market_probs(test), test))}
    # The projection-and-simulation model: parameters tuned on the training races, scored out of sample.
    proj_ok = all(r.race_id in proj for r in with_bsp)
    proj_rows = []
    if proj_ok:
        params_tr = P.fit_params([proj[r.race_id] for r in train])
        ins = B.score(proj_probs(proj, train, params_tr), train)
        out = B.score(proj_probs(proj, test, params_tr), test)
        proj_rows.append(("projection_sim", None, ins, out, None, None))
    # Deployed on DISTANCE FROM BSP, with the bar set at the morning market rather than at
    # zero. BSP is the sharpest price anyone gets, so it stands for the truth; the morning
    # market is the price we actually bet into. A model closer to BSP than the morning market
    # is has beaten the market we are betting against, which is the whole job. Being AT BSP
    # is neither possible nor the point.
    market_bar = yard["opening_market"][1].kl_to_bsp
    form_rows = [r for r in rows if not (set(r[1]) & B.NON_DEPLOYABLE)] + proj_rows
    best = min(form_rows, key=lambda r: r[3].kl_to_bsp)
    chosen_name, chosen_feats = best[0], best[1]
    chosen_target = best[4] if len(best) > 4 else B.bsp_chances
    chosen_ridge = best[5] if len(best) > 5 and best[5] is not None else 1e-8
    if chosen_name == "projection_sim":
        final_params = P.fit_params([proj[r.race_id] for r in with_bsp])
        final_probs = proj_probs(proj, with_bsp, final_params)
        final_beta = None
    else:
        # Deployed: refitted on every race at the ridge its own cross-validation chose.
        final_beta = B.fit(with_bsp, chosen_feats, ridge=chosen_ridge, target=chosen_target or B.bsp_chances)
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
             "Each model is a conditional logit fitted to minimise the cross-entropy against a target: the BSP-implied "
             "chances, or ('@winners') the actual result. 'KL to BSP' is how far it sits from Betfair SP, the sharpest "
             "price anyone gets and so the stand-in for the truth. **The bar is not zero, it is the morning market**, "
             f"which sits at {market_bar:.4f} out of sample: that is the price we bet into, so a model closer to BSP than "
             "it is has beaten the market it is betting against. 'log loss' is scored on the actual winners and 'top pick "
             "won' is the share of races the model's highest-rated runner won.", "",
             "| model | KL to BSP (in / out) | vs the morning market | ridge | log loss vs winners (in / out) | top pick won (in / out) |",
             "|---|---|---|---|---|---|"]
    for name, (i, o) in yard.items():
        lines.append(f"| {name} | {i.kl_to_bsp:.4f} / {o.kl_to_bsp:.4f} | {'the bar' if name == 'opening_market' else '-'} | - | "
                     f"{i.log_loss:.4f} / {o.log_loss:.4f} | {i.winner_top_rated:.1%} / {o.winner_top_rated:.1%} |")
    for name, feats, i, o, _t, ridge in rows + proj_rows:
        mark = " **(deployed)**" if name == chosen_name else ""
        beat = "BEATS IT" if o.kl_to_bsp < market_bar else f"{o.kl_to_bsp - market_bar:+.4f}"
        rg = f"{ridge:g}" if ridge is not None else "-"
        lines.append(f"| {name}{mark} | {i.kl_to_bsp:.4f} / {o.kl_to_bsp:.4f} | {beat} | {rg} | {i.log_loss:.4f} / {o.log_loss:.4f} | {i.winner_top_rated:.1%} / {o.winner_top_rated:.1%} |")
    verdict = ("BEATS the morning market" if best[3].kl_to_bsp < market_bar
               else f"does NOT beat the morning market, {best[3].kl_to_bsp - market_bar:+.4f} behind it")
    lines += ["", f"Deployed: **{chosen_name}**, the model closest to BSP out of sample, refitted on all {len(with_bsp)} races. "
              f"It {verdict}. The morning price is a legitimate input: we bet into it, so using it and landing closer to BSP "
              "than it does is exactly what beating the market means. EXP is the one thing barred, because Form King derives "
              "it from the market without saying which one and it scores like a figure that already knows the close. "
              "'@winners' marks a model fitted to the actual result rather than to the closing price.", ""]
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
              "open_logit = the log of the opening-market chance and market_prob the chance itself, carried together so the fit "
              "can bend the market\'s own curve (short prices are historically underbet and long ones overbet, and log-chance "
              "alone cannot correct that); market_x_neural = the market read against Neural. The move from the open to the "
              "price NOW is deliberately absent: a race pulled after it ran carries its FINAL price, so it would be reading "
              "the answer. career peak and the 12-month peak; speed_rel, speed_best_rel = points below the race\'s best of Form King\'s speed "
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
    replay = B.plan_replay(with_bsp, replay_feats, target=chosen_target or B.bsp_chances, ridge=chosen_ridge)
    lines += ["", f"## The plans, replayed over {replay['races']} races the fit never saw", "",
              "Five blocks by date, each priced by a model fitted on the other four. Every bet is chosen against the MORNING "
              "market and struck at the morning price. The two profit columns are the SAME bets on two settlement bases: paid "
              "at Betfair SP, which is what betting into the jump gets you, and paid at the price it was struck at, which is "
              "what taking the morning price gets you. They differ by however far the selections moved.", "",
              "| plan | bets | winners | staked | at BSP: profit | return | at the struck price: profit | return |",
              "|---|---|---|---|---|---|---|---|"]
    from fk import paper as PB
    for plan in PB.PLANS:
        a = replay["at_open"].get(plan); b = replay["at_struck"].get(plan)
        if not a:
            continue
        b_profit = f"{b.profit:+.1f}" if b else "n/a"
        b_roi = f"{b.roi:+.1%}" if b and b.roi is not None else "n/a"
        lines.append(f"| {plan} | {a.bets} | {a.winners} | {a.staked:.1f} | {a.profit:+.1f} | {a.roi:+.1%} | {b_profit} | {b_roi} |")
    # Which rule should pick a value bet, and at what edge. Chosen on the older racing only
    # and then shown on the newer racing it never saw, so a rule that only fits the past
    # shows up as one that stops working.
    sweeps = {}
    for label, under in (("value_flags", None), ("value_under_8", 8.0)):
        sweep_rows, best = B.value_sweep(with_bsp, replay_feats, target=chosen_target or B.bsp_chances, ridge=chosen_ridge, under=under)
        sweeps[label] = {"chosen": list(best) if best else None, "rows": [vars(r) for r in sweep_rows]}
        lines += ["", f"## Choosing the value rule: {label}", "",
                  "gap = our chance beats the market's by more than the threshold in percentage points (the live rule is gap "
                  "0.05). ev = our chance times the morning price is more than 1 plus the threshold. Each rule is picked on the "
                  f"OLDER {B.SWEEP_CHOOSE_BLOCKS} fifths of the racing by its return at Betfair SP (at least {B.SWEEP_MIN_BETS} "
                  "bets), then shown on the NEWER two fifths it never saw. Returns are one unit a bet, before commission.", "",
                  "| rule | threshold | older: bets | at BSP | at morning price | newer: bets | at BSP | at morning price |",
                  "|---|---|---|---|---|---|---|---|"]
        by = {(r.rule, r.threshold, r.half): r for r in sweep_rows}
        for rule, ts in B.VALUE_RULES.items():
            for t in ts:
                c, f = by[(rule, t, "choose")], by[(rule, t, "confirm")]
                mark = " **(chosen)**" if best == (rule, t) else (" (live)" if (rule, t) == ("gap", 0.05) else "")
                lines.append(f"| {rule}{mark} | {t:.2f} | {c.bets} | {c.roi_bsp:+.1%} | {c.roi_struck:+.1%} | "
                             f"{f.bets} | {f.roi_bsp:+.1%} | {f.roi_struck:+.1%} |")
    model = {
        "fitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "races": len(with_bsp), "runners": final_score.runners, "from": dates[0], "to": dates[-1],
        "model": chosen_name, "features": chosen_feats, "beta": final_beta,
        "fitted_to": "winners" if chosen_target is B.winner_chances else "bsp",
        "ridge": chosen_ridge,
        "params": vars(final_params) if final_params is not None else None,
        "projection_params": projection_params,
        "value_sweep": sweeps,
        "plan_replay": {side: {plan: vars(summ) for plan, summ in replay[side].items()} for side in ("at_open", "at_struck")},
        "scores": {"deployed_in_sample": vars(final_score),
                   **{f"{name}_out_of_sample": vars(o) for name, _, _, o, _t, _r in rows},
                   **{f"{name}_out_of_sample": vars(o) for name, (_, o) in yard.items()}},
    }
    return model, "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--history", default=str(ROOT / "history"), help="directory of history day files (fk/history.py)")
    a = ap.parse_args()
    races, proj = load_races(a.state, Path(a.history))
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
