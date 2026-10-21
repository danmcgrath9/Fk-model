# Team model, step 2: candidate improvements (head-to-head log loss)

Every candidate predicts each match from earlier information only. Choices are made on 2015-16 to 2022-23; 2023-24 to 2025-26 were already seen in step 1, so they are indicative only.

| candidate | 2015-16 to 2022-23 | vs dc (90% interval, by week) | 2023-24 to 2025-26 (seen) | vs dc |
|---|---|---|---|---|
| dc | 1.0349 |  | 1.0696 |  |
| dc_home60 | 1.0376 | +0.0026 (+0.0008 to +0.0045) | 1.0724 | +0.0028 (-0.0010 to +0.0068) |
| dc_home120 | 1.0345 | -0.0004 (-0.0008 to -0.0001) | 1.0695 | -0.0001 (-0.0008 to +0.0005) |
| dc_home240 | 1.0326 | -0.0023 (-0.0036 to -0.0011) | 1.0690 | -0.0006 (-0.0038 to +0.0027) |
| dc_recal | 1.0344 | -0.0005 (-0.0050 to +0.0040) | 1.0728 | +0.0033 (-0.0026 to +0.0091) |
| pi | 1.0394 | +0.0044 (-0.0076 to +0.0158) | 1.0843 | +0.0147 (+0.0030 to +0.0262) |
| elo | 1.0353 | +0.0004 (-0.0075 to +0.0082) | 1.0811 | +0.0115 (-0.0014 to +0.0245) |
| ens | 1.0309 | -0.0040 (-0.0109 to +0.0027) | 1.0757 | +0.0062 (-0.0027 to +0.0152) |

## Home sides priced 50% or more: predicted against happened

| candidate | block | games | predicted home win | happened |
|---|---|---|---|---|
| dc | select | 236 | 0.579 | 0.644 |
| dc | seen | 125 | 0.566 | 0.488 |
| dc_home120 | select | 249 | 0.578 | 0.639 |
| dc_home120 | seen | 126 | 0.566 | 0.492 |
| dc_recal | select | 354 | 0.585 | 0.573 |
| dc_recal | seen | 149 | 0.567 | 0.470 |
| ens | select | 335 | 0.582 | 0.591 |
| ens | seen | 139 | 0.553 | 0.439 |

Fitted home edge (log goals) by season with a 120-day home half-life: 2016-17 0.152, 2017-18 0.099, 2018-19 0.069, 2019-20 0.134, 2020-21 0.108, 2021-22 0.191, 2022-23 0.245, 2023-24 0.228, 2024-25 0.043, 2025-26 0.104

## Verdict

None of the published ideas that work on goals alone moves this model much, which is what the
literature predicts (docs/RESEARCH.md: the best score-based models are "nearly indistinguishable").
Adopted: the league level and home edge on their own 240-day half-life (settings.json `home_half_life`),
the one candidate better on the selection seasons with an interval clear of zero and no worse on the
seen seasons. Faster home decays were worse, so the A-League's home edge moves slowly. Not adopted:
recalibration, pi-ratings, Elo and the ensemble (no reliable gain, and worse on the seen seasons).
The real gains left need new information: the market (odds), line-ups (being pulled), and shots.
