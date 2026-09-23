# Back-test against Betfair SP

Fitted 2026-09-23 00:34 UTC over 386 resulted races (4024 runners), 2026-04-30 to 2026-09-22. Out of sample = fitted on the first 270 races by date, scored on the last 116.

Each model is a conditional logit fitted to minimise the cross-entropy against a target: the BSP-implied chances, or ('@winners') the actual result. 'KL to BSP' is how far it sits from Betfair SP, the sharpest price anyone gets and so the stand-in for the truth. **The bar is not zero, it is the morning market**, which sits at 0.1611 out of sample: that is the price we bet into, so a model closer to BSP than it is has beaten the market it is betting against. 'log loss' is scored on the actual winners and 'top pick won' is the share of races the model's highest-rated runner won.

| model | KL to BSP (in / out) | vs the morning market | log loss vs winners (in / out) | top pick won (in / out) |
|---|---|---|---|---|
| bsp_itself | 0.0000 / 0.0000 | - | 1.8651 / 1.7809 | 35.6% / 37.9% |
| opening_market | 0.1187 / 0.1611 | the bar | 1.9821 / 1.9337 | 31.9% / 32.8% |
| neural_only | 0.2326 / 0.2860 | +0.1249 | 2.1460 / 2.0778 | 21.1% / 25.9% |
| neural_only @winners | 0.2333 / 0.2865 | +0.1254 | 2.1454 / 2.0800 | 21.1% / 25.9% |
| ratings_only | 0.2767 / 0.3261 | +0.1649 | 2.0714 / 2.0623 | 25.2% / 30.2% |
| ratings_only @winners | 0.3754 / 0.3982 | +0.2370 | 1.9805 / 2.0690 | 27.8% / 26.7% |
| ratings_plus_distance | 0.2428 / 0.3055 | +0.1443 | 2.0281 / 2.0459 | 31.1% / 27.6% |
| ratings_plus_distance @winners | 0.3493 / 0.3859 | +0.2247 | 1.9310 / 2.0561 | 31.5% / 25.0% |
| all_form | 0.1796 / 0.2450 | +0.0838 | 1.9986 / 1.9950 | 26.3% / 27.6% |
| all_form @winners | 0.2904 / 0.3456 | +0.1845 | 1.8963 / 2.0232 | 31.1% / 26.7% |
| all_form_plus_class | 0.1713 / 0.2304 | +0.0693 | 1.9928 / 1.9857 | 26.3% / 32.8% |
| all_form_plus_class @winners | 0.2885 / 0.3394 | +0.1782 | 1.8846 / 2.0202 | 33.0% / 28.4% |
| ratings_class_distance | 0.2316 / 0.2881 | +0.1269 | 2.0201 / 2.0354 | 31.9% / 28.4% |
| ratings_class_distance @winners | 0.3442 / 0.3768 | +0.2156 | 1.9173 / 2.0509 | 32.6% / 25.0% |
| all_form_plus_open_market **(deployed)** | 0.1080 / 0.1539 | BEATS IT | 1.9400 / 1.9091 | 33.7% / 31.9% |
| all_form_plus_open_market @winners | 0.2204 / 0.2522 | +0.0910 | 1.8368 / 1.9342 | 36.3% / 31.0% |
| distance_aware | 0.1709 / 0.2302 | +0.0690 | 1.9895 / 1.9895 | 27.8% / 32.8% |
| distance_aware @winners | 0.2960 / 0.3405 | +0.1794 | 1.8741 / 2.0434 | 34.1% / 29.3% |
| distance_shape | 0.1706 / 0.2305 | +0.0693 | 1.9875 / 1.9858 | 28.1% / 31.9% |
| distance_shape @winners | 0.2986 / 0.3452 | +0.1841 | 1.8698 / 2.0350 | 33.7% / 30.2% |
| distance_shape_exp | 0.0158 / 0.0662 | BEATS IT | 1.8925 / 1.8466 | 34.4% / 33.6% |
| distance_shape_exp @winners | 0.1543 / 0.1758 | +0.0147 | 1.7649 / 1.8834 | 41.1% / 31.9% |
| speed_only | 0.3391 / 0.4588 | +0.2976 | 2.2202 / 2.2635 | 18.9% / 20.7% |
| speed_only @winners | 0.3459 / 0.4633 | +0.3021 | 2.2137 / 2.2614 | 22.6% / 20.7% |
| form_plus_speed | 0.1696 / 0.2313 | +0.0702 | 1.9946 / 1.9854 | 27.4% / 31.9% |
| form_plus_speed @winners | 0.3133 / 0.3723 | +0.2112 | 1.8605 / 2.0354 | 35.6% / 30.2% |
| distance_speed | 0.1692 / 0.2309 | +0.0697 | 1.9925 / 1.9905 | 27.0% / 32.8% |
| distance_speed @winners | 0.3198 / 0.3706 | +0.2095 | 1.8530 / 2.0494 | 34.8% / 30.2% |
| everything | 0.1688 / 0.2313 | +0.0702 | 1.9911 / 1.9864 | 27.8% / 32.8% |
| everything @winners | 0.3207 / 0.3719 | +0.2107 | 1.8506 / 2.0367 | 35.2% / 29.3% |
| position_only | 0.2986 / 0.3791 | +0.2179 | 2.1585 / 2.1668 | 24.1% / 19.8% |
| position_only @winners | 0.3110 / 0.3858 | +0.2246 | 2.1464 / 2.1728 | 23.3% / 18.1% |
| form_plus_position | 0.1672 / 0.2274 | +0.0662 | 1.9994 / 1.9832 | 28.9% / 30.2% |
| form_plus_position @winners | 0.3250 / 0.3854 | +0.2242 | 1.8555 / 2.0661 | 36.3% / 27.6% |
| position_and_style | 0.1666 / 0.2289 | +0.0677 | 1.9980 / 1.9801 | 28.1% / 29.3% |
| position_and_style @winners | 0.3343 / 0.3887 | +0.2275 | 1.8452 / 2.0477 | 35.2% / 27.6% |
| the_lot | 0.1651 / 0.2296 | +0.0685 | 1.9946 / 1.9813 | 28.5% / 31.0% |
| the_lot @winners | 0.3541 / 0.3984 | +0.2373 | 1.8251 / 2.0594 | 34.8% / 30.2% |
| projection_sim | 0.3034 / 0.3665 | +0.2053 | 2.1628 / 2.1095 | 28.9% / 30.2% |

Deployed: **all_form_plus_open_market**, the model closest to BSP out of sample, refitted on all 386 races. It BEATS the morning market. The morning price is a legitimate input: we bet into it, so using it and landing closer to BSP than it does is exactly what beating the market means. EXP is the one thing barred, because Form King derives it from the market without saying which one and it scores like a figure that already knows the close. '@winners' marks a model fitted to the actual result rather than to the closing price.

## Coefficients of the deployed model

- neural_rel: +0.4795
- last_rel: +0.0201
- peak_rel: -0.0029
- peak12_rel: +0.0136
- wfa_rel: -0.0114
- wfa_best_rel: +0.0063
- ohr_rel: -0.0031
- dist_rel: +0.0180
- dist_win: +0.3345
- open_logit: +0.8310

projection_sim parameters on the training races: recent_runs 4, decay 0.7, scope_bonus 1.0, trend_weight 0.0, shape_weight 0.0, late_weight 0.5, sd_floor 3.0, light_sd 1.5, sd_scale 4.0, unrated_gap 7.0, unrated_sd 3.0, neural_weight 20.0

Runners with no rated run (projected at the field mean less the unrated gap): 168 of 4024.

Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the career peak and the 12-month peak; speed_rel, speed_best_rel = points below the race's best of Form King's speed figure (100 = class par) read over the last 4 races newest-weighted, and of the best one; finish_speed_rel = the same over finishing speed (last 600 as a share of the run to the 600); last600_rel, to600_rel = the last 600m and the run to it against the class standard, in lengths; settle_share, pos800_share = where the horse settles and where it sits with 800m to run, as a share of its own field (0 = on the lead, 1 = last) read over its recent races and centred on today's field; pos_gain, late_gain = positions made up from settling and from the 400m to the post, on the same share; style_x_tempo = that settling share against the expected tempo, so a backmarker in a slow-run race reads negative; map_vs_habit = how far today's speedmap asks the horse to race from where it usually does; wfa_rel, wfa_best_rel = points below the best of the latest and the best WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean rating of runs within 200m of today's trip; dist_win = the record at the distance as a shrunk win rate, against the race mean; last_vs_lws, best_vs_lws = the latest and the best rated run against the race's Likely Winning Standard (class); trend_slope = rating points per run over the last six runs; starts_log = log of career starts against the race mean (scope); open_logit = log of the opening-market chance (comparison only, never deployed, so Value keeps meaning disagreement with the market).

## Calibration of the deployed model

| rated chance | runners | mean rated | share that won |
|---|---|---|---|
| 0% to 5% | 1479 | 2.8% | 2.4% |
| 5% to 10% | 1142 | 7.2% | 7.8% |
| 10% to 20% | 925 | 14.0% | 13.0% |
| 20% to 30% | 308 | 23.9% | 24.7% |
| 30% to 50% | 126 | 36.3% | 43.7% |
| 50% to 100% | 23 | 58.1% | 60.9% |

## The plans, replayed over 386 races the fit never saw

Five blocks by date, each priced by a model fitted on the other four. Every bet is chosen against the MORNING market and struck at the morning price. The two profit columns are the SAME bets on two settlement bases: paid at Betfair SP, which is what betting into the jump gets you, and paid at the price it was struck at, which is what taking the morning price gets you. They differ by however far the selections moved.

| plan | bets | winners | staked | at BSP: profit | return | at the struck price: profit | return |
|---|---|---|---|---|---|---|---|
| top_pick | 386 | 125 | 386.0 | +48.3 | +12.5% | +40.4 | +10.5% |
| value_flags | 63 | 32 | 63.0 | +28.5 | +45.3% | +37.9 | +60.1% |
| value_under_8 | 63 | 32 | 63.0 | +28.5 | +45.3% | +37.9 | +60.1% |
| top_pick_to_win_1 | 386 | 125 | 189.6 | +24.1 | +12.7% | +14.7 | +7.8% |
| kelly_quarter | 931 | 119 | 535.0 | +45.3 | +8.5% | +274.0 | +51.2% |
