# Back-test against Betfair SP

Fitted 2026-09-12 02:05 UTC over 209 resulted races (2095 runners), 2026-04-30 to 2026-08-31. Out of sample = fitted on the first 146 races by date, scored on the last 63.

Each model is a conditional logit fitted to minimise the cross-entropy against the BSP-implied chances. 'KL to BSP' is how far it sits from BSP (0 = BSP itself); 'log loss' is scored on the actual winners (lower is better); 'top pick won' is the share of races the model's highest-rated runner won.

| model | KL to BSP (in / out) | log loss vs winners (in / out) | top pick won (in / out) |
|---|---|---|---|
| bsp_itself | 0.0000 / 0.0000 | 1.7528 / 1.8102 | 39.7% / 33.3% |
| opening_market | 0.1367 / 0.1341 | 1.8497 / 1.9125 | 34.9% / 27.0% |
| neural_only | 0.2410 / 0.2653 | 2.0231 / 2.0546 | 21.9% / 30.2% |
| ratings_only | 0.2786 / 0.3133 | 2.0126 / 2.1169 | 24.7% / 17.5% |
| ratings_plus_distance | 0.2540 / 0.2897 | 1.9804 / 2.0896 | 30.1% / 25.4% |
| all_form | 0.1877 / 0.2152 | 1.9114 / 2.0110 | 27.4% / 27.0% |
| all_form_plus_class **(deployed)** | 0.1832 / 0.2067 | 1.9005 / 1.9867 | 27.4% / 33.3% |
| ratings_class_distance | 0.2495 / 0.2825 | 1.9683 / 2.0721 | 30.8% / 27.0% |
| all_form_plus_open_market | 0.1234 / 0.1278 | 1.8214 / 1.9136 | 35.6% / 20.6% |
| projection_sim | 0.8065 / 1.2131 | 2.5643 / 3.4716 | 26.7% / 14.3% |

Deployed: **all_form_plus_class**, the form-only model closest to BSP out of sample, refitted on all 209 races.

## Coefficients of the deployed model

- neural_rel: +1.7651
- last_rel: +0.0002
- peak_rel: +0.0146
- peak12_rel: +0.0447
- wfa_rel: +0.0260
- wfa_best_rel: +0.0009
- ohr_rel: -0.0021
- dist_rel: +0.0340
- dist_win: +0.0058
- last_vs_lws: +0.0002
- best_vs_lws: -0.0021
- trend_slope: -0.0034
- starts_log: -0.2331

projection_sim parameters on the training races: recent_runs 4, decay 0.7, scope_bonus 0.0, trend_weight 0.0, shape_weight 0.0, late_weight 0.0, sd_floor 3.0, light_sd 1.5, sd_scale 2.2

Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the career peak and the 12-month peak; wfa_rel, wfa_best_rel = points below the best of the latest and the best WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean rating of runs within 200m of today's trip; dist_win = the record at the distance as a shrunk win rate, against the race mean; last_vs_lws, best_vs_lws = the latest and the best rated run against the race's Likely Winning Standard (class); trend_slope = rating points per run over the last six runs; starts_log = log of career starts against the race mean (scope); open_logit = log of the opening-market chance (comparison only, never deployed, so Value keeps meaning disagreement with the market).

## Calibration of the deployed model

| rated chance | runners | mean rated | share that won |
|---|---|---|---|
| 0% to 5% | 621 | 3.1% | 1.8% |
| 5% to 10% | 749 | 7.3% | 7.5% |
| 10% to 20% | 491 | 13.8% | 14.3% |
| 20% to 30% | 159 | 24.1% | 25.2% |
| 30% to 50% | 66 | 36.5% | 40.9% |
| 50% to 100% | 9 | 60.3% | 66.7% |
