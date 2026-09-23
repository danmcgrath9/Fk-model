# Back-test against Betfair SP

Fitted 2026-09-23 04:30 UTC over 1330 resulted races (13610 runners), 2026-04-30 to 2026-09-22. Out of sample = fitted on the first 930 races by date, scored on the last 400.

Each model is a conditional logit fitted to minimise the cross-entropy against a target: the BSP-implied chances, or ('@winners') the actual result. 'KL to BSP' is how far it sits from Betfair SP, the sharpest price anyone gets and so the stand-in for the truth. **The bar is not zero, it is the morning market**, which sits at 0.1478 out of sample: that is the price we bet into, so a model closer to BSP than it is has beaten the market it is betting against. 'log loss' is scored on the actual winners and 'top pick won' is the share of races the model's highest-rated runner won.

| model | KL to BSP (in / out) | vs the morning market | ridge | log loss vs winners (in / out) | top pick won (in / out) |
|---|---|---|---|---|---|
| bsp_itself | 0.0000 / 0.0000 | - | - | 1.8619 / 1.7824 | 32.0% / 35.5% |
| opening_market | 0.1310 / 0.1478 | the bar | - | 2.0113 / 1.9139 | 27.0% / 31.8% |
| neural_only | 0.2494 / 0.2597 | +0.1118 | 0.01 | 2.1429 / 2.0597 | 21.3% / 23.5% |
| ratings_only | 0.2769 / 0.3021 | +0.1543 | 1 | 2.1490 / 2.0422 | 21.5% / 27.3% |
| ratings_plus_distance | 0.2533 / 0.2766 | +0.1287 | 1e-08 | 2.1210 / 2.0266 | 22.4% / 27.5% |
| all_form | 0.2017 / 0.2098 | +0.0619 | 1e-08 | 2.0839 / 1.9796 | 23.5% / 27.8% |
| all_form_plus_class | 0.1968 / 0.2046 | +0.0567 | 0.01 | 2.0855 / 1.9722 | 23.8% / 28.5% |
| ratings_class_distance | 0.2496 / 0.2708 | +0.1230 | 1 | 2.1234 / 2.0192 | 22.4% / 28.7% |
| all_form_plus_open_market | 0.1207 / 0.1373 | BEATS IT | 0.01 | 2.0001 / 1.8978 | 26.6% / 31.5% |
| all_form_plus_open_market @winners | 0.1283 / 0.1590 | +0.0112 | 1 | 1.9923 / 1.9026 | 27.7% / 32.2% |
| distance_aware | 0.1965 / 0.2045 | +0.0566 | 0.01 | 2.0858 / 1.9733 | 24.1% / 28.5% |
| distance_shape | 0.1954 / 0.2032 | +0.0554 | 0.01 | 2.0872 / 1.9718 | 24.5% / 28.7% |
| distance_shape_exp | 0.0197 / 0.0386 | BEATS IT | 1e-08 | 1.8872 / 1.8251 | 30.6% / 33.2% |
| speed_only | 0.3505 / 0.3908 | +0.2430 | 1 | 2.1953 / 2.1679 | 22.0% / 22.0% |
| form_plus_speed | 0.1944 / 0.2044 | +0.0566 | 0.01 | 2.0807 / 1.9726 | 23.5% / 28.7% |
| distance_speed | 0.1940 / 0.2044 | +0.0566 | 0.01 | 2.0809 / 1.9737 | 23.7% / 28.2% |
| everything | 0.1925 / 0.2037 | +0.0559 | 0.01 | 2.0814 / 1.9738 | 23.8% / 28.7% |
| position_only | 0.3133 / 0.3353 | +0.1874 | 0.01 | 2.1770 / 2.1182 | 22.0% / 22.5% |
| form_plus_position | 0.1908 / 0.1996 | +0.0517 | 1 | 2.0793 / 1.9680 | 24.7% / 28.0% |
| position_and_style | 0.1901 / 0.1999 | +0.0521 | 1 | 2.0810 / 1.9699 | 24.8% / 28.5% |
| the_lot | 0.1887 / 0.2002 | +0.0524 | 1 | 2.0780 / 1.9696 | 24.6% / 29.5% |
| market_plus_class | 0.1204 / 0.1379 | BEATS IT | 1 | 2.0012 / 1.8970 | 26.8% / 32.0% |
| market_plus_distance | 0.1203 / 0.1378 | BEATS IT | 1 | 2.0011 / 1.8975 | 27.0% / 32.0% |
| market_plus_speed | 0.1201 / 0.1383 | BEATS IT | 1 | 1.9998 / 1.8963 | 27.4% / 31.8% |
| market_plus_position | 0.1203 / 0.1378 | BEATS IT | 1 | 2.0013 / 1.8966 | 26.7% / 32.0% |
| market_plus_everything | 0.1199 / 0.1380 | BEATS IT | 1 | 2.0000 / 1.8962 | 27.1% / 32.0% |
| market_the_lot | 0.1198 / 0.1381 | BEATS IT | 1 | 2.0008 / 1.8953 | 27.1% / 32.0% |
| market_shaped | 0.1196 / 0.1383 | BEATS IT | 1e-08 | 2.0013 / 1.9001 | 26.8% / 31.5% |
| market_shaped_all | 0.1191 / 0.1383 | BEATS IT | 0.01 | 2.0003 / 1.8985 | 27.0% / 31.8% |
| extras_only | 0.3074 / 0.3309 | +0.1830 | 0.01 | 2.1871 / 2.1330 | 18.0% / 21.5% |
| form_plus_extras | 0.1744 / 0.1821 | +0.0343 | 1 | 2.0605 / 1.9486 | 24.1% / 30.0% |
| kitchen_sink | 0.1675 / 0.1783 | +0.0305 | 1 | 2.0544 / 1.9456 | 25.4% / 30.5% |
| market_kitchen_sink **(deployed)** | 0.1121 / 0.1319 | BEATS IT | 1 | 1.9919 / 1.8906 | 28.1% / 32.0% |
| market_kitchen_sink @winners | 0.1346 / 0.1795 | +0.0316 | 1 | 1.9686 / 1.9226 | 29.0% / 32.8% |
| projection_sim | 0.3281 / 0.3347 | +0.1869 | - | 2.1831 / 2.1137 | 23.4% / 27.8% |

Deployed: **market_kitchen_sink**, the model closest to BSP out of sample, refitted on all 1330 races. It BEATS the morning market. The morning price is a legitimate input: we bet into it, so using it and landing closer to BSP than it does is exactly what beating the market means. EXP is the one thing barred, because Form King derives it from the market without saying which one and it scores like a figure that already knows the close. '@winners' marks a model fitted to the actual result rather than to the closing price.

## Coefficients of the deployed model

- neural_rel: +0.1980
- last_rel: +0.0184
- peak_rel: +0.0017
- peak12_rel: +0.0146
- wfa_rel: -0.0200
- wfa_best_rel: -0.0686
- ohr_rel: -0.0014
- dist_rel: +0.0213
- dist_win: -0.0065
- last_vs_lws: +0.0184
- best_vs_lws: +0.0657
- trend_slope: -0.0031
- starts_log: -0.0189
- last_dist_rel: -0.0042
- best_dist_rel: +0.0028
- dist_change: +0.0011
- speed_rel: +0.0016
- speed_best_rel: -0.0006
- finish_speed_rel: +0.0071
- last600_rel: -0.0062
- to600_rel: +0.0016
- settle_share: -0.0295
- pos800_share: -0.1212
- pos_gain: -0.0930
- late_gain: +0.2283
- early_pos: +0.0318
- early_x_tempo: -0.0484
- style_x_tempo: +0.0386
- map_vs_habit: -0.0492
- barrier_share: +0.0372
- days_log: -0.0610
- run_in_prep: -0.0032
- weight_rel: +0.0120
- wfa_diff: +0.0544
- beaten_3: -0.0017
- prize_log: -0.0197
- track_win: +0.2284
- going_win: +0.4835
- class_win: -0.0000
- td_win: +0.2323
- wet_win: +0.0000
- up_win: +0.0223
- jockey_win: +0.0287
- trainer_win: +0.0093
- jt_combo_win: +0.0000
- open_logit: +0.7982
- market_prob: -0.2054
- market_x_neural: -0.0764

projection_sim parameters on the training races: recent_runs 4, decay 0.7, scope_bonus 0.0, trend_weight 0.0, shape_weight 0.0, late_weight 0.5, sd_floor 3.0, light_sd 1.5, sd_scale 3.0, unrated_gap 7.0, unrated_sd 3.0, neural_weight 15.0

Runners with no rated run (projected at the field mean less the unrated gap): 935 of 13610.

Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the open_logit = the log of the opening-market chance and market_prob the chance itself, carried together so the fit can bend the market's own curve (short prices are historically underbet and long ones overbet, and log-chance alone cannot correct that); market_x_neural = the market read against Neural. The move from the open to the price NOW is deliberately absent: a race pulled after it ran carries its FINAL price, so it would be reading the answer. career peak and the 12-month peak; speed_rel, speed_best_rel = points below the race's best of Form King's speed figure (100 = class par) read over the last 4 races newest-weighted, and of the best one; finish_speed_rel = the same over finishing speed (last 600 as a share of the run to the 600); last600_rel, to600_rel = the last 600m and the run to it against the class standard, in lengths; settle_share, pos800_share = where the horse settles and where it sits with 800m to run, as a share of its own field (0 = on the lead, 1 = last) read over its recent races and centred on today's field; pos_gain, late_gain = positions made up from settling and from the 400m to the post, on the same share; style_x_tempo = that settling share against the expected tempo, so a backmarker in a slow-run race reads negative; map_vs_habit = how far today's speedmap asks the horse to race from where it usually does; wfa_rel, wfa_best_rel = points below the best of the latest and the best WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean rating of runs within 200m of today's trip; dist_win = the record at the distance as a shrunk win rate, against the race mean; last_vs_lws, best_vs_lws = the latest and the best rated run against the race's Likely Winning Standard (class); trend_slope = rating points per run over the last six runs; starts_log = log of career starts against the race mean (scope); open_logit = log of the opening-market chance (comparison only, never deployed, so Value keeps meaning disagreement with the market).

## Calibration of the deployed model

| rated chance | runners | mean rated | share that won |
|---|---|---|---|
| 0% to 5% | 5107 | 2.6% | 2.7% |
| 5% to 10% | 3559 | 7.2% | 7.2% |
| 10% to 20% | 3312 | 14.0% | 14.2% |
| 20% to 30% | 1077 | 24.1% | 23.7% |
| 30% to 50% | 466 | 37.1% | 36.7% |
| 50% to 100% | 68 | 58.0% | 64.7% |

## The plans, replayed over 1330 races the fit never saw

Five blocks by date, each priced by a model fitted on the other four. Every bet is chosen against the MORNING market and struck at the morning price. The two profit columns are the SAME bets on two settlement bases: paid at Betfair SP, which is what betting into the jump gets you, and paid at the price it was struck at, which is what taking the morning price gets you. They differ by however far the selections moved.

| plan | bets | winners | staked | at BSP: profit | return | at the struck price: profit | return |
|---|---|---|---|---|---|---|---|
| top_pick | 1330 | 385 | 1330.0 | -19.5 | -1.5% | -31.9 | -2.4% |
| value_flags | 362 | 102 | 362.0 | -39.5 | -10.9% | +76.7 | +21.2% |
| value_under_8 | 355 | 101 | 355.0 | -35.5 | -10.0% | +70.7 | +19.9% |
| top_pick_to_win_1 | 1324 | 384 | 785.5 | -101.9 | -13.0% | -149.6 | -19.0% |
| kelly_quarter | 3651 | 431 | 2389.5 | +21.9 | +0.9% | +1110.7 | +46.5% |
