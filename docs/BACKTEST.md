# Back-test against Betfair SP

Fitted 2026-09-22 00:11 UTC over 378 resulted races (3940 runners), 2026-04-30 to 2026-09-21. Out of sample = fitted on the first 264 races by date, scored on the last 114.

Each model is a conditional logit fitted to minimise the cross-entropy against the BSP-implied chances. 'KL to BSP' is how far it sits from BSP (0 = BSP itself); 'log loss' is scored on the actual winners (lower is better); 'top pick won' is the share of races the model's highest-rated runner won.

| model | KL to BSP (in / out) | log loss vs winners (in / out) | top pick won (in / out) |
|---|---|---|---|
| bsp_itself | 0.0000 / 0.0000 | 1.8699 / 1.7879 | 35.6% / 37.7% |
| opening_market | 0.1190 / 0.1589 | 1.9887 / 1.9421 | 32.2% / 31.6% |
| neural_only | 0.2325 / 0.2815 | 2.1465 / 2.0805 | 21.2% / 25.4% |
| ratings_only | 0.2761 / 0.3279 | 2.0699 / 2.0663 | 25.4% / 28.9% |
| ratings_plus_distance | 0.2421 / 0.3089 | 2.0287 / 2.0360 | 31.4% / 26.3% |
| all_form | 0.1790 / 0.2427 | 1.9959 / 1.9855 | 26.5% / 28.1% |
| all_form_plus_class | 0.1709 / 0.2305 | 1.9916 / 1.9804 | 25.8% / 32.5% |
| ratings_class_distance | 0.2313 / 0.2925 | 2.0223 / 2.0288 | 31.8% / 28.9% |
| all_form_plus_open_market | 0.1081 / 0.1532 | 1.9437 / 1.9140 | 33.7% / 31.6% |
| distance_aware **(deployed)** | 0.1703 / 0.2305 | 1.9883 / 1.9826 | 28.4% / 32.5% |
| distance_shape | 0.1700 / 0.2312 | 1.9869 / 1.9771 | 28.4% / 30.7% |
| distance_shape_exp | 0.0158 / 0.0632 | 1.8959 / 1.8527 | 34.5% / 33.3% |
| projection_sim | 0.3032 / 0.3667 | 2.1629 / 2.1103 | 29.2% / 29.8% |

Deployed: **distance_aware**, the form-only model closest to BSP out of sample, refitted on all 378 races.

## Coefficients of the deployed model

- neural_rel: +1.7667
- last_rel: +0.1107
- peak_rel: +0.0056
- peak12_rel: +0.0499
- wfa_rel: -0.1972
- wfa_best_rel: +0.2092
- ohr_rel: -0.0024
- dist_rel: +0.0301
- dist_win: -0.2188
- last_vs_lws: +0.1107
- best_vs_lws: -0.2146
- trend_slope: +0.0055
- starts_log: -0.3124
- last_dist_rel: +0.0028
- best_dist_rel: +0.0143
- dist_change: +0.0002

projection_sim parameters on the training races: recent_runs 4, decay 0.7, scope_bonus 1.0, trend_weight 0.0, shape_weight 0.0, late_weight 0.5, sd_floor 3.0, light_sd 1.5, sd_scale 4.0, unrated_gap 10.0, unrated_sd 3.0, neural_weight 20.0

Runners with no rated run (projected at the field mean less the unrated gap): 164 of 3940.

Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the career peak and the 12-month peak; wfa_rel, wfa_best_rel = points below the best of the latest and the best WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean rating of runs within 200m of today's trip; dist_win = the record at the distance as a shrunk win rate, against the race mean; last_vs_lws, best_vs_lws = the latest and the best rated run against the race's Likely Winning Standard (class); trend_slope = rating points per run over the last six runs; starts_log = log of career starts against the race mean (scope); open_logit = log of the opening-market chance (comparison only, never deployed, so Value keeps meaning disagreement with the market).

## Calibration of the deployed model

| rated chance | runners | mean rated | share that won |
|---|---|---|---|
| 0% to 5% | 1206 | 3.2% | 2.3% |
| 5% to 10% | 1407 | 7.2% | 7.5% |
| 10% to 20% | 932 | 13.8% | 13.8% |
| 20% to 30% | 263 | 24.1% | 23.6% |
| 30% to 50% | 98 | 37.1% | 44.9% |
| 50% to 100% | 16 | 56.9% | 75.0% |

## The plans, replayed over 378 races the fit never saw

Five blocks by date, each priced by a model fitted on the other four; bets at the OPENING price and settled at Betfair SP (the live book's rule), then the same bets at BSP itself. A plan that only pays at the opening price is living on the market firming after it, which a real bet placed late does not get.

| plan | bets | winners | staked | returned | profit | return | at BSP: profit | return |
|---|---|---|---|---|---|---|---|---|
| top_pick | 378 | 102 | 378.0 | 352.9 | -25.1 | -6.7% | -25.1 | -6.7% |
| value_flags | 400 | 66 | 400.0 | 449.7 | +49.7 | +12.4% | +9.9 | +1.8% |
| value_under_8 | 296 | 58 | 296.0 | 291.7 | -4.3 | -1.4% | -62.1 | -19.1% |
| top_pick_to_win_1 | 377 | 102 | 155.3 | 172.2 | +17.0 | +10.9% | +13.6 | +8.2% |
| kelly_quarter | 1762 | 146 | 1545.8 | 1726.9 | +181.0 | +11.7% | +251.1 | +10.6% |
