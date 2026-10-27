# Back-test against Betfair SP

Fitted 2026-10-27 12:45 UTC over 5003 resulted races (49496 runners), 2025-07-01 to 2026-10-26. Out of sample = fitted on the first 3502 races by date, scored on the last 1501.

Each model is a conditional logit fitted to minimise the cross-entropy against a target: the BSP-implied chances, or ('@winners') the actual result. 'KL to BSP' is how far it sits from Betfair SP, the sharpest price anyone gets and so the stand-in for the truth. **The bar is not zero, it is the morning market**, which sits at 0.1430 out of sample: that is the price we bet into, so a model closer to BSP than it is has beaten the market it is betting against. 'log loss' is scored on the actual winners and 'top pick won' is the share of races the model's highest-rated runner won.

| model | KL to BSP (in / out) | vs the morning market | ridge | log loss vs winners (in / out) | top pick won (in / out) |
|---|---|---|---|---|---|
| bsp_itself | 0.0000 / 0.0000 | - | - | 1.7730 / 1.8083 | 35.0% / 34.0% |
| opening_market | 0.1203 / 0.1430 | the bar | - | 1.9009 / 1.9615 | 29.9% / 28.4% |
| neural_only | 0.2769 / 0.2628 | +0.1198 | 0.01 | 2.0552 / 2.1042 | 24.2% / 22.1% |
| kitchen_sink | 0.1815 / 0.1753 | +0.0323 | 1 | 1.9638 / 2.0062 | 27.8% / 26.9% |
| all_form_plus_open_market | 0.1132 / 0.1335 | BEATS IT | 1 | 1.8916 / 1.9511 | 30.6% / 29.0% |
| all_form_plus_open_market @winners | 0.1139 / 0.1336 | BEATS IT | 1 | 1.8909 / 1.9526 | 30.2% / 29.2% |
| market_plus_class | 0.1126 / 0.1329 | BEATS IT | 1 | 1.8920 / 1.9509 | 30.5% / 29.5% |
| market_plus_distance | 0.1125 / 0.1328 | BEATS IT | 1 | 1.8920 / 1.9508 | 30.6% / 29.5% |
| market_plus_speed | 0.1123 / 0.1329 | BEATS IT | 1 | 1.8919 / 1.9506 | 30.3% / 29.4% |
| market_plus_position | 0.1124 / 0.1327 | BEATS IT | 1 | 1.8922 / 1.9506 | 30.5% / 29.3% |
| market_plus_everything | 0.1120 / 0.1326 | BEATS IT | 1 | 1.8921 / 1.9500 | 30.2% / 29.6% |
| market_the_lot | 0.1120 / 0.1326 | BEATS IT | 1 | 1.8917 / 1.9501 | 30.1% / 29.4% |
| market_shaped | 0.1119 / 0.1330 | BEATS IT | 1 | 1.8910 / 1.9516 | 30.2% / 29.4% |
| market_shaped_all | 0.1114 / 0.1326 | BEATS IT | 1 | 1.8910 / 1.9506 | 30.1% / 29.4% |
| market_kitchen_sink | 0.1073 / 0.1258 | BEATS IT | 1 | 1.8879 / 1.9433 | 30.1% / 30.1% |
| market_kitchen_sink @winners | 0.1126 / 0.1309 | BEATS IT | 1 | 1.8817 / 1.9501 | 30.5% / 29.2% |
| market_plus_experience | 0.1121 / 0.1320 | BEATS IT | 1 | 1.8906 / 1.9505 | 30.2% / 29.2% |
| market_kitchen_sink_exp | 0.1069 / 0.1252 | BEATS IT | 1 | 1.8869 / 1.9432 | 30.2% / 30.0% |
| memory_plus_market | 0.1156 / 0.1379 | BEATS IT | 1 | 1.8948 / 1.9597 | 30.4% / 28.8% |
| market_plus_memory | 0.1105 / 0.1298 | BEATS IT | 1 | 1.8893 / 1.9487 | 30.5% / 29.5% |
| market_kitchen_sink_memory | 0.1055 / 0.1233 | BEATS IT | 1 | 1.8857 / 1.9415 | 29.8% / 29.3% |
| market_kitchen_sink_memory_intent **(deployed)** | 0.1042 / 0.1226 | BEATS IT | 1 | 1.8835 / 1.9425 | 30.4% / 29.0% |
| projection_sim | 0.3271 / 0.3321 | +0.1891 | - | 2.1025 / 2.1442 | 24.9% / 25.0% |

Deployed: **market_kitchen_sink_memory_intent**, the model closest to BSP out of sample, refitted on all 5003 races. It BEATS the morning market. The morning price is a legitimate input: we bet into it, so using it and landing closer to BSP than it does is exactly what beating the market means. EXP is the one thing barred, because Form King derives it from the market without saying which one and it scores like a figure that already knows the close. '@winners' marks a model fitted to the actual result rather than to the closing price.

## Coefficients of the deployed model

- neural_rel: +0.1165
- last_rel: +0.0284
- peak_rel: -0.0078
- peak12_rel: +0.0109
- wfa_rel: -0.0386
- wfa_best_rel: -0.0403
- ohr_rel: +0.0006
- dist_rel: +0.0191
- dist_win: +0.1994
- last_vs_lws: +0.0284
- best_vs_lws: +0.0442
- trend_slope: +0.0008
- starts_log: -0.0373
- last_dist_rel: -0.0012
- best_dist_rel: +0.0059
- dist_change: +0.0030
- speed_rel: +0.0034
- speed_best_rel: +0.0002
- finish_speed_rel: +0.0079
- last600_rel: -0.0039
- to600_rel: +0.0016
- settle_share: +0.0146
- pos800_share: -0.2160
- pos_gain: -0.1473
- late_gain: +0.2068
- early_pos: +0.1244
- early_x_tempo: -0.0377
- style_x_tempo: +0.0202
- map_vs_habit: -0.1561
- barrier_share: -0.0694
- days_log: -0.0384
- run_in_prep: -0.0047
- weight_rel: -0.0084
- wfa_diff: +0.0520
- beaten_3: +0.0002
- prize_log: -0.0059
- track_win: +0.3506
- going_win: +0.4702
- class_win: -0.0000
- td_win: +0.1649
- wet_win: +0.2171
- up_win: +0.1430
- jockey_win: +0.0221
- trainer_win: +0.0075
- jt_combo_win: +0.0000
- open_logit: +0.8591
- market_prob: -0.4741
- market_x_neural: -0.0505
- first_starter: +0.4552
- unrated: +0.0454
- trial_margin: -0.0076
- trialled_recently: +0.0141
- first_starter_x_market: +0.2452
- mkt_class: +0.0549
- beat_market: -0.2424
- beat_market_last: +0.0350
- field_strength: +0.0023
- strength_last: +0.0008
- trainer_only: +0.0177
- jockey_only: -0.0199
- apprentice_claim: -0.0573
- days_since_win_log: +0.0120
- dual_acceptor: +0.0120
- emergency: +0.1342

projection_sim parameters on the training races: recent_runs 4, decay 0.7, scope_bonus 2.0, trend_weight 0.0, shape_weight 0.0, late_weight 0.5, sd_floor 3.0, light_sd 1.5, sd_scale 3.0, unrated_gap 7.0, unrated_sd 3.0, neural_weight 15.0

Runners with no rated run (projected at the field mean less the unrated gap): 3497 of 49496.

Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the open_logit = the log of the opening-market chance and market_prob the chance itself, carried together so the fit can bend the market's own curve (short prices are historically underbet and long ones overbet, and log-chance alone cannot correct that); market_x_neural = the market read against Neural. The move from the open to the price NOW is deliberately absent: a race pulled after it ran carries its FINAL price, so it would be reading the answer. career peak and the 12-month peak; speed_rel, speed_best_rel = points below the race's best of Form King's speed figure (100 = class par) read over the last 4 races newest-weighted, and of the best one; finish_speed_rel = the same over finishing speed (last 600 as a share of the run to the 600); last600_rel, to600_rel = the last 600m and the run to it against the class standard, in lengths; settle_share, pos800_share = where the horse settles and where it sits with 800m to run, as a share of its own field (0 = on the lead, 1 = last) read over its recent races and centred on today's field; pos_gain, late_gain = positions made up from settling and from the 400m to the post, on the same share; style_x_tempo = that settling share against the expected tempo, so a backmarker in a slow-run race reads negative; map_vs_habit = how far today's speedmap asks the horse to race from where it usually does; wfa_rel, wfa_best_rel = points below the best of the latest and the best WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean rating of runs within 200m of today's trip; dist_win = the record at the distance as a shrunk win rate, against the race mean; last_vs_lws, best_vs_lws = the latest and the best rated run against the race's Likely Winning Standard (class); trend_slope = rating points per run over the last six runs; starts_log = log of career starts against the race mean (scope); open_logit = log of the opening-market chance (comparison only, never deployed, so Value keeps meaning disagreement with the market).

## Calibration of the deployed model

| rated chance | runners | mean rated | share that won |
|---|---|---|---|
| 0% to 5% | 18500 | 2.5% | 2.4% |
| 5% to 10% | 12368 | 7.3% | 7.2% |
| 10% to 20% | 11989 | 14.1% | 14.5% |
| 20% to 30% | 4271 | 24.2% | 24.4% |
| 30% to 50% | 2056 | 36.8% | 35.8% |
| 50% to 100% | 269 | 57.8% | 59.1% |

## The plans, replayed over 5003 races the fit never saw

Five blocks by date, each priced by a model fitted on the other four. Every bet is chosen against the OPENING market. The two profit columns are the SAME bets on two settlement bases: paid at Betfair SP, which is what betting into the jump gets you, and paid at Form King's AVERAGE OPENING price (avgOpen).

**Read the opening-price column as an upper bound, not a result.** avgOpen is an average of the first prices bookmakers put up, which nobody can take as a single bet, and it is the one price history holds. The live paper book bets at the price on the page when the morning run happens, which is later and sharper than the open, and there the value selections have drifted and lost (see the paper book). Profit is judged at Betfair SP here and at the struck price in the live book; this column only shows how much the open itself was beatable.

| plan | bets | winners | staked | at BSP: profit | return | at the average opening price: profit | return |
|---|---|---|---|---|---|---|---|
| top_pick | 5003 | 1497 | 5003.0 | -33.2 | -0.7% | -71.7 | -1.4% |
| value_flags | 1510 | 477 | 1510.0 | -10.9 | -0.7% | +319.2 | +21.1% |
| value_under_8 | 1497 | 476 | 1497.0 | -13.4 | -0.9% | +320.2 | +21.4% |
| top_pick_to_win_1 | 4986 | 1492 | 3005.5 | +557.5 | +18.5% | -464.8 | -15.5% |
| kelly_quarter | 11336 | 1635 | 8519.0 | +9.0 | +0.1% | +3894.8 | +45.7% |
| value_ev20 | 4688 | 723 | 4688.0 | +149.8 | +3.2% | +2919.3 | +62.3% |
| value_ev05 | 9102 | 1344 | 9102.0 | +10.6 | +0.1% | +3368.4 | +37.0% |
| value_ev10 | 7296 | 1090 | 7296.0 | +189.8 | +2.6% | +3375.4 | +46.3% |
| value_tiered | 9102 | 1344 | 21086.0 | +350.2 | +1.7% | +9663.1 | +45.8% |
| value_ev20_kelly | 4688 | 723 | 6238.6 | +31.1 | +0.5% | +3658.4 | +58.6% |

## Choosing the value rule: value_flags

gap = our chance beats the opening market's by more than the threshold in percentage points (the live rule is gap 0.05). ev = our chance times the average opening price is more than 1 plus the threshold. Each rule is picked on the OLDER 3 fifths of the racing by its return at Betfair SP (at least 30 bets), then shown on the NEWER two fifths it never saw. Returns are one unit a bet, before commission.

| rule | threshold | older: bets | at BSP | at avg opening price | newer: bets | at BSP | at avg opening price |
|---|---|---|---|---|---|---|---|
| gap | 0.02 | 3766 | +0.7% | +16.3% | 2369 | -6.7% | +13.4% |
| gap | 0.03 | 2288 | -0.3% | +20.6% | 1432 | -5.3% | +19.5% |
| gap (live) | 0.05 | 910 | -0.1% | +20.7% | 593 | -2.5% | +22.5% |
| gap | 0.08 | 240 | -3.2% | +19.9% | 180 | -12.0% | +8.2% |
| gap | 0.10 | 97 | -1.1% | +6.9% | 79 | +1.1% | +8.3% |
| ev | 0.05 | 5859 | -1.8% | +32.5% | 3728 | +6.0% | +41.2% |
| ev | 0.10 | 4661 | +1.4% | +42.3% | 3029 | +10.7% | +51.6% |
| ev | 0.20 | 2968 | -8.2% | +50.6% | 1958 | +18.9% | +77.2% |
| ev | 0.30 | 1913 | -2.0% | +68.8% | 1286 | +19.8% | +90.0% |
| ev **(chosen)** | 0.50 | 857 | +5.3% | +104.9% | 610 | +9.3% | +90.1% |

## Choosing the value rule: value_under_8

gap = our chance beats the opening market's by more than the threshold in percentage points (the live rule is gap 0.05). ev = our chance times the average opening price is more than 1 plus the threshold. Each rule is picked on the OLDER 3 fifths of the racing by its return at Betfair SP (at least 30 bets), then shown on the NEWER two fifths it never saw. Returns are one unit a bet, before commission.

| rule | threshold | older: bets | at BSP | at avg opening price | newer: bets | at BSP | at avg opening price |
|---|---|---|---|---|---|---|---|
| gap **(chosen)** | 0.02 | 3110 | +4.1% | +16.0% | 1977 | -4.5% | +11.1% |
| gap | 0.03 | 2124 | +0.2% | +18.5% | 1339 | -5.2% | +15.1% |
| gap (live) | 0.05 | 903 | -1.0% | +20.3% | 586 | -1.3% | +24.0% |
| gap | 0.08 | 240 | -3.2% | +19.9% | 180 | -12.0% | +8.2% |
| gap | 0.10 | 97 | -1.1% | +6.9% | 79 | +1.1% | +8.3% |
| ev | 0.05 | 2562 | +1.6% | +34.2% | 1650 | -2.2% | +31.5% |
| ev | 0.10 | 2063 | -1.6% | +37.4% | 1377 | -3.9% | +33.9% |
| ev | 0.20 | 1329 | -5.6% | +42.5% | 915 | -3.0% | +47.4% |
| ev | 0.30 | 875 | -7.5% | +51.4% | 639 | -8.2% | +49.3% |
| ev | 0.50 | 419 | -5.8% | +77.8% | 313 | -10.3% | +66.5% |

## The strategy search: where, if anywhere, the bets make money

161 strategies: each betting rule (ev = our chance x the opening price must beat 1 by the threshold; gap = our chance must beat the market's by the threshold in points) crossed with a slice of the racing (price band, field size, first starters, metro or not). Every one is scored on the OLDER three fifths of the racing and then on the NEWER two fifths it never saw. One unit a bet, before commission. '±' is one standard error: a return inside about two of them is indistinguishable from luck. With this many tried, some look good on the older racing by chance alone, so only the newer column counts.

- Profitable at Betfair SP in BOTH halves: 50 of 161
- Profitable at the average opening price in BOTH halves: 151 of 161 (upper bound: an average, not a takeable price)
- Profitable at Betfair SP on the newer racing by more than two standard errors, and profitable on the older: 0
- Profitable at the average opening price on the newer racing by more than two standard errors, and on the older: 116


### Best twelve on the older racing at Betfair SP, and how they did on the newer

| rule | slice | older: bets | at BSP | at open | newer: bets | at BSP | at open |
|---|---|---|---|---|---|---|---|
| gap 0.05 | price $8-16 | 84 | +58.8% ±40.2% | +100.9% ±42.9% | 44 | -39.5% ±24.1% | +28.4% ±49.8% |
| ev 0.35 | metro | 234 | +43.4% ±29.9% | +117.9% ±44.7% | 162 | +44.9% ±41.9% | +97.0% ±46.8% |
| ev 0.20 | first starters | 125 | +32.5% ±32.6% | +90.8% ±41.8% | 72 | -23.1% ±24.5% | +18.8% ±32.3% |
| ev 0.50 | our top pick | 149 | +20.4% ±17.3% | +100.3% ±24.7% | 122 | -1.3% ±16.5% | +55.3% ±21.4% |
| ev 0.25 | metro | 392 | +18.4% ±19.5% | +78.3% ±29.3% | 252 | +31.8% ±29.6% | +82.1% ±35.1% |
| ev 0.15 | first starters | 146 | +17.1% ±28.2% | +68.9% ±36.3% | 93 | -40.5% ±19.2% | -8.1% ±25.5% |
| ev 0.10 | field <=8 | 1527 | +15.1% ±15.4% | +66.6% ±14.7% | 966 | +9.1% ±11.8% | +69.0% ±19.4% |
| ev 0.35 | field <=8 | 668 | +13.6% ±13.6% | +108.5% ±25.4% | 436 | +14.1% ±15.7% | +112.0% ±34.9% |
| gap 0.05 | we rate $5-10 | 135 | +13.4% ±25.6% | +27.8% ±26.3% | 64 | +4.5% ±25.9% | +93.0% ±49.7% |
| ev 0.35 | we rate $10+ | 672 | +13.0% ±18.7% | +99.0% ±32.0% | 421 | +48.0% ±31.0% | +151.3% ±48.7% |
| ev 0.25 | field <=8 | 934 | +12.4% ±11.3% | +92.0% ±19.7% | 606 | +5.3% ±12.5% | +86.2% ±26.9% |
| ev 0.05 | field <=8 | 1829 | +12.3% ±13.1% | +55.8% ±12.6% | 1117 | +8.7% ±11.5% | +57.0% ±17.0% |

### Best twelve on the older racing at the opening price, and how they did on the newer

| rule | slice | older: bets | at BSP | at open | newer: bets | at BSP | at open |
|---|---|---|---|---|---|---|---|
| ev 0.50 | field <=8 | 422 | +10.8% ±16.4% | +139.5% ±36.8% | 290 | +14.2% ±20.4% | +102.2% ±35.7% |
| ev 0.50 | price $16+ | 408 | +8.4% ±21.5% | +134.4% ±44.4% | 264 | +29.1% ±35.6% | +122.8% ±51.5% |
| ev 0.50 | we rate $10+ | 351 | +8.6% ±24.3% | +119.2% ±49.2% | 225 | +36.7% ±41.2% | +113.4% ±57.6% |
| ev 0.35 | metro | 234 | +43.4% ±29.9% | +117.9% ±44.7% | 162 | +44.9% ±41.9% | +97.0% ±46.8% |
| ev 0.50 | weekdays | 722 | +10.7% ±13.3% | +115.4% ±25.2% | 560 | +11.5% ±18.3% | +94.0% ±26.7% |
| ev 0.50 | we rate <$5 | 222 | +12.0% ±13.0% | +111.7% ±22.6% | 189 | -20.1% ±12.9% | +28.4% ±17.4% |
| ev 0.35 | price $16+ | 690 | +9.8% ±17.9% | +110.1% ±31.8% | 437 | +41.1% ±29.7% | +153.1% ±47.5% |
| ev 0.50 | raced horses | 811 | +7.3% ±12.3% | +108.8% ±24.0% | 584 | +11.0% ±17.8% | +93.9% ±25.9% |
| ev 0.35 | field <=8 | 668 | +13.6% ±13.6% | +108.5% ±25.4% | 436 | +14.1% ±15.7% | +112.0% ±34.9% |
| ev 0.50 | country and provincial | 751 | +5.1% ±12.5% | +106.6% ±24.4% | 527 | +12.1% ±18.9% | +101.8% ±28.3% |
| ev 0.50 | all | 852 | +5.9% ±11.8% | +106.1% ±23.1% | 609 | +9.4% ±17.1% | +90.4% ±24.9% |
| ev 0.50 | metro | 101 | +11.4% ±35.6% | +103.1% ±70.2% | 82 | -7.6% ±37.2% | +16.9% ±35.8% |

### Beating the morning price, ranked by how far clear of luck on the newer racing

| rule | slice | older: bets | at open | newer: bets | at open | at BSP | standard errors clear |
|---|---|---|---|---|---|---|---|
| ev 0.20 | all | 2963 | +50.9% | 1957 | +77.3% ±14.5% | +19.0% | 5.3 |
| ev 0.20 | raced horses | 2838 | +49.1% | 1885 | +79.6% ±15.0% | +20.6% | 5.3 |
| ev 0.15 | raced horses | 3541 | +48.9% | 2359 | +65.0% ±12.4% | +16.6% | 5.2 |
| ev 0.15 | all | 3687 | +49.7% | 2452 | +62.2% ±12.0% | +14.4% | 5.2 |
| ev 0.10 | all | 4656 | +42.4% | 3028 | +51.6% ±10.1% | +10.7% | 5.1 |
| ev 0.10 | raced horses | 4468 | +42.2% | 2917 | +52.9% ±10.4% | +11.8% | 5.1 |
| ev 0.20 | weekdays | 2439 | +52.3% | 1742 | +75.6% ±15.6% | +17.7% | 4.8 |
| ev 0.05 | all | 5854 | +32.6% | 3727 | +41.2% ±8.5% | +6.0% | 4.8 |
| ev 0.05 | raced horses | 5614 | +32.8% | 3593 | +42.2% ±8.8% | +6.9% | 4.8 |
| ev 0.20 | country and provincial | 2432 | +50.3% | 1640 | +77.7% ±16.3% | +15.8% | 4.8 |
| ev 0.25 | all | 2389 | +60.4% | 1580 | +78.4% ±16.5% | +20.2% | 4.8 |
| ev 0.25 | raced horses | 2291 | +59.8% | 1517 | +81.1% ±17.1% | +22.1% | 4.7 |
| ev 0.10 | weekdays | 3755 | +45.7% | 2636 | +52.1% ±11.0% | +11.4% | 4.7 |
| ev 0.15 | weekdays | 3022 | +50.5% | 2154 | +60.2% ±13.0% | +13.6% | 4.6 |
| ev 0.35 | raced horses | 1477 | +81.3% | 1003 | +102.3% ±22.3% | +18.7% | 4.6 |
| ev 0.15 | country and provincial | 2986 | +50.3% | 2028 | +61.7% ±13.5% | +11.3% | 4.6 |
| ev 0.35 | all | 1545 | +80.9% | 1048 | +97.5% ±21.4% | +15.9% | 4.5 |
| ev 0.10 | country and provincial | 3730 | +45.0% | 2489 | +51.5% ±11.5% | +8.3% | 4.5 |
| ev 0.05 | country and provincial | 4615 | +35.7% | 3020 | +43.0% ±9.7% | +5.4% | 4.4 |
| ev 0.05 | weekdays | 4668 | +37.3% | 3208 | +40.6% ±9.3% | +5.0% | 4.4 |
