# NBL team model, step 1: margin and total

Fitted on 2016-17 to 2022-23 (965 games); the penalty was chosen by predicting each season from 2018-19 on from the seasons before it. Each later season is scored once. 2026-27 is this season to 18 Oct 2026, 36 games. No public NBL model with an archive of predictions was found to compare against, and no betting lines are held yet, so the benchmarks are a results-only rating and always picking the home team. **The test that matters, against the market, waits for recorded lines.**

**Honesty note.** The final-check seasons (2025-26, 2026-27) were scored once with a first version of this model (Elo K 0.06, penalty chosen on 2022-23 alone). The Elo settings and the penalty method were then changed, both chosen on 2016-17 to 2022-23 only, and everything was scored again; then squad on-court ratings from the play-by-play (nbl/model/onoff.py, settings chosen on 2016-17 to 2022-23 only) were added and it was scored a third time; then the bottom-up total (chosen on 2016-17 to 2022-23) was added and it was scored a fourth time. So this is a fourth look, not a clean one. No version beat the results-only rating on 2025-26 for margins.

Win chance = normal around the predicted margin, spread 13.0 points; total spread 16.7 points (training seasons).

## 2023-24 (confirmation season)

| model | games | winner picked | margin miss (pts) | Brier | log loss |
|---|---|---|---|---|---|
| results-only rating (Elo) | 154 | 57.8% | 10.9 | 0.241 | 0.674 |
| ours, squads named | 154 | 59.1% | 10.9 | 0.241 | 0.676 |
| home team, at the training home-win rate | 154 | 59.7% | 11.2 | 0.241 | 0.676 |
| ours, at the open (no team news) | 154 | 55.2% | 11.0 | 0.243 | 0.681 |

## 2024-25 (confirmation season)

| model | games | winner picked | margin miss (pts) | Brier | log loss |
|---|---|---|---|---|---|
| ours, squads named | 159 | 65.4% | 11.6 | 0.228 | 0.653 |
| ours, at the open (no team news) | 159 | 63.5% | 11.6 | 0.230 | 0.656 |
| results-only rating (Elo) | 159 | 64.2% | 11.7 | 0.230 | 0.657 |
| home team, at the training home-win rate | 159 | 56.0% | 12.2 | 0.247 | 0.686 |

## 2025-26 (final check)

| model | games | winner picked | margin miss (pts) | Brier | log loss |
|---|---|---|---|---|---|
| results-only rating (Elo) | 179 | 65.4% | 12.0 | 0.212 | 0.609 |
| ours, at the open (no team news) | 179 | 63.1% | 12.0 | 0.214 | 0.616 |
| ours, squads named | 179 | 63.1% | 12.1 | 0.214 | 0.616 |
| home team, at the training home-win rate | 179 | 53.1% | 14.0 | 0.251 | 0.694 |

## 2026-27 (final check)

| model | games | winner picked | margin miss (pts) | Brier | log loss |
|---|---|---|---|---|---|
| home team, at the training home-win rate | 40 | 60.0% | 11.3 | 0.241 | 0.675 |
| ours, squads named | 40 | 47.5% | 11.5 | 0.268 | 0.729 |
| results-only rating (Elo) | 40 | 47.5% | 11.3 | 0.269 | 0.731 |
| ours, at the open (no team news) | 40 | 47.5% | 11.4 | 0.271 | 0.735 |

Lower is better for margin miss, Brier and log loss. A coin flip scores Brier 0.250 and log loss 0.693.

## Is the win chance honest? (all test seasons, squads named)

| our home win chance | games | home won |
|---|---|---|
| 0% to 20% | 4 | 0% |
| 20% to 35% | 35 | 23% |
| 35% to 50% | 122 | 48% |
| 50% to 65% | 205 | 57% |
| 65% to 80% | 138 | 68% |
| 80% to 100% | 28 | 82% |

## Team news: how much the named squad moves the prediction (all test seasons)

| change in our margin, open to named | games | open margin miss | named margin miss |
|---|---|---|---|
| 0 to 1 pts | 484 | 11.4 | 11.4 |
| 1 to 2 pts | 38 | 13.4 | 13.2 |
| 2 to 4 pts | 8 | 11.9 | 10.2 |
| 4 to more pts | 2 | 14.8 | 19.0 |

## Totals

| season | games | total miss, ours named (pts) | ours open | always the training average |
|---|---|---|---|---|
| 2023-24 | 154 | 14.1 | 14.1 | 15.1 |
| 2024-25 | 159 | 15.2 | 15.2 | 19.1 |
| 2025-26 | 179 | 14.8 | 14.9 | 16.9 |
| 2026-27 | 40 | 15.3 | 15.5 | 19.2 |

Scores include overtime, as head-to-head, line and total bets settle.

## What the margin model leans on (named; standardised, points per standard deviation)

- intercept: +2.50
- elo_margin: +3.10
- d_net_ew: +2.56
- d_margin_ew: -4.03
- d_named_val: +0.23
- d_named_rapm: +2.10
- d_days_rest: -0.97
- d_b2b: +0.00
- d_travel_km: -0.16

Penalties chosen: m_elo 0.1, m_open 1, m_named 1, t_open 300, t_named 300.
