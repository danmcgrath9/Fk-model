# Back-test against Betfair SP

Fitted 2026-09-12 02:31 UTC over 326 resulted races (3386 runners), 2026-04-30 to 2026-08-31. Out of sample = fitted on the first 228 races by date, scored on the last 98.

Each model is a conditional logit fitted to minimise the cross-entropy against the BSP-implied chances. 'KL to BSP' is how far it sits from BSP (0 = BSP itself); 'log loss' is scored on the actual winners (lower is better); 'top pick won' is the share of races the model's highest-rated runner won.

| model | KL to BSP (in / out) | log loss vs winners (in / out) | top pick won (in / out) |
|---|---|---|---|
| bsp_itself | 0.0000 / 0.0000 | 1.8944 / 1.7667 | 35.1% / 35.7% |
| opening_market | 0.1145 / 0.1398 | 2.0273 / 1.8455 | 32.5% / 28.6% |
| neural_only | 0.2264 / 0.2665 | 2.1752 / 2.0202 | 21.1% / 27.6% |
| ratings_only | 0.2793 / 0.2958 | 2.0940 / 2.0596 | 23.2% / 24.5% |
| ratings_plus_distance | 0.2465 / 0.2650 | 2.0489 / 2.0350 | 30.7% / 25.5% |
| all_form | 0.1785 / 0.2061 | 2.0218 / 1.9530 | 25.9% / 25.5% |
| all_form_plus_class **(deployed)** | 0.1692 / 0.1993 | 2.0193 / 1.9294 | 27.6% / 30.6% |
| ratings_class_distance | 0.2332 / 0.2638 | 2.0440 / 2.0138 | 31.6% / 27.6% |
| all_form_plus_open_market | 0.1051 / 0.1272 | 1.9831 / 1.8352 | 33.3% / 26.5% |
| projection_sim | 0.3029 / 0.3236 | 2.1757 / 2.0971 | 29.4% / 28.6% |

Deployed: **all_form_plus_class**, the form-only model closest to BSP out of sample, refitted on all 326 races.

## Coefficients of the deployed model

- neural_rel: +1.8359
- last_rel: +0.1184
- peak_rel: -0.0019
- peak12_rel: +0.0501
- wfa_rel: -0.2137
- wfa_best_rel: +0.2166
- ohr_rel: -0.0032
- dist_rel: +0.0400
- dist_win: -0.1570
- last_vs_lws: +0.1184
- best_vs_lws: -0.2077
- trend_slope: +0.0132
- starts_log: -0.2871

projection_sim parameters on the training races: recent_runs 4, decay 0.7, scope_bonus 1.0, trend_weight 0.0, shape_weight 0.0, late_weight 0.5, sd_floor 3.0, light_sd 1.5, sd_scale 4.0, unrated_gap 10.0, unrated_sd 3.0, neural_weight 20.0

Runners with no rated run (projected at the field mean less the unrated gap): 109 of 3386.

Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the career peak and the 12-month peak; wfa_rel, wfa_best_rel = points below the best of the latest and the best WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean rating of runs within 200m of today's trip; dist_win = the record at the distance as a shrunk win rate, against the race mean; last_vs_lws, best_vs_lws = the latest and the best rated run against the race's Likely Winning Standard (class); trend_slope = rating points per run over the last six runs; starts_log = log of career starts against the race mean (scope); open_logit = log of the opening-market chance (comparison only, never deployed, so Value keeps meaning disagreement with the market).

## Calibration of the deployed model

| rated chance | runners | mean rated | share that won |
|---|---|---|---|
| 0% to 5% | 1030 | 3.1% | 2.4% |
| 5% to 10% | 1229 | 7.3% | 7.4% |
| 10% to 20% | 799 | 13.7% | 13.8% |
| 20% to 30% | 226 | 23.9% | 24.8% |
| 30% to 50% | 89 | 37.2% | 42.7% |
| 50% to 100% | 13 | 58.8% | 69.2% |
