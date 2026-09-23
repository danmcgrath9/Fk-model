# Back-test against Betfair SP

Fitted 2026-09-23 13:51 UTC over 3584 resulted races (35176 runners), 2025-10-08 to 2026-09-22. Out of sample = fitted on the first 2508 races by date, scored on the last 1076.

Each model is a conditional logit fitted to minimise the cross-entropy against a target: the BSP-implied chances, or ('@winners') the actual result. 'KL to BSP' is how far it sits from Betfair SP, the sharpest price anyone gets and so the stand-in for the truth. **The bar is not zero, it is the morning market**, which sits at 0.1361 out of sample: that is the price we bet into, so a model closer to BSP than it is has beaten the market it is betting against. 'log loss' is scored on the actual winners and 'top pick won' is the share of races the model's highest-rated runner won.

| model | KL to BSP (in / out) | vs the morning market | ridge | log loss vs winners (in / out) | top pick won (in / out) |
|---|---|---|---|---|---|
| bsp_itself | 0.0000 / 0.0000 | - | - | 1.7567 / 1.8181 | 34.9% / 34.3% |
| opening_market | 0.1236 / 0.1361 | the bar | - | 1.8976 / 1.9608 | 29.6% / 28.7% |
| neural_only | 0.2796 / 0.2491 | +0.1129 | 0.01 | 2.0557 / 2.1023 | 23.2% / 22.7% |
| kitchen_sink | 0.1817 / 0.1720 | +0.0359 | 1 | 1.9561 / 2.0099 | 28.0% / 27.0% |
| all_form_plus_open_market | 0.1156 / 0.1276 | BEATS IT | 1 | 1.8862 / 1.9494 | 30.5% / 28.8% |
| all_form_plus_open_market @winners | 0.1190 / 0.1491 | +0.0130 | 1 | 1.8828 / 1.9602 | 29.8% / 28.5% |
| market_plus_class | 0.1150 / 0.1276 | BEATS IT | 1 | 1.8870 / 1.9493 | 30.3% / 29.6% |
| market_plus_distance | 0.1149 / 0.1275 | BEATS IT | 1 | 1.8871 / 1.9488 | 30.1% / 29.4% |
| market_plus_speed | 0.1146 / 0.1276 | BEATS IT | 1 | 1.8863 / 1.9492 | 30.1% / 29.5% |
| market_plus_position | 0.1150 / 0.1274 | BEATS IT | 1 | 1.8870 / 1.9491 | 30.2% / 29.3% |
| market_plus_everything | 0.1143 / 0.1275 | BEATS IT | 1 | 1.8864 / 1.9485 | 29.8% / 29.5% |
| market_the_lot | 0.1142 / 0.1275 | BEATS IT | 1 | 1.8859 / 1.9488 | 29.7% / 29.6% |
| market_shaped | 0.1142 / 0.1276 | BEATS IT | 1 | 1.8851 / 1.9507 | 30.2% / 29.4% |
| market_shaped_all | 0.1134 / 0.1276 | BEATS IT | 1 | 1.8845 / 1.9499 | 29.8% / 29.6% |
| market_kitchen_sink | 0.1091 / 0.1220 | BEATS IT | 1e-08 | 1.8805 / 1.9464 | 29.9% / 30.0% |
| market_kitchen_sink @winners | 0.1170 / 0.1407 | +0.0045 | 1 | 1.8715 / 1.9558 | 30.6% / 30.1% |
| market_plus_experience | 0.1145 / 0.1266 | BEATS IT | 1 | 1.8857 / 1.9493 | 29.9% / 29.4% |
| market_kitchen_sink_exp **(deployed)** | 0.1088 / 0.1211 | BEATS IT | 1 | 1.8804 / 1.9457 | 29.7% / 30.1% |
| projection_sim | 0.3267 / 0.3273 | +0.1911 | - | 2.1012 / 2.1352 | 24.6% / 26.1% |

Deployed: **market_kitchen_sink_exp**, the model closest to BSP out of sample, refitted on all 3584 races. It BEATS the morning market. The morning price is a legitimate input: we bet into it, so using it and landing closer to BSP than it does is exactly what beating the market means. EXP is the one thing barred, because Form King derives it from the market without saying which one and it scores like a figure that already knows the close. '@winners' marks a model fitted to the actual result rather than to the closing price.

## Coefficients of the deployed model

- neural_rel: +0.0967
- last_rel: +0.0208
- peak_rel: +0.0063
- peak12_rel: +0.0128
- wfa_rel: -0.0240
- wfa_best_rel: -0.0635
- ohr_rel: -0.0003
- dist_rel: +0.0221
- dist_win: +0.0804
- last_vs_lws: +0.0208
- best_vs_lws: +0.0521
- trend_slope: -0.0057
- starts_log: -0.0197
- last_dist_rel: -0.0029
- best_dist_rel: +0.0059
- dist_change: +0.0014
- speed_rel: +0.0044
- speed_best_rel: -0.0009
- finish_speed_rel: +0.0103
- last600_rel: -0.0049
- to600_rel: +0.0023
- settle_share: -0.0149
- pos800_share: -0.2012
- pos_gain: -0.1065
- late_gain: +0.1865
- early_pos: +0.1202
- early_x_tempo: -0.0439
- style_x_tempo: +0.0444
- map_vs_habit: -0.1464
- barrier_share: -0.0487
- days_log: -0.0474
- run_in_prep: -0.0048
- weight_rel: +0.0072
- wfa_diff: +0.0572
- beaten_3: -0.0007
- prize_log: -0.0222
- track_win: +0.3065
- going_win: +0.3992
- class_win: +0.0000
- td_win: +0.1555
- wet_win: +0.0000
- up_win: +0.0612
- jockey_win: +0.0244
- trainer_win: +0.0077
- jt_combo_win: +0.0000
- open_logit: +0.8945
- market_prob: -0.4412
- market_x_neural: -0.0611
- first_starter: +0.3764
- unrated: -0.0601
- trial_margin: -0.0093
- trialled_recently: +0.0223
- first_starter_x_market: +0.2001

projection_sim parameters on the training races: recent_runs 4, decay 0.7, scope_bonus 2.0, trend_weight 0.0, shape_weight 0.0, late_weight 0.5, sd_floor 3.0, light_sd 1.5, sd_scale 3.0, unrated_gap 7.0, unrated_sd 3.0, neural_weight 15.0

Runners with no rated run (projected at the field mean less the unrated gap): 2525 of 35176.

Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the open_logit = the log of the opening-market chance and market_prob the chance itself, carried together so the fit can bend the market's own curve (short prices are historically underbet and long ones overbet, and log-chance alone cannot correct that); market_x_neural = the market read against Neural. The move from the open to the price NOW is deliberately absent: a race pulled after it ran carries its FINAL price, so it would be reading the answer. career peak and the 12-month peak; speed_rel, speed_best_rel = points below the race's best of Form King's speed figure (100 = class par) read over the last 4 races newest-weighted, and of the best one; finish_speed_rel = the same over finishing speed (last 600 as a share of the run to the 600); last600_rel, to600_rel = the last 600m and the run to it against the class standard, in lengths; settle_share, pos800_share = where the horse settles and where it sits with 800m to run, as a share of its own field (0 = on the lead, 1 = last) read over its recent races and centred on today's field; pos_gain, late_gain = positions made up from settling and from the 400m to the post, on the same share; style_x_tempo = that settling share against the expected tempo, so a backmarker in a slow-run race reads negative; map_vs_habit = how far today's speedmap asks the horse to race from where it usually does; wfa_rel, wfa_best_rel = points below the best of the latest and the best WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean rating of runs within 200m of today's trip; dist_win = the record at the distance as a shrunk win rate, against the race mean; last_vs_lws, best_vs_lws = the latest and the best rated run against the race's Likely Winning Standard (class); trend_slope = rating points per run over the last six runs; starts_log = log of career starts against the race mean (scope); open_logit = log of the opening-market chance (comparison only, never deployed, so Value keeps meaning disagreement with the market).

## Calibration of the deployed model

| rated chance | runners | mean rated | share that won |
|---|---|---|---|
| 0% to 5% | 12986 | 2.5% | 2.4% |
| 5% to 10% | 8816 | 7.3% | 7.2% |
| 10% to 20% | 8610 | 14.2% | 14.6% |
| 20% to 30% | 3093 | 24.2% | 24.6% |
| 30% to 50% | 1458 | 36.7% | 35.2% |
| 50% to 100% | 192 | 57.5% | 59.9% |

## The plans, replayed over 3584 races the fit never saw

Five blocks by date, each priced by a model fitted on the other four. Every bet is chosen against the OPENING market. The two profit columns are the SAME bets on two settlement bases: paid at Betfair SP, which is what betting into the jump gets you, and paid at Form King's AVERAGE OPENING price (avgOpen).

**Read the opening-price column as an upper bound, not a result.** avgOpen is an average of the first prices bookmakers put up, which nobody can take as a single bet, and it is the one price history holds. The live paper book bets at the price on the page when the morning run happens, which is later and sharper than the open, and there the value selections have drifted and lost (see the paper book). Profit is judged at Betfair SP here and at the struck price in the live book; this column only shows how much the open itself was beatable.

| plan | bets | winners | staked | at BSP: profit | return | at the average opening price: profit | return |
|---|---|---|---|---|---|---|---|
| top_pick | 3584 | 1069 | 3584.0 | -25.0 | -0.7% | -88.0 | -2.5% |
| value_flags | 879 | 287 | 879.0 | -18.5 | -2.1% | +196.7 | +22.4% |
| value_under_8 | 873 | 287 | 873.0 | -12.5 | -1.4% | +202.7 | +23.2% |
| top_pick_to_win_1 | 3575 | 1067 | 2185.2 | +656.8 | +30.1% | -337.4 | -15.4% |
| kelly_quarter | 8109 | 1134 | 5855.0 | +27.3 | +0.5% | +2776.4 | +47.4% |
| value_ev20 | 3267 | 501 | 3267.0 | +81.1 | +2.5% | +2159.8 | +66.1% |
| value_ev05 | 6422 | 904 | 6422.0 | -310.1 | -4.8% | +2106.9 | +32.8% |
| value_ev10 | 5150 | 751 | 5150.0 | -62.5 | -1.2% | +2277.0 | +44.2% |
| value_tiered | 6422 | 904 | 14839.0 | -291.5 | -2.0% | +6543.6 | +44.1% |
| value_ev20_kelly | 3267 | 501 | 4324.5 | +50.7 | +1.2% | +2607.3 | +60.3% |

## Choosing the value rule: value_flags

gap = our chance beats the opening market's by more than the threshold in percentage points (the live rule is gap 0.05). ev = our chance times the average opening price is more than 1 plus the threshold. Each rule is picked on the OLDER 3 fifths of the racing by its return at Betfair SP (at least 30 bets), then shown on the NEWER two fifths it never saw. Returns are one unit a bet, before commission.

| rule | threshold | older: bets | at BSP | at avg opening price | newer: bets | at BSP | at avg opening price |
|---|---|---|---|---|---|---|---|
| gap | 0.02 | 2457 | +0.9% | +19.5% | 1580 | -11.3% | +5.3% |
| gap | 0.03 | 1441 | +3.4% | +21.3% | 948 | -9.4% | +12.8% |
| gap (live) | 0.05 | 500 | -1.4% | +23.3% | 375 | -2.6% | +22.2% |
| gap **(chosen)** | 0.08 | 128 | +20.9% | +48.4% | 115 | -3.9% | +11.2% |
| gap | 0.10 | 50 | -5.7% | +22.7% | 61 | +3.2% | +8.1% |
| ev | 0.05 | 3924 | -4.8% | +30.3% | 2502 | -5.0% | +36.5% |
| ev | 0.10 | 3143 | -3.4% | +39.5% | 2011 | +2.0% | +51.3% |
| ev | 0.20 | 1962 | -3.5% | +58.8% | 1309 | +11.2% | +76.6% |
| ev | 0.30 | 1287 | -3.0% | +70.9% | 864 | +12.7% | +77.4% |
| ev | 0.50 | 623 | -10.1% | +93.3% | 401 | +24.6% | +108.5% |

## Choosing the value rule: value_under_8

gap = our chance beats the opening market's by more than the threshold in percentage points (the live rule is gap 0.05). ev = our chance times the average opening price is more than 1 plus the threshold. Each rule is picked on the OLDER 3 fifths of the racing by its return at Betfair SP (at least 30 bets), then shown on the NEWER two fifths it never saw. Returns are one unit a bet, before commission.

| rule | threshold | older: bets | at BSP | at avg opening price | newer: bets | at BSP | at avg opening price |
|---|---|---|---|---|---|---|---|
| gap | 0.02 | 2052 | +3.2% | +16.8% | 1370 | -9.6% | +3.8% |
| gap | 0.03 | 1348 | +2.8% | +18.6% | 902 | -7.2% | +11.5% |
| gap (live) | 0.05 | 498 | -1.0% | +23.8% | 371 | -1.6% | +23.5% |
| gap **(chosen)** | 0.08 | 128 | +20.9% | +48.4% | 115 | -3.9% | +11.2% |
| gap | 0.10 | 50 | -5.7% | +22.7% | 61 | +3.2% | +8.1% |
| ev | 0.05 | 1758 | +1.7% | +38.6% | 1128 | +0.8% | +30.7% |
| ev | 0.10 | 1406 | -4.5% | +39.7% | 941 | +6.0% | +40.8% |
| ev | 0.20 | 898 | -5.8% | +50.1% | 656 | +3.9% | +47.0% |
| ev | 0.30 | 610 | -5.2% | +60.7% | 446 | +1.5% | +54.5% |
| ev | 0.50 | 305 | +4.4% | +101.5% | 222 | +7.6% | +75.6% |

## The strategy search: where, if anywhere, the bets make money

153 strategies: each betting rule (ev = our chance x the opening price must beat 1 by the threshold; gap = our chance must beat the market's by the threshold in points) crossed with a slice of the racing (price band, field size, first starters, metro or not). Every one is scored on the OLDER three fifths of the racing and then on the NEWER two fifths it never saw. One unit a bet, before commission. '±' is one standard error: a return inside about two of them is indistinguishable from luck. With this many tried, some look good on the older racing by chance alone, so only the newer column counts.

- Profitable at Betfair SP in BOTH halves: 25 of 153
- Profitable at the average opening price in BOTH halves: 148 of 153 (upper bound: an average, not a takeable price)
- Profitable at Betfair SP on the newer racing by more than two standard errors, and profitable on the older: 0
- Profitable at the average opening price on the newer racing by more than two standard errors, and on the older: 86


### Best twelve on the older racing at Betfair SP, and how they did on the newer

| rule | slice | older: bets | at BSP | at open | newer: bets | at BSP | at open |
|---|---|---|---|---|---|---|---|
| ev 0.25 | metro | 266 | +53.3% ±36.5% | +88.3% ±38.7% | 180 | +8.2% ±23.2% | +74.2% ±41.0% |
| ev 0.20 | metro | 344 | +45.0% ±29.8% | +84.0% ±33.0% | 241 | -4.1% ±18.4% | +52.7% ±32.1% |
| ev 0.20 | first starters | 78 | +42.9% ±43.5% | +114.6% ±57.0% | 54 | -39.1% ±28.4% | -8.5% ±34.5% |
| ev 0.15 | metro | 445 | +39.0% ±27.1% | +72.7% ±28.5% | 307 | -2.5% ±16.8% | +42.5% ±26.5% |
| ev 0.35 | metro | 144 | +35.5% ±46.9% | +92.8% ±55.3% | 118 | +7.3% ±29.8% | +42.5% ±32.8% |
| ev 0.50 | metro | 73 | +31.5% ±51.7% | +120.5% ±94.6% | 45 | -35.5% ±26.7% | +18.2% ±49.5% |
| ev 0.15 | first starters | 97 | +29.8% ±35.7% | +91.8% ±46.9% | 67 | -50.9% ±23.1% | -26.3% ±28.1% |
| ev 0.50 | our top pick | 102 | +27.3% ±22.6% | +100.9% ±29.7% | 82 | +2.7% ±21.6% | +61.8% ±27.8% |
| ev 0.10 | metro | 594 | +20.2% ±20.9% | +48.3% ±22.0% | 403 | -6.2% ±14.1% | +40.2% ±22.5% |
| ev 0.05 | first starters | 152 | +18.3% ±31.5% | +52.6% ±32.6% | 95 | -26.6% ±26.3% | +5.9% ±35.8% |
| ev 0.10 | Saturdays | 623 | +17.8% ±19.2% | +43.5% ±21.2% | 268 | -6.9% ±16.4% | +49.5% ±29.8% |
| ev 0.25 | Saturdays | 276 | +17.4% ±27.8% | +67.2% ±36.5% | 119 | +6.8% ±26.8% | +84.6% ±55.2% |

### Best twelve on the older racing at the opening price, and how they did on the newer

| rule | slice | older: bets | at BSP | at open | newer: bets | at BSP | at open |
|---|---|---|---|---|---|---|---|
| ev 0.20 | field 13+ | 60 | -10.7% ±35.8% | +152.5% ±105.8% | 79 | -5.5% ±28.1% | +61.1% ±51.3% |
| ev 0.50 | field <=8 | 357 | +0.5% ±15.6% | +139.0% ±41.3% | 214 | +4.3% ±19.8% | +91.2% ±35.2% |
| ev 0.50 | metro | 73 | +31.5% ±51.7% | +120.5% ±94.6% | 45 | -35.5% ±26.7% | +18.2% ±49.5% |
| ev 0.20 | first starters | 78 | +42.9% ±43.5% | +114.6% ±57.0% | 54 | -39.1% ±28.4% | -8.5% ±34.5% |
| ev 0.50 | we rate <$5 | 170 | +14.7% ±15.5% | +111.0% ±26.1% | 131 | -11.6% ±17.3% | +34.2% ±22.0% |
| ev 0.50 | we rate $5-10 | 191 | +0.1% ±19.0% | +104.3% ±36.3% | 131 | +31.0% ±28.7% | +145.8% ±45.9% |
| ev 0.50 | price $16+ | 305 | -20.9% ±20.1% | +104.1% ±51.5% | 164 | +43.7% ±49.8% | +150.7% ±67.3% |
| ev 0.50 | our top pick | 102 | +27.3% ±22.6% | +100.9% ±29.7% | 82 | +2.7% ±21.6% | +61.8% ±27.8% |
| ev 0.35 | field <=8 | 523 | -4.7% ±13.1% | +100.6% ±29.6% | 329 | +19.7% ±18.6% | +99.0% ±31.0% |
| ev 0.50 | weekdays | 528 | -9.1% ±12.6% | +96.5% ±29.2% | 369 | +27.9% ±24.4% | +114.8% ±33.1% |
| ev 0.50 | all | 619 | -9.5% ±11.6% | +94.5% ±27.4% | 401 | +24.6% ±22.9% | +108.5% ±31.1% |
| ev 0.50 | raced horses | 590 | -10.3% ±12.0% | +93.8% ±28.4% | 384 | +28.4% ±23.9% | +113.9% ±32.4% |

### Beating the morning price, ranked by how far clear of luck on the newer racing

| rule | slice | older: bets | at open | newer: bets | at open | at BSP | standard errors clear |
|---|---|---|---|---|---|---|---|
| ev 0.20 | raced horses | 1880 | +56.8% | 1255 | +80.2% ±18.2% | +13.4% | 4.4 |
| ev 0.20 | all | 1958 | +59.1% | 1309 | +76.6% ±17.5% | +11.2% | 4.4 |
| ev 0.10 | our top pick | 496 | +33.3% | 367 | +49.9% ±11.5% | +18.1% | 4.3 |
| ev 0.15 | raced horses | 2394 | +49.6% | 1547 | +67.4% ±15.7% | +7.8% | 4.3 |
| ev 0.25 | raced horses | 1548 | +65.4% | 1022 | +87.0% ±20.3% | +17.2% | 4.3 |
| ev 0.25 | all | 1606 | +64.9% | 1070 | +83.2% ±19.5% | +15.0% | 4.3 |
| ev 0.15 | all | 2491 | +51.2% | 1614 | +63.5% ±15.1% | +5.4% | 4.2 |
| ev 0.20 | weekdays | 1605 | +58.1% | 1146 | +78.5% ±19.1% | +13.2% | 4.1 |
| ev 0.10 | raced horses | 3012 | +38.6% | 1928 | +53.4% ±13.0% | +3.6% | 4.1 |
| ev 0.10 | all | 3139 | +39.7% | 2011 | +51.3% ±12.6% | +2.0% | 4.1 |
| ev 0.20 | country and provincial | 1614 | +53.8% | 1068 | +81.9% ±20.2% | +14.7% | 4.1 |
| ev 0.25 | weekdays | 1330 | +64.4% | 951 | +83.0% ±20.8% | +16.0% | 4.0 |
| ev 0.15 | our top pick | 409 | +40.8% | 307 | +50.8% ±12.8% | +13.1% | 4.0 |
| ev 0.25 | we rate $5-10 | 498 | +68.6% | 316 | +95.3% ±24.3% | +26.2% | 3.9 |
| ev 0.15 | weekdays | 2026 | +50.7% | 1412 | +64.4% ±16.5% | +6.9% | 3.9 |
| ev 0.15 | country and provincial | 2046 | +46.5% | 1307 | +68.5% ±17.6% | +7.2% | 3.9 |
| ev 0.15 | we rate $5-10 | 787 | +51.2% | 494 | +68.2% ±17.5% | +15.2% | 3.9 |
| ev 0.25 | country and provincial | 1340 | +60.3% | 890 | +85.1% ±21.9% | +16.3% | 3.9 |
| ev 0.10 | weekdays | 2516 | +38.7% | 1743 | +51.6% ±13.8% | +3.4% | 3.8 |
| ev 0.20 | we rate $5-10 | 610 | +57.2% | 397 | +75.6% ±20.4% | +16.2% | 3.7 |
