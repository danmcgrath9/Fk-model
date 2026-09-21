# Back-test against Betfair SP

Fitted 2026-09-21 23:55 UTC over 327 resulted races (3393 runners), 2026-04-30 to 2026-09-09. Out of sample = fitted on the first 228 races by date, scored on the last 99.

Each model is a conditional logit fitted to minimise the cross-entropy against the BSP-implied chances. 'KL to BSP' is how far it sits from BSP (0 = BSP itself); 'log loss' is scored on the actual winners (lower is better); 'top pick won' is the share of races the model's highest-rated runner won.

| model | KL to BSP (in / out) | log loss vs winners (in / out) | top pick won (in / out) |
|---|---|---|---|
| bsp_itself | 0.0000 / 0.0000 | 1.8944 / 1.7592 | 35.1% / 36.4% |
| opening_market | 0.1145 / 0.1386 | 2.0273 / 1.8376 | 32.5% / 29.3% |
| neural_only | 0.2264 / 0.2653 | 2.1752 / 2.0118 | 21.1% / 28.3% |
| ratings_only | 0.2793 / 0.2962 | 2.0940 / 2.0572 | 23.2% / 24.2% |
| ratings_plus_distance | 0.2465 / 0.2660 | 2.0489 / 2.0334 | 30.7% / 25.3% |
| all_form | 0.1785 / 0.2063 | 2.0218 / 1.9469 | 25.9% / 25.3% |
| all_form_plus_class **(deployed)** | 0.1692 / 0.1994 | 2.0193 / 1.9244 | 27.6% / 30.3% |
| ratings_class_distance | 0.2332 / 0.2649 | 2.0440 / 2.0136 | 31.6% / 27.3% |
| all_form_plus_open_market | 0.1051 / 0.1262 | 1.9831 / 1.8274 | 33.3% / 27.3% |
| distance_aware | 0.1682 / 0.1998 | 2.0116 / 1.9298 | 29.4% / 30.3% |
| distance_shape | 0.1680 / 0.2006 | 2.0107 / 1.9264 | 28.9% / 30.3% |
| distance_shape_exp | 0.0132 / 0.0237 | 1.9183 / 1.7944 | 33.8% / 33.3% |
| projection_sim | 0.3029 / 0.3228 | 2.1757 / 2.0906 | 29.4% / 28.3% |

Deployed: **all_form_plus_class**, the form-only model closest to BSP out of sample, refitted on all 327 races.

## Coefficients of the deployed model

- neural_rel: +1.8393
- last_rel: +0.1182
- peak_rel: -0.0021
- peak12_rel: +0.0500
- wfa_rel: -0.2134
- wfa_best_rel: +0.2165
- ohr_rel: -0.0032
- dist_rel: +0.0397
- dist_win: -0.1598
- last_vs_lws: +0.1182
- best_vs_lws: -0.2074
- trend_slope: +0.0132
- starts_log: -0.2876

projection_sim parameters on the training races: recent_runs 4, decay 0.7, scope_bonus 1.0, trend_weight 0.0, shape_weight 0.0, late_weight 0.5, sd_floor 3.0, light_sd 1.5, sd_scale 4.0, unrated_gap 10.0, unrated_sd 3.0, neural_weight 20.0

Runners with no rated run (projected at the field mean less the unrated gap): 113 of 3393.

Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the career peak and the 12-month peak; wfa_rel, wfa_best_rel = points below the best of the latest and the best WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean rating of runs within 200m of today's trip; dist_win = the record at the distance as a shrunk win rate, against the race mean; last_vs_lws, best_vs_lws = the latest and the best rated run against the race's Likely Winning Standard (class); trend_slope = rating points per run over the last six runs; starts_log = log of career starts against the race mean (scope); open_logit = log of the opening-market chance (comparison only, never deployed, so Value keeps meaning disagreement with the market).

## Calibration of the deployed model

| rated chance | runners | mean rated | share that won |
|---|---|---|---|
| 0% to 5% | 1031 | 3.1% | 2.4% |
| 5% to 10% | 1234 | 7.3% | 7.4% |
| 10% to 20% | 798 | 13.7% | 13.8% |
| 20% to 30% | 227 | 23.9% | 25.1% |
| 30% to 50% | 90 | 37.1% | 42.2% |
| 50% to 100% | 13 | 58.8% | 69.2% |

## The plans, replayed over 327 races the fit never saw

Five blocks by date, each priced by a model fitted on the other four; bets at the OPENING price and settled at Betfair SP (the live book's rule), then the same bets at BSP itself. A plan that only pays at the opening price is living on the market firming after it, which a real bet placed late does not get.

| plan | bets | winners | staked | returned | profit | return | at BSP: profit | return |
|---|---|---|---|---|---|---|---|---|
| top_pick | 327 | 90 | 327.0 | 339.7 | +12.7 | +3.9% | +12.7 | +3.9% |
| value_flags | 342 | 54 | 342.0 | 373.5 | +31.5 | +9.2% | +31.5 | +9.2% |
| value_under_8 | 251 | 46 | 251.0 | 239.8 | -11.2 | -4.5% | -11.2 | -4.5% |
| top_pick_to_win_1 | 327 | 90 | 137.6 | 157.4 | +19.8 | +14.4% | +9.8 | +6.9% |
| kelly_quarter | 1537 | 122 | 1352.4 | 1562.6 | +210.2 | +15.5% | +235.5 | +11.6% |
