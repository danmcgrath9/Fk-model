# AFL props, step 1: goals, marks, tackles

Fitted 2013-2023, every choice made on 2024, 2025 and 2026 scored once. Established players (5+ games on record), named subs excluded.

## Marks

Spread on 2024: variance = mean + 0.066 x mean squared.

| season | player-games | projection miss | last-10 average miss |
|---|---|---|---|
| 2025 | 9,047 | 1.78 | 1.83 |
| 2026 | 9,474 | 1.78 | 1.84 |

Stand-in line: last-10 average -0.10, rounded to the .5 below (tuned on 2024). **Proxy, not market lines.**

| season | blind over wins | bet when chance over | bets | hit rate | ROI at 1.87 | 90% interval |
|---|---|---|---|---|---|---|
| 2025 | 49.4% | 56% | 5,667 | 63.4% | +18.5% | +16.8% to +20.2% |
| 2025 | 49.4% | 60% | 3,749 | 65.8% | +23.1% | +21.0% to +25.1% |
| 2026 | 49.5% | 56% | 6,056 | 63.0% | +17.8% | +15.1% to +20.7% |
| 2026 | 49.5% | 60% | 4,105 | 65.3% | +22.1% | +19.3% to +24.9% |

Leans on: M_ewm 45%, M_l20 16%, M_season 2%, venue_rel 2%, M_opp_conc_l8 2%, M_opp_rel 2%

## Tackles

Spread on 2024: variance = mean + 0.090 x mean squared.

| season | player-games | projection miss | last-10 average miss |
|---|---|---|---|
| 2025 | 9,047 | 1.44 | 1.48 |
| 2026 | 9,474 | 1.40 | 1.43 |

Stand-in line: last-10 average -0.20, rounded to the .5 below (tuned on 2024). **Proxy, not market lines.**

| season | blind over wins | bet when chance over | bets | hit rate | ROI at 1.87 | 90% interval |
|---|---|---|---|---|---|---|
| 2025 | 52.7% | 56% | 6,197 | 64.0% | +19.8% | +17.7% to +22.0% |
| 2025 | 52.7% | 60% | 4,282 | 66.8% | +24.9% | +22.6% to +27.2% |
| 2026 | 50.8% | 56% | 6,373 | 62.5% | +17.0% | +15.1% to +18.9% |
| 2026 | 50.8% | 60% | 4,418 | 64.8% | +21.1% | +18.5% to +23.7% |

Leans on: T_ewm 45%, T_rate20 26%, T_l20 8%, T_season 1%, CL_pg 1%, T_opp_rel 1%

## Goals

Spread on 2024: variance = mean + 0.080 x mean squared.

| season | player-games | projection miss | last-10 average miss |
|---|---|---|---|
| 2025 | 9,047 | 0.53 | 0.52 |
| 2026 | 9,474 | 0.53 | 0.53 |

Chances of kicking 1+, 2+, 3+ goals: our model against a Poisson around the last-10 average. Log loss, lower is better; calibration = average predicted against what happened.

| season | goals | model log loss | baseline log loss | model: predicted / actual | baseline: predicted / actual |
|---|---|---|---|---|---|
| 2025 | 1+ | 0.4920 | 0.5290 | 34.9% / 33.7% | 33.7% / 33.7% |
| 2025 | 2+ | 0.2755 | 0.2973 | 12.7% / 12.9% | 13.2% / 12.9% |
| 2025 | 3+ | 0.1448 | 0.1555 | 4.8% / 5.2% | 5.2% / 5.2% |
| 2026 | 1+ | 0.4876 | 0.5206 | 35.3% / 34.2% | 33.9% / 34.2% |
| 2026 | 2+ | 0.2902 | 0.3136 | 13.1% / 14.0% | 13.7% / 14.0% |
| 2026 | 3+ | 0.1529 | 0.1619 | 5.0% / 5.5% | 5.5% / 5.5% |

Anytime goal: calibration, both seasons

| our chance | player-games | average predicted | actually kicked one |
|---|---|---|---|
| (0.0, 0.1] | 3,491 | 5.0% | 3.9% |
| (0.1, 0.2] | 2,369 | 14.8% | 14.0% |
| (0.2, 0.3] | 3,149 | 25.6% | 21.9% |
| (0.3, 0.4] | 2,824 | 34.5% | 32.8% |
| (0.4, 0.5] | 1,730 | 44.8% | 44.5% |
| (0.5, 0.6] | 1,287 | 54.9% | 55.3% |
| (0.6, 0.7] | 1,407 | 65.1% | 66.6% |
| (0.7, 1.0] | 2,264 | 79.2% | 78.8% |

Leans on: G_ewm 49%, G_l20 17%, G_rate20 14%, MI5_pg 3%, ITC_pg 1%, CL_pg 1%

