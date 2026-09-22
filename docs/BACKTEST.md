# Back-test against Betfair SP

Fitted 2026-09-22 23:51 UTC over 386 resulted races (4024 runners), 2026-04-30 to 2026-09-22. Out of sample = fitted on the first 270 races by date, scored on the last 116.

Each model is a conditional logit fitted to minimise the cross-entropy against the BSP-implied chances. 'KL to BSP' is how far it sits from BSP (0 = BSP itself); 'log loss' is scored on the actual winners (lower is better); 'top pick won' is the share of races the model's highest-rated runner won.

| model | KL to BSP (in / out) | log loss vs winners (in / out) | top pick won (in / out) |
|---|---|---|---|
| bsp_itself | 0.0000 / 0.0000 | 1.8651 / 1.7809 | 35.6% / 37.9% |
| opening_market | 0.1187 / 0.1611 | 1.9821 / 1.9337 | 31.9% / 32.8% |
| neural_only | 0.2326 / 0.2860 | 2.1460 / 2.0778 | 21.1% / 25.9% |
| ratings_only | 0.2767 / 0.3261 | 2.0714 / 2.0623 | 25.2% / 30.2% |
| ratings_plus_distance | 0.2428 / 0.3055 | 2.0281 / 2.0459 | 31.1% / 27.6% |
| all_form | 0.1796 / 0.2450 | 1.9986 / 1.9950 | 26.3% / 27.6% |
| all_form_plus_class | 0.1713 / 0.2304 | 1.9928 / 1.9857 | 26.3% / 32.8% |
| ratings_class_distance | 0.2316 / 0.2881 | 2.0201 / 2.0354 | 31.9% / 28.4% |
| all_form_plus_open_market | 0.1080 / 0.1539 | 1.9400 / 1.9091 | 33.7% / 31.9% |
| distance_aware | 0.1709 / 0.2302 | 1.9895 / 1.9895 | 27.8% / 32.8% |
| distance_shape | 0.1706 / 0.2305 | 1.9875 / 1.9858 | 28.1% / 31.9% |
| distance_shape_exp | 0.0158 / 0.0662 | 1.8925 / 1.8466 | 34.4% / 33.6% |
| speed_only | 0.3391 / 0.4588 | 2.2202 / 2.2635 | 18.9% / 20.7% |
| form_plus_speed | 0.1696 / 0.2313 | 1.9946 / 1.9854 | 27.4% / 31.9% |
| distance_speed | 0.1692 / 0.2309 | 1.9925 / 1.9905 | 27.0% / 32.8% |
| everything | 0.1688 / 0.2313 | 1.9911 / 1.9864 | 27.8% / 32.8% |
| position_only | 0.2986 / 0.3791 | 2.1585 / 2.1668 | 24.1% / 19.8% |
| form_plus_position **(deployed)** | 0.1672 / 0.2274 | 1.9994 / 1.9832 | 28.9% / 30.2% |
| position_and_style | 0.1666 / 0.2289 | 1.9980 / 1.9801 | 28.1% / 29.3% |
| the_lot | 0.1651 / 0.2296 | 1.9946 / 1.9813 | 28.5% / 31.0% |
| projection_sim | 0.3034 / 0.3665 | 2.1628 / 2.1095 | 28.9% / 30.2% |

Deployed: **form_plus_position**, the form-only model closest to BSP out of sample, refitted on all 386 races.

## Coefficients of the deployed model

- neural_rel: +1.5821
- last_rel: +0.1152
- peak_rel: +0.0071
- peak12_rel: +0.0484
- wfa_rel: -0.2127
- wfa_best_rel: +0.2278
- ohr_rel: -0.0012
- dist_rel: +0.0370
- dist_win: -0.2102
- last_vs_lws: +0.1152
- best_vs_lws: -0.2264
- trend_slope: -0.0013
- starts_log: -0.2982
- settle_share: -0.5934
- pos800_share: -0.1768
- pos_gain: +0.2818
- late_gain: +0.3632

projection_sim parameters on the training races: recent_runs 4, decay 0.7, scope_bonus 1.0, trend_weight 0.0, shape_weight 0.0, late_weight 0.5, sd_floor 3.0, light_sd 1.5, sd_scale 4.0, unrated_gap 7.0, unrated_sd 3.0, neural_weight 20.0

Runners with no rated run (projected at the field mean less the unrated gap): 168 of 4024.

Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the career peak and the 12-month peak; speed_rel, speed_best_rel = points below the race's best of Form King's speed figure (100 = class par) read over the last 4 races newest-weighted, and of the best one; finish_speed_rel = the same over finishing speed (last 600 as a share of the run to the 600); last600_rel, to600_rel = the last 600m and the run to it against the class standard, in lengths; settle_share, pos800_share = where the horse settles and where it sits with 800m to run, as a share of its own field (0 = on the lead, 1 = last) read over its recent races and centred on today's field; pos_gain, late_gain = positions made up from settling and from the 400m to the post, on the same share; style_x_tempo = that settling share against the expected tempo, so a backmarker in a slow-run race reads negative; map_vs_habit = how far today's speedmap asks the horse to race from where it usually does; wfa_rel, wfa_best_rel = points below the best of the latest and the best WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean rating of runs within 200m of today's trip; dist_win = the record at the distance as a shrunk win rate, against the race mean; last_vs_lws, best_vs_lws = the latest and the best rated run against the race's Likely Winning Standard (class); trend_slope = rating points per run over the last six runs; starts_log = log of career starts against the race mean (scope); open_logit = log of the opening-market chance (comparison only, never deployed, so Value keeps meaning disagreement with the market).

## Calibration of the deployed model

| rated chance | runners | mean rated | share that won |
|---|---|---|---|
| 0% to 5% | 1241 | 3.1% | 2.3% |
| 5% to 10% | 1455 | 7.2% | 7.8% |
| 10% to 20% | 913 | 13.8% | 13.4% |
| 20% to 30% | 274 | 24.0% | 24.5% |
| 30% to 50% | 103 | 37.5% | 45.6% |
| 50% to 100% | 17 | 56.5% | 64.7% |

## The plans, replayed over 386 races the fit never saw

Five blocks by date, each priced by a model fitted on the other four; bets at the OPENING price and settled at Betfair SP (the live book's rule), then the same bets at BSP itself. A plan that only pays at the opening price is living on the market firming after it, which a real bet placed late does not get.

| plan | bets | winners | staked | returned | profit | return | at BSP: profit | return |
|---|---|---|---|---|---|---|---|---|
| top_pick | 386 | 112 | 386.0 | 427.6 | +41.6 | +10.8% | +41.6 | +10.8% |
| value_flags | 395 | 63 | 395.0 | 382.2 | -12.8 | -3.2% | +92.6 | +16.9% |
| value_under_8 | 303 | 55 | 303.0 | 278.1 | -24.9 | -8.2% | -73.4 | -22.2% |
| top_pick_to_win_1 | 385 | 112 | 161.2 | 185.0 | +23.8 | +14.8% | +23.3 | +13.5% |
| kelly_quarter | 1789 | 139 | 1567.8 | 1707.6 | +139.8 | +8.9% | +191.5 | +8.0% |
