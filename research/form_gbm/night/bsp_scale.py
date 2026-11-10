"""What liquidity at BSP would buy (11 Nov 2026, founder: "Yeah but more liquidity at bsp").
For the three BSP survivors (bsp_scan2.py) and the open book: the edge with its uncertainty, the stake a bet needs to
match the open book's median month ($10,350 at $50 a unit, risk_months.py), and what a month looks like at that stake.
    python3.13 bsp_scale.py   (night folder)"""
import numpy as np
src = open("bsp_scan.py").read().split('print("1. WHEN WE DISAGREE')[0]; exec(src)
mv = op / bs; r = bs / ours; MONTHS = 16.3; TARGET = 10350.0
rng = np.random.default_rng(0)
RULES = [("back $3-$5, firmed 1.5x+ from the open", "BACK", (bs >= 3) & (bs < 5) & (mv >= 1.5)),
         ("lay $20-$40, BSP 0.6x ours or less", "LAY", (bs >= 20) & (bs < 40) & (r < 0.6)),
         ("back $20-$40, firmed 1.25x+, we 10%+ shorter", "BACK", (bs >= 20) & (bs <= 40) & (mv >= 1.25) & (r >= 1.1))]
for name, side, m in RULES:
    m = np.nan_to_num(m.astype(float), nan=0) > 0; m &= ok; u = (ul if side == "LAY" else ub)[m]; q_ = qb[m]; b_ = bs[m]
    n = int(m.sum()); per_m = n / MONTHS; w, e = int(won[m].sum()), float(q_.sum()); sd_w = np.sqrt(np.sum(q_ * (1 - q_)))
    # the edge at A/E 2 SD either side: scale BSP's chances by that A/E and recompute the expected return a bet
    def ret(ae):
        p = np.clip(q_ * ae, 0, 1)
        return float(np.mean(p * (b_ - 1) * 0.92 - (1 - p))) if side == "BACK" else float(np.mean((1 - p) * 0.92 - p * (b_ - 1)))
    ae = w / e; lo, hi = (w - 2 * sd_w) / e, (w + 2 * sd_w) / e
    be = next(a for a in np.arange(0.5, 1.6, 0.001) if (ret(a) > 0) == (side == "BACK"))  # break-even A/E
    mean_u = u.mean(); stake = TARGET / (per_m * mean_u)
    # a month: resample whole bets
    sims = np.array([rng.choice(u, size=rng.poisson(per_m)).sum() for _ in range(20000)]) * stake
    liab = float(np.median(b_ - 1)) * stake if side == "LAY" else stake
    print(f"{name}: {n} bets, {per_m:.0f} a month, median BSP ${np.median(b_):.0f}\n"
          f"   winners {w} v {e:.1f} by BSP, A/E {ae:.2f} (2 SD: {lo:.2f} to {hi:.2f}); it pays only if A/E is {'above' if side == 'BACK' else 'below'} {be:.2f}\n"
          f"   return a bet {100*mean_u:+.1f}% as it happened; at the 2-SD ends {100*ret(lo):+.1f}% to {100*ret(hi):+.1f}%\n"
          f"   to make $10,350 a month: ${stake:,.0f} a bet" + (f" (liability about ${liab:,.0f} a lay)" if side == "LAY" else "")
          + f"; at that stake a month is median ${np.median(sims):+,.0f}, one month in five under ${np.percentile(sims, 20):+,.0f}, {100*np.mean(sims < 0):.0f}% of months lose, worst 5% ${np.percentile(sims, 5):+,.0f}")
