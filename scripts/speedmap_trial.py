"""What does the speedmap add to the form price? Read-only, no Form King calls.

    python scripts/speedmap_trial.py [--state VIC] [--history history]

The deployed form price (config/form_price.json: its features, ridge and target) is fitted on
the older 70% of racing with the speedmap inputs taken out, as deployed, and with the map across
the track added (fk.backtest.MAP). Each is scored on the newer 30% it never saw: KL to Betfair SP
(lower is closer), log loss against the winners and how often its top pick won. Scored over every
race, over the races that carry a speedmap, and over sprints to 1300m with one.

Speedmap inputs: early_pos, early_x_tempo (where Form King maps it to settle, and that against
the expected tempo), style_x_tempo and map_vs_habit (its usual settling spot against today's
tempo and map). Past positions (settle_share, pos800_share, pos_gain, late_gain) are the horse's
own runs, not the map, and are taken out separately.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fk import backtest as B  # noqa: E402
from fit_form_only import TARGETS, TRAIN_SHARE, fit_np, split_by_date  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SPEEDMAP = ["early_pos", "early_x_tempo", "style_x_tempo", "map_vs_habit"]


def has_map(race) -> bool:
    return any(abs(r.x.get("early_pos", 0.0)) > 1e-12 for r in race.runners)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--history", default=str(ROOT / "history"))
    a = ap.parse_args()
    cfg = json.loads((ROOT / "config" / "form_price.json").read_text())
    target = TARGETS[cfg.get("fitted_to", "bsp")]
    base, ridge = list(cfg["features"]), float(cfg["ridge"])
    from backtest import load_races
    races, _ = load_races(a.state, Path(a.history))
    races = [r for r in races if B.bsp_chances(r.runners) and B.winner_chances(r.runners)]
    train, test = split_by_date(races, TRAIN_SHARE)
    mapped = [r for r in test if has_map(r)]
    sprint = [r for r in mapped if (getattr(r, "distance_m", None) or 9999) <= 1300]
    print(f"Deployed form price: {cfg['model']}, ridge {ridge:g}, fitted to {cfg.get('fitted_to')}. "
          f"Fitted on {len(train)} races, scored on the newer {len(test)} ({test[0].date} to {test[-1].date}).")
    print(f"Speedmap on {len(mapped)} of the {len(test)} test races ({len(mapped) / len(test):.0%}), "
          f"{sum(has_map(r) for r in train)} of the {len(train)} training races.\n")
    sets = [
        ("no speedmap, no past positions", [f for f in base if f not in SPEEDMAP + B.POSITION]),
        ("no speedmap", [f for f in base if f not in SPEEDMAP]),
        ("as deployed (with the speedmap)", base),
        ("deployed + path, cover, drawn wide", base + [f for f in B.MAP if f not in base]),
    ]
    mkt = B.market_probs
    print("KL to BSP: lower is closer. Log loss: lower is more right about the winner.\n")
    print("| price | every race: KL | log loss | top pick | with a map: KL | log loss | sprints with a map: KL | log loss |")
    print("|---|---|---|---|---|---|---|---|")
    for name, feats in sets:
        beta = fit_np(train, feats, ridge, target=target)
        probs = lambda rs: [B.predict(beta, r.runners) for r in rs]  # noqa: E731
        s_all, s_map = B.score(probs(test), test), B.score(probs(mapped), mapped)
        s_spr = B.score(probs(sprint), sprint) if len(sprint) >= 40 else None
        spr = f"{s_spr.kl_to_bsp:.4f} | {s_spr.log_loss:.4f}" if s_spr else "too few | "
        print(f"| {name} | {s_all.kl_to_bsp:.4f} | {s_all.log_loss:.4f} | {s_all.winner_top_rated:.1%} | "
              f"{s_map.kl_to_bsp:.4f} | {s_map.log_loss:.4f} | {spr} |", flush=True)
    m_all, m_map = B.score(mkt(test), test), B.score(mkt(mapped), mapped)
    m_spr = B.score(mkt(sprint), sprint) if len(sprint) >= 40 else None
    spr = f"{m_spr.kl_to_bsp:.4f} | {m_spr.log_loss:.4f}" if m_spr else "too few | "
    print(f"| opening market | {m_all.kl_to_bsp:.4f} | {m_all.log_loss:.4f} | {m_all.winner_top_rated:.1%} | "
          f"{m_map.kl_to_bsp:.4f} | {m_map.log_loss:.4f} | {spr} |")
    print(f"\n{len(sprint)} test sprints to 1300m carry a map.")


if __name__ == "__main__":
    main()
