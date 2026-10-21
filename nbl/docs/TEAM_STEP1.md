# NBL team model, step 1: margin and total

Fitted on 2016-17 to 2022-23 (965 games); the penalty was chosen by predicting each season from 2018-19 on from the seasons before it. Each later season is scored once. 2026-27 is this season to 18 Oct 2026, 36 games. No public NBL model with an archive of predictions was found to compare against, and no betting lines are held yet, so the benchmarks are a results-only rating and always picking the home team. **The test that matters, against the market, waits for recorded lines.**

**Honesty note.** The final-check seasons (2025-26, 2026-27) were scored once with a first version of this model (Elo K 0.06, penalty chosen on 2022-23 alone). The Elo settings and the penalty method were then changed, both chosen on 2016-17 to 2022-23 only, and everything was scored again. It is a second look, not a clean one; the first version was no better on those seasons.

Win chance = normal around the predicted margin, spread 13.1 points; total spread 16.9 points (training seasons).

## 2023-24 (confirmation season)

| model | games | winner picked | margin miss (pts) | Brier | log loss |
|---|---|---|---|---|---|
| results-only rating (Elo) | 154 | 57.8% | 10.9 | 0.241 | 0.674 |
| home team, at the training home-win rate | 154 | 59.7% | 11.2 | 0.241 | 0.676 |
| ours, squads named | 154 | 56.5% | 11.1 | 0.244 | 0.683 |
| ours, at the open (no team news) | 154 | 56.5% | 11.1 | 0.244 | 0.684 |

## 2024-25 (confirmation season)

| model | games | winner picked | margin miss (pts) | Brier | log loss |
|---|---|---|---|---|---|
| results-only rating (Elo) | 159 | 64.2% | 11.7 | 0.230 | 0.657 |
| ours, squads named | 159 | 66.0% | 11.8 | 0.234 | 0.665 |
| ours, at the open (no team news) | 159 | 66.7% | 11.8 | 0.235 | 0.666 |
| home team, at the training home-win rate | 159 | 56.0% | 12.2 | 0.247 | 0.686 |

## 2025-26 (final check)

| model | games | winner picked | margin miss (pts) | Brier | log loss |
|---|---|---|---|---|---|
| results-only rating (Elo) | 179 | 65.4% | 12.0 | 0.212 | 0.609 |
| ours, squads named | 179 | 62.6% | 12.1 | 0.214 | 0.615 |
| ours, at the open (no team news) | 179 | 62.6% | 12.1 | 0.214 | 0.616 |
| home team, at the training home-win rate | 179 | 53.1% | 14.0 | 0.251 | 0.694 |

## 2026-27 (final check)

| model | games | winner picked | margin miss (pts) | Brier | log loss |
|---|---|---|---|---|---|
| home team, at the training home-win rate | 36 | 61.1% | 10.7 | 0.239 | 0.672 |
| ours, at the open (no team news) | 36 | 47.2% | 11.0 | 0.274 | 0.743 |
| ours, squads named | 36 | 44.4% | 11.0 | 0.274 | 0.744 |
| results-only rating (Elo) | 36 | 44.4% | 10.9 | 0.275 | 0.745 |

Lower is better for margin miss, Brier and log loss. A coin flip scores Brier 0.250 and log loss 0.693.

## Is the win chance honest? (all test seasons, squads named)

| our home win chance | games | home won |
|---|---|---|
| 0% to 20% | 3 | 0% |
| 20% to 35% | 28 | 32% |
| 35% to 50% | 121 | 46% |
| 50% to 65% | 209 | 56% |
| 65% to 80% | 138 | 67% |
| 80% to 100% | 29 | 83% |

## Team news: how much the named squad moves the prediction (all test seasons)

| change in our margin, open to named | games | open margin miss | named margin miss |
|---|---|---|---|
| 0 to 1 pts | 528 | 11.6 | 11.6 |

## Totals

| season | games | total miss, ours named (pts) | ours open | always the training average |
|---|---|---|---|---|
| 2023-24 | 154 | 14.0 | 14.1 | 15.1 |
| 2024-25 | 159 | 15.6 | 15.6 | 19.1 |
| 2025-26 | 179 | 15.1 | 15.2 | 16.9 |
| 2026-27 | 36 | 15.9 | 16.3 | 19.4 |

Scores include overtime, as head-to-head, line and total bets settle.

## What the margin model leans on (named; standardised, points per standard deviation)

- intercept: +2.50
- elo_margin: +5.67
- d_net_ew: +2.44
- d_margin_ew: -4.51
- d_named_val: +0.03
- d_days_rest: -0.97
- d_b2b: +0.00
- d_travel_km: -0.18

Penalties chosen: m_elo 0.1, m_open 0.1, m_named 1, t_open 300, t_named 300.
