# Back-test against Betfair SP

Fitted 2026-09-23 02:27 UTC over 856 resulted races (8856 runners), 2026-04-30 to 2026-09-22. Out of sample = fitted on the first 599 races by date, scored on the last 257.

Each model is a conditional logit fitted to minimise the cross-entropy against a target: the BSP-implied chances, or ('@winners') the actual result. 'KL to BSP' is how far it sits from Betfair SP, the sharpest price anyone gets and so the stand-in for the truth. **The bar is not zero, it is the morning market**, which sits at 0.1470 out of sample: that is the price we bet into, so a model closer to BSP than it is has beaten the market it is betting against. 'log loss' is scored on the actual winners and 'top pick won' is the share of races the model's highest-rated runner won.

| model | KL to BSP (in / out) | vs the morning market | ridge | log loss vs winners (in / out) | top pick won (in / out) |
|---|---|---|---|---|---|
| bsp_itself | 0.0000 / 0.0000 | - | - | 1.8788 / 1.7722 | 32.7% / 38.5% |
| opening_market | 0.1271 / 0.1470 | the bar | - | 2.0271 / 1.8775 | 27.2% / 34.2% |
| neural_only | 0.2450 / 0.2600 | +0.1130 | 1e-08 | 2.1616 / 2.0356 | 21.4% / 24.9% |
| ratings_only | 0.2676 / 0.3096 | +0.1627 | 1 | 2.1625 / 2.0048 | 21.4% / 30.4% |
| ratings_plus_distance | 0.2462 / 0.2852 | +0.1382 | 0.01 | 2.1376 / 1.9870 | 23.0% / 30.0% |
| all_form | 0.1949 / 0.2170 | +0.0700 | 0.01 | 2.0998 / 1.9327 | 24.5% / 30.4% |
| all_form_plus_class | 0.1891 / 0.2114 | +0.0644 | 1 | 2.0944 / 1.9232 | 24.9% / 32.7% |
| ratings_class_distance | 0.2412 / 0.2790 | +0.1320 | 0.01 | 2.1336 / 1.9772 | 23.4% / 29.6% |
| all_form_plus_open_market | 0.1157 / 0.1391 | BEATS IT | 0.01 | 2.0150 / 1.8492 | 27.7% / 33.9% |
| all_form_plus_open_market @winners | 0.1284 / 0.1921 | +0.0451 | 1 | 2.0014 / 1.8740 | 28.2% / 35.8% |
| distance_aware | 0.1882 / 0.2110 | +0.0640 | 0.01 | 2.0958 / 1.9247 | 25.0% / 32.3% |
| distance_shape | 0.1876 / 0.2101 | +0.0631 | 1 | 2.0960 / 1.9224 | 25.0% / 31.9% |
| distance_shape_exp | 0.0174 / 0.0417 | BEATS IT | 0.01 | 1.8995 / 1.8249 | 31.9% / 35.0% |
| speed_only | 0.3443 / 0.4068 | +0.2598 | 1 | 2.2306 / 2.1919 | 20.0% / 23.7% |
| form_plus_speed | 0.1871 / 0.2113 | +0.0643 | 1 | 2.0945 / 1.9250 | 24.5% / 32.3% |
| distance_speed | 0.1863 / 0.2108 | +0.0638 | 1 | 2.0951 / 1.9256 | 24.5% / 32.3% |
| everything | 0.1854 / 0.2097 | +0.0627 | 1 | 2.0951 / 1.9256 | 24.5% / 32.3% |
| position_only | 0.3037 / 0.3412 | +0.1942 | 0.01 | 2.1936 / 2.1118 | 20.7% / 24.9% |
| form_plus_position | 0.1829 / 0.2076 | +0.0606 | 1 | 2.0917 / 1.9225 | 25.7% / 31.9% |
| position_and_style | 0.1824 / 0.2079 | +0.0609 | 1 | 2.0938 / 1.9237 | 25.5% / 31.1% |
| the_lot | 0.1803 / 0.2079 | +0.0609 | 1 | 2.0933 / 1.9224 | 24.7% / 33.1% |
| market_plus_class | 0.1153 / 0.1395 | BEATS IT | 1 | 2.0144 / 1.8480 | 28.0% / 34.2% |
| market_plus_distance | 0.1149 / 0.1392 | BEATS IT | 1 | 2.0144 / 1.8487 | 28.4% / 34.2% |
| market_plus_speed | 0.1147 / 0.1400 | BEATS IT | 1 | 2.0137 / 1.8457 | 27.9% / 35.0% |
| market_plus_position | 0.1150 / 0.1392 | BEATS IT | 1 | 2.0155 / 1.8466 | 27.9% / 35.4% |
| market_plus_everything | 0.1139 / 0.1397 | BEATS IT | 1 | 2.0150 / 1.8453 | 28.2% / 33.9% |
| market_the_lot | 0.1138 / 0.1399 | BEATS IT | 1 | 2.0161 / 1.8439 | 28.9% / 34.2% |
| market_shaped | 0.1148 / 0.1397 | BEATS IT | 1 | 2.0150 / 1.8499 | 28.2% / 34.6% |
| market_shaped_all | 0.1133 / 0.1399 | BEATS IT | 1 | 2.0157 / 1.8470 | 28.2% / 34.2% |
| extras_only | 0.3051 / 0.3432 | +0.1962 | 0.01 | 2.2095 / 2.1500 | 17.7% / 21.4% |
| form_plus_extras | 0.1672 / 0.1928 | +0.0458 | 1 | 2.0718 / 1.9082 | 24.9% / 33.1% |
| kitchen_sink | 0.1595 / 0.1901 | +0.0431 | 1 | 2.0696 / 1.9072 | 26.7% / 33.9% |
| market_kitchen_sink **(deployed)** | 0.1055 / 0.1358 | BEATS IT | 1 | 2.0066 / 1.8438 | 29.5% / 34.6% |
| market_kitchen_sink @winners | 0.1391 / 0.2071 | +0.0602 | 1 | 1.9716 / 1.8932 | 29.9% / 35.8% |
| projection_sim | 0.3213 / 0.3452 | +0.1982 | - | 2.1903 / 2.0627 | 23.0% / 31.9% |

Deployed: **market_kitchen_sink**, the model closest to BSP out of sample, refitted on all 856 races. It BEATS the morning market. The morning price is a legitimate input: we bet into it, so using it and landing closer to BSP than it does is exactly what beating the market means. EXP is the one thing barred, because Form King derives it from the market without saying which one and it scores like a figure that already knows the close. '@winners' marks a model fitted to the actual result rather than to the closing price.

## Coefficients of the deployed model

- neural_rel: +0.1767
- last_rel: +0.0106
- peak_rel: +0.0062
- peak12_rel: +0.0155
- wfa_rel: -0.0032
- wfa_best_rel: -0.0932
- ohr_rel: -0.0013
- dist_rel: +0.0188
- dist_win: +0.0410
- last_vs_lws: +0.0106
- best_vs_lws: +0.0855
- trend_slope: +0.0075
- starts_log: -0.0213
- last_dist_rel: -0.0061
- best_dist_rel: +0.0071
- dist_change: -0.0018
- speed_rel: +0.0008
- speed_best_rel: -0.0011
- finish_speed_rel: +0.0103
- last600_rel: -0.0082
- to600_rel: +0.0024
- settle_share: -0.0260
- pos800_share: -0.1488
- pos_gain: -0.1693
- late_gain: +0.3373
- early_pos: +0.0157
- early_x_tempo: -0.0208
- style_x_tempo: +0.0286
- map_vs_habit: -0.0573
- barrier_share: +0.0625
- days_log: -0.0586
- run_in_prep: -0.0041
- weight_rel: +0.0096
- wfa_diff: +0.0628
- beaten_3: -0.0023
- prize_log: -0.0304
- track_win: +0.2731
- going_win: +0.4018
- class_win: -0.0000
- td_win: +0.1572
- wet_win: +0.0000
- up_win: +0.1042
- jockey_win: +0.0289
- trainer_win: +0.0072
- jt_combo_win: +0.0000
- open_logit: +0.7999
- market_prob: -0.0809
- market_x_neural: -0.0875

projection_sim parameters on the training races: recent_runs 4, decay 0.7, scope_bonus 0.0, trend_weight 0.0, shape_weight 0.0, late_weight 0.5, sd_floor 3.0, light_sd 1.5, sd_scale 3.0, unrated_gap 7.0, unrated_sd 3.0, neural_weight 15.0

Runners with no rated run (projected at the field mean less the unrated gap): 555 of 8856.

Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the open_logit = the log of the opening-market chance and market_prob the chance itself, carried together so the fit can bend the market's own curve (short prices are historically underbet and long ones overbet, and log-chance alone cannot correct that); market_x_neural = the market read against Neural. The move from the open to the price NOW is deliberately absent: a race pulled after it ran carries its FINAL price, so it would be reading the answer. career peak and the 12-month peak; speed_rel, speed_best_rel = points below the race's best of Form King's speed figure (100 = class par) read over the last 4 races newest-weighted, and of the best one; finish_speed_rel = the same over finishing speed (last 600 as a share of the run to the 600); last600_rel, to600_rel = the last 600m and the run to it against the class standard, in lengths; settle_share, pos800_share = where the horse settles and where it sits with 800m to run, as a share of its own field (0 = on the lead, 1 = last) read over its recent races and centred on today's field; pos_gain, late_gain = positions made up from settling and from the 400m to the post, on the same share; style_x_tempo = that settling share against the expected tempo, so a backmarker in a slow-run race reads negative; map_vs_habit = how far today's speedmap asks the horse to race from where it usually does; wfa_rel, wfa_best_rel = points below the best of the latest and the best WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean rating of runs within 200m of today's trip; dist_win = the record at the distance as a shrunk win rate, against the race mean; last_vs_lws, best_vs_lws = the latest and the best rated run against the race's Likely Winning Standard (class); trend_slope = rating points per run over the last six runs; starts_log = log of career starts against the race mean (scope); open_logit = log of the opening-market chance (comparison only, never deployed, so Value keeps meaning disagreement with the market).

## Calibration of the deployed model

| rated chance | runners | mean rated | share that won |
|---|---|---|---|
| 0% to 5% | 3312 | 2.6% | 2.8% |
| 5% to 10% | 2364 | 7.2% | 6.9% |
| 10% to 20% | 2142 | 14.0% | 14.0% |
| 20% to 30% | 670 | 24.0% | 24.3% |
| 30% to 50% | 303 | 36.9% | 37.6% |
| 50% to 100% | 44 | 57.5% | 65.9% |

## The plans, replayed over 856 races the fit never saw

Five blocks by date, each priced by a model fitted on the other four. Every bet is chosen against the MORNING market and struck at the morning price. The two profit columns are the SAME bets on two settlement bases: paid at Betfair SP, which is what betting into the jump gets you, and paid at the price it was struck at, which is what taking the morning price gets you. They differ by however far the selections moved.

| plan | bets | winners | staked | at BSP: profit | return | at the struck price: profit | return |
|---|---|---|---|---|---|---|---|
| top_pick | 856 | 258 | 856.0 | +33.8 | +4.0% | +36.3 | +4.2% |
| value_flags | 236 | 72 | 236.0 | -8.5 | -3.6% | +55.2 | +23.4% |
| value_under_8 | 231 | 72 | 231.0 | -3.5 | -1.5% | +60.2 | +26.1% |
| top_pick_to_win_1 | 855 | 258 | 524.6 | -81.2 | -15.5% | -108.1 | -20.6% |
| kelly_quarter | 2358 | 283 | 1536.5 | +5.1 | +0.3% | +697.2 | +45.4% |
