"""Does the FORM-ONLY price make money against the opening market? Out of sample, read-only.

    python scripts/form_value_trial.py [--state VIC] [--history history]

The form-only model (config/form_price.json: its feature set and ridge) is refitted on the
older 70% of racing and never sees the newer 30%. On those newer races every runner whose
form price is shorter than Form King's average opening price by the value threshold is
backed, one unit flat, and settled three ways:

  at the opening price   what the bet returns IF that price could be taken. It cannot: the
                         opening average is a blend of bookmakers' first prices, and the
                         deployed model's back-test profit against it vanished at real prices.
  at Betfair SP          a price anyone can take, before commission.
  at BSP less 8%         Betfair's commission on net winnings (standard Australian rate is
                         5 to 10% depending on the market and the account), so this is closer
                         to what a real account keeps.

Every figure carries its margin of luck (1 standard error), and several thresholds are shown,
so the best-looking row is partly the best-looking by chance.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fk import backtest as B  # noqa: E402
from fit_form_only import TARGETS, fit_np, split_by_date, TRAIN_SHARE  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = [0.0, 0.1, 0.2, 0.3, 0.5]
COMMISSION = 0.08
MAX_RATED = 50.0


def bets_for(races, beta, threshold: float, cap: bool, top_only: bool = False) -> list[tuple[float, bool, float | None]]:
    """(open price, won, bsp) for each bet the rule takes."""
    out = []
    for race in races:
        p = B.predict(beta, race.runners)
        best = max(range(len(p)), key=lambda i: p[i])
        for i, (r, pi) in enumerate(zip(race.runners, p)):
            price = r.raw.get("open")
            if not price or price <= 1 or pi <= 0:
                continue
            if cap and 1.0 / pi >= MAX_RATED:
                continue
            if top_only and i != best:
                continue
            if not top_only and pi * price - 1.0 <= threshold:
                continue
            out.append((price, r.finish == 1, r.bsp or r.sp))
    return out


def summary(bets) -> str:
    n = len(bets)
    if not n:
        return "| 0 | | | | | |"
    wins = sum(w for _, w, _ in bets)
    at_open = B._roi_se([p if w else 0.0 for p, w, _ in bets])
    at_bsp = B._roi_se([(b if b and b > 1 else 1.0) if w else 0.0 for _, w, b in bets])
    net = B._roi_se([(1 + ((b if b and b > 1 else 1.0) - 1) * (1 - COMMISSION)) if w else 0.0 for _, w, b in bets])
    f = lambda m: f"{m[0]:+.1%} ± {m[1]:.1%}"  # noqa: E731
    return f"| {n} | {wins} ({wins / n:.0%}) | {f(at_open)} | {f(at_bsp)} | {f(net)} |"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--history", default=str(ROOT / "history"))
    a = ap.parse_args()
    cfg = json.loads((ROOT / "config" / "form_price.json").read_text())
    from backtest import load_races
    races, _ = load_races(a.state, Path(a.history))
    races = [r for r in races if B.bsp_chances(r.runners)]
    train, test = split_by_date(races, TRAIN_SHARE)
    beta = fit_np(train, cfg["features"], cfg["ridge"], target=TARGETS[cfg.get("fitted_to", "bsp")])
    print(f"Form-only model ({cfg['model']} fitted to {cfg.get('fitted_to', 'bsp')}, ridge {cfg['ridge']:g}) fitted on {len(train)} races to {train[-1].date}; "
          f"bets on the {len(test)} newer races ({test[0].date} to {test[-1].date}) it never saw. One unit flat per bet.\n")
    print("Value = form chance x opening price - 1. Profit per unit staked, ± one standard error (the margin of luck).\n")
    print("| rule | bets | winners | at the opening price (cannot be taken) | at Betfair SP | at BSP less 8% commission |")
    print("|---|---|---|---|---|---|")
    for t in THRESHOLDS:
        for cap in (False, True):
            label = f"value over {t:.0%}" + (", rated under $50" if cap else "")
            print(f"| {label} " + summary(bets_for(test, beta, t, cap)))
    print(f"| every race: back the form top pick " + summary(bets_for(test, beta, 0.0, False, top_only=True)))

    try:
        from _common import load_settings
        from fk.db import Db
        pre = Db(load_settings().database_url).races_pulled_before_the_jump(a.state)
        live = [r for r in test if r.race_id in pre]
        print(f"\nOnly the {len(live)} newer races the live pipeline pulled BEFORE the jump (no back-filled data at all):\n")
        print("| rule | bets | winners | at the opening price | at Betfair SP | at BSP less 8% |")
        print("|---|---|---|---|---|---|")
        for t in (0.1, 0.2):
            print(f"| value over {t:.0%}, rated under $50 " + summary(bets_for(live, beta, t, True)))
    except Exception as ex:  # noqa: BLE001
        print(f"\npulled-before-the-jump split skipped: {type(ex).__name__}: {ex}")


if __name__ == "__main__":
    main()
