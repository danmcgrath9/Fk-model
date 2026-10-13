# Back-test against Betfair SP

Fitted 2026-10-13 04:58 UTC over 3720 resulted races (36541 runners), 2025-10-08 to 2026-10-09. Out of sample = fitted on the first 2604 races by date, scored on the last 1116.

Each model is a conditional logit fitted to minimise the cross-entropy against a target: the BSP-implied chances, or ('@winners') the actual result. 'KL to BSP' is how far it sits from Betfair SP, the sharpest price anyone gets and so the stand-in for the truth. **The bar is not zero, it is the morning market**, which sits at 0.1420 out of sample: that is the price we bet into, so a model closer to BSP than it is has beaten the market it is betting against. 'log loss' is scored on the actual winners and 'top pick won' is the share of races the model's highest-rated runner won.

| model | KL to BSP (in / out) | vs the morning market | ridge | log loss vs winners (in / out) | top pick won (in / out) |
|---|---|---|---|---|---|
| bsp_itself | 0.0000 / 0.0000 | - | - | 1.7584 / 1.8005 | 34.9% / 35.3% |
| opening_market | 0.1238 / 0.1420 | the bar | - | 1.8983 / 1.9570 | 29.5% / 28.7% |
| neural_only | 0.2776 / 0.2569 | +0.1149 | 0.01 | 2.0556 / 2.1017 | 23.2% / 23.1% |
| kitchen_sink | 0.1805 / 0.1744 | +0.0325 | 1 | 1.9564 / 2.0015 | 28.0% / 27.4% |
| all_form_plus_open_market | 0.1156 / 0.1325 | BEATS IT | 1 | 1.8865 / 1.9454 | 30.3% / 29.7% |
| all_form_plus_open_market @winners | 0.1184 / 0.1473 | +0.0053 | 1 | 1.8837 / 1.9500 | 29.6% / 29.6% |
| market_plus_class | 0.1151 / 0.1323 | BEATS IT | 1 | 1.8874 / 1.9447 | 30.3% / 29.9% |
| market_plus_distance | 0.1150 / 0.1322 | BEATS IT | 1 | 1.8874 / 1.9441 | 30.1% / 30.3% |
| market_plus_speed | 0.1147 / 0.1322 | BEATS IT | 1 | 1.8868 / 1.9445 | 30.2% / 29.9% |
| market_plus_position | 0.1150 / 0.1322 | BEATS IT | 1 | 1.8874 / 1.9446 | 30.1% / 29.7% |
| market_plus_everything | 0.1144 / 0.1321 | BEATS IT | 1 | 1.8867 / 1.9438 | 29.6% / 30.1% |
| market_the_lot | 0.1143 / 0.1321 | BEATS IT | 1 | 1.8863 / 1.9441 | 29.7% / 30.1% |
| market_shaped | 0.1143 / 0.1323 | BEATS IT | 1 | 1.8856 / 1.9460 | 30.1% / 30.2% |
| market_shaped_all | 0.1136 / 0.1321 | BEATS IT | 1 | 1.8849 / 1.9450 | 29.8% / 30.2% |
| market_kitchen_sink | 0.1092 / 0.1260 | BEATS IT | 1 | 1.8814 / 1.9391 | 29.8% / 30.4% |
| market_kitchen_sink @winners | 0.1173 / 0.1414 | BEATS IT | 1 | 1.8714 / 1.9479 | 30.5% / 29.6% |
| market_plus_experience | 0.1145 / 0.1313 | BEATS IT | 1 | 1.8865 / 1.9437 | 29.8% / 29.6% |
| market_kitchen_sink_exp | 0.1087 / 0.1252 | BEATS IT | 1 | 1.8809 / 1.9384 | 29.5% / 30.5% |
| memory_plus_market | 0.1189 / 0.1361 | BEATS IT | 1 | 1.8927 / 1.9548 | 30.3% / 29.3% |
| market_plus_memory | 0.1129 / 0.1289 | BEATS IT | 1 | 1.8851 / 1.9404 | 30.3% / 29.9% |
| market_kitchen_sink_memory | 0.1072 / 0.1233 | BEATS IT | 1 | 1.8799 / 1.9357 | 29.4% / 29.7% |
| market_kitchen_sink_memory_intent **(deployed)** | 0.1060 / 0.1226 | BEATS IT | 1 | 1.8772 / 1.9370 | 29.9% / 29.4% |
| projection_sim | 0.3259 / 0.3302 | +0.1882 | - | 2.0985 / 2.1420 | 24.6% / 25.6% |

Deployed: **market_kitchen_sink_memory_intent**, the model closest to BSP out of sample, refitted on all 3720 races. It BEATS the morning market. The morning price is a legitimate input: we bet into it, so using it and landing closer to BSP than it does is exactly what beating the market means. EXP is the one thing barred, because Form King derives it from the market without saying which one and it scores like a figure that already knows the close. '@winners' marks a model fitted to the actual result rather than to the closing price.

## Coefficients of the deployed model

- neural_rel: +0.1383
- last_rel: +0.0279
- peak_rel: +0.0109
- peak12_rel: +0.0120
- wfa_rel: -0.0366
- wfa_best_rel: -0.0477
- ohr_rel: +0.0004
- dist_rel: +0.0194
- dist_win: +0.1870
- last_vs_lws: +0.0279
- best_vs_lws: +0.0310
- trend_slope: +0.0013
- starts_log: -0.0255
- last_dist_rel: -0.0015
- best_dist_rel: +0.0075
- dist_change: +0.0032
- speed_rel: +0.0051
- speed_best_rel: -0.0012
- finish_speed_rel: +0.0103
- last600_rel: -0.0052
- to600_rel: +0.0021
- settle_share: +0.0004
- pos800_share: -0.2102
- pos_gain: -0.1236
- late_gain: +0.1954
- early_pos: +0.1218
- early_x_tempo: -0.0406
- style_x_tempo: +0.0397
- map_vs_habit: -0.1455
- barrier_share: -0.0594
- days_log: -0.0389
- run_in_prep: -0.0051
- weight_rel: -0.0051
- wfa_diff: +0.0539
- beaten_3: +0.0005
- prize_log: -0.0075
- track_win: +0.3190
- going_win: +0.5083
- class_win: -0.0000
- td_win: +0.1783
- wet_win: +0.2259
- up_win: +0.0663
- jockey_win: +0.0227
- trainer_win: +0.0080
- jt_combo_win: +0.0000
- open_logit: +0.8523
- market_prob: -0.5344
- market_x_neural: -0.0432
- first_starter: +0.4175
- unrated: +0.0293
- trial_margin: -0.0090
- trialled_recently: +0.0229
- first_starter_x_market: +0.2389
- mkt_class: +0.0597
- beat_market: -0.2357
- beat_market_last: +0.0193
- field_strength: +0.0025
- strength_last: +0.0007
- trainer_only: +0.0143
- jockey_only: -0.0107
- apprentice_claim: -0.0563
- days_since_win_log: +0.0074
- dual_acceptor: +0.0064
- emergency: +0.1245

projection_sim parameters on the training races: recent_runs 4, decay 0.7, scope_bonus 1.0, trend_weight 0.0, shape_weight 0.0, late_weight 0.5, sd_floor 3.0, light_sd 1.5, sd_scale 3.0, unrated_gap 7.0, unrated_sd 3.0, neural_weight 15.0

Runners with no rated run (projected at the field mean less the unrated gap): 2608 of 36541.

Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the open_logit = the log of the opening-market chance and market_prob the chance itself, carried together so the fit can bend the market's own curve (short prices are historically underbet and long ones overbet, and log-chance alone cannot correct that); market_x_neural = the market read against Neural. The move from the open to the price NOW is deliberately absent: a race pulled after it ran carries its FINAL price, so it would be reading the answer. career peak and the 12-month peak; speed_rel, speed_best_rel = points below the race's best of Form King's speed figure (100 = class par) read over the last 4 races newest-weighted, and of the best one; finish_speed_rel = the same over finishing speed (last 600 as a share of the run to the 600); last600_rel, to600_rel = the last 600m and the run to it against the class standard, in lengths; settle_share, pos800_share = where the horse settles and where it sits with 800m to run, as a share of its own field (0 = on the lead, 1 = last) read over its recent races and centred on today's field; pos_gain, late_gain = positions made up from settling and from the 400m to the post, on the same share; style_x_tempo = that settling share against the expected tempo, so a backmarker in a slow-run race reads negative; map_vs_habit = how far today's speedmap asks the horse to race from where it usually does; wfa_rel, wfa_best_rel = points below the best of the latest and the best WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean rating of runs within 200m of today's trip; dist_win = the record at the distance as a shrunk win rate, against the race mean; last_vs_lws, best_vs_lws = the latest and the best rated run against the race's Likely Winning Standard (class); trend_slope = rating points per run over the last six runs; starts_log = log of career starts against the race mean (scope); open_logit = log of the opening-market chance (comparison only, never deployed, so Value keeps meaning disagreement with the market).

## Calibration of the deployed model

| rated chance | runners | mean rated | share that won |
|---|---|---|---|
| 0% to 5% | 13517 | 2.5% | 2.4% |
| 5% to 10% | 9167 | 7.3% | 7.2% |
| 10% to 20% | 8908 | 14.2% | 14.7% |
| 20% to 30% | 3176 | 24.2% | 24.0% |
| 30% to 50% | 1535 | 36.8% | 36.2% |
| 50% to 100% | 202 | 57.8% | 57.9% |

## The plans, replayed over 3720 races the fit never saw

Five blocks by date, each priced by a model fitted on the other four. Every bet is chosen against the OPENING market. The two profit columns are the SAME bets on two settlement bases: paid at Betfair SP, which is what betting into the jump gets you, and paid at Form King's AVERAGE OPENING price (avgOpen).

**Read the opening-price column as an upper bound, not a result.** avgOpen is an average of the first prices bookmakers put up, which nobody can take as a single bet, and it is the one price history holds. The live paper book bets at the price on the page when the morning run happens, which is later and sharper than the open, and there the value selections have drifted and lost (see the paper book). Profit is judged at Betfair SP here and at the struck price in the live book; this column only shows how much the open itself was beatable.

| plan | bets | winners | staked | at BSP: profit | return | at the average opening price: profit | return |
|---|---|---|---|---|---|---|---|
| top_pick | 3720 | 1105 | 3720.0 | -52.8 | -1.4% | -66.0 | -1.8% |
| value_flags | 1172 | 380 | 1172.0 | +49.8 | +4.3% | +353.1 | +30.1% |
| value_under_8 | 1162 | 379 | 1162.0 | +44.3 | +3.8% | +351.1 | +30.2% |
| top_pick_to_win_1 | 3703 | 1100 | 2239.0 | +634.3 | +28.3% | -345.6 | -15.4% |
| kelly_quarter | 8246 | 1213 | 6449.3 | +117.3 | +1.8% | +3262.0 | +50.6% |
| value_ev20 | 3512 | 560 | 3512.0 | +188.8 | +5.4% | +2289.6 | +65.2% |
| value_ev05 | 6677 | 996 | 6677.0 | +57.0 | +0.9% | +2644.5 | +39.6% |
| value_ev10 | 5432 | 831 | 5432.0 | +208.3 | +3.8% | +2691.0 | +49.5% |
| value_tiered | 6677 | 996 | 15621.0 | +454.1 | +2.9% | +7625.1 | +48.8% |
| value_ev20_kelly | 3512 | 560 | 4782.4 | +193.5 | +4.0% | +3108.9 | +65.0% |

## Choosing the value rule: value_flags

gap = our chance beats the opening market's by more than the threshold in percentage points (the live rule is gap 0.05). ev = our chance times the average opening price is more than 1 plus the threshold. Each rule is picked on the OLDER 3 fifths of the racing by its return at Betfair SP (at least 30 bets), then shown on the NEWER two fifths it never saw. Returns are one unit a bet, before commission.

| rule | threshold | older: bets | at BSP | at avg opening price | newer: bets | at BSP | at avg opening price |
|---|---|---|---|---|---|---|---|
| gap | 0.02 | 2829 | -0.1% | +18.2% | 1831 | -4.8% | +14.6% |
| gap | 0.03 | 1744 | +1.0% | +23.6% | 1120 | -1.6% | +22.0% |
| gap **(chosen)** | 0.05 | 678 | +11.7% | +35.7% | 482 | -6.3% | +24.5% |
| gap | 0.08 | 181 | +2.0% | +38.9% | 152 | -6.2% | +18.2% |
| gap | 0.10 | 73 | +7.6% | +27.0% | 77 | +7.5% | +27.6% |
| ev | 0.05 | 4219 | -4.1% | +33.0% | 2796 | -2.2% | +38.8% |
| ev | 0.10 | 3409 | -1.1% | +43.1% | 2305 | +0.5% | +48.3% |
| ev | 0.20 | 2201 | -3.7% | +54.9% | 1481 | +10.0% | +73.2% |
| ev | 0.30 | 1460 | -1.3% | +67.6% | 981 | +18.0% | +89.0% |
| ev | 0.50 | 679 | +4.1% | +108.5% | 460 | +18.3% | +94.8% |

## Choosing the value rule: value_under_8

gap = our chance beats the opening market's by more than the threshold in percentage points (the live rule is gap 0.05). ev = our chance times the average opening price is more than 1 plus the threshold. Each rule is picked on the OLDER 3 fifths of the racing by its return at Betfair SP (at least 30 bets), then shown on the NEWER two fifths it never saw. Returns are one unit a bet, before commission.

| rule | threshold | older: bets | at BSP | at avg opening price | newer: bets | at BSP | at avg opening price |
|---|---|---|---|---|---|---|---|
| gap | 0.02 | 2334 | +5.5% | +19.3% | 1525 | -3.7% | +9.7% |
| gap | 0.03 | 1606 | +2.7% | +22.6% | 1047 | -0.6% | +18.4% |
| gap **(chosen)** | 0.05 | 676 | +9.7% | +34.3% | 474 | -4.7% | +26.6% |
| gap | 0.08 | 181 | +2.0% | +38.9% | 152 | -6.2% | +18.2% |
| gap | 0.10 | 73 | +7.6% | +27.0% | 77 | +7.5% | +27.6% |
| ev | 0.05 | 1887 | -0.8% | +38.3% | 1247 | -2.2% | +30.7% |
| ev | 0.10 | 1561 | -3.9% | +39.9% | 1046 | -1.5% | +36.1% |
| ev | 0.20 | 999 | -5.9% | +47.4% | 714 | +2.6% | +50.9% |
| ev | 0.30 | 682 | -4.8% | +59.4% | 500 | -0.2% | +60.6% |
| ev | 0.50 | 337 | +1.4% | +92.3% | 251 | +0.9% | +75.3% |

## The strategy search: where, if anywhere, the bets make money

158 strategies: each betting rule (ev = our chance x the opening price must beat 1 by the threshold; gap = our chance must beat the market's by the threshold in points) crossed with a slice of the racing (price band, field size, first starters, metro or not). Every one is scored on the OLDER three fifths of the racing and then on the NEWER two fifths it never saw. One unit a bet, before commission. '±' is one standard error: a return inside about two of them is indistinguishable from luck. With this many tried, some look good on the older racing by chance alone, so only the newer column counts.

- Profitable at Betfair SP in BOTH halves: 51 of 158
- Profitable at the average opening price in BOTH halves: 150 of 158 (upper bound: an average, not a takeable price)
- Profitable at Betfair SP on the newer racing by more than two standard errors, and profitable on the older: 0
- Profitable at the average opening price on the newer racing by more than two standard errors, and on the older: 105


### Best twelve on the older racing at Betfair SP, and how they did on the newer

| rule | slice | older: bets | at BSP | at open | newer: bets | at BSP | at open |
|---|---|---|---|---|---|---|---|
| ev 0.35 | metro | 184 | +82.2% ±45.1% | +161.1% ±57.0% | 129 | +19.0% ±29.2% | +95.0% ±51.5% |
| ev 0.25 | metro | 295 | +49.8% ±31.1% | +103.1% ±37.7% | 208 | +7.6% ±22.2% | +72.3% ±37.9% |
| ev 0.20 | metro | 388 | +49.0% ±27.4% | +87.2% ±30.3% | 259 | -4.5% ±18.5% | +55.6% ±31.9% |
| ev 0.15 | metro | 505 | +38.4% ±24.5% | +71.4% ±25.8% | 347 | -1.7% ±16.5% | +52.6% ±26.4% |
| ev 0.50 | our top pick | 113 | +37.0% ±21.1% | +125.9% ±29.1% | 100 | +13.5% ±19.6% | +71.8% ±24.5% |
| ev 0.50 | metro | 81 | +36.0% ±47.1% | +142.4% ±88.1% | 67 | -11.8% ±38.7% | +17.7% ±36.3% |
| ev 0.15 | first starters | 112 | +30.2% ±33.9% | +99.6% ±47.1% | 70 | -42.4% ±24.0% | -25.1% ±27.0% |
| gap 0.10 | field 9-12 | 40 | +29.5% ±42.8% | +39.0% ±33.3% | 41 | +6.3% ±21.3% | +39.5% ±28.6% |
| ev 0.20 | first starters | 87 | +29.4% ±38.8% | +101.9% ±51.5% | 54 | -25.3% ±30.7% | -3.0% ±34.5% |
| gap 0.05 | we rate $5-10 | 92 | +29.2% ±30.3% | +54.3% ±34.9% | 68 | +8.6% ±25.0% | +118.4% ±52.2% |
| ev 0.15 | Saturdays | 526 | +27.9% ±21.8% | +62.4% ±24.8% | 248 | +2.8% ±19.0% | +70.2% ±33.8% |
| ev 0.35 | Saturdays | 194 | +24.8% ±28.9% | +125.9% ±53.1% | 88 | +31.5% ±34.0% | +136.8% ±70.7% |

### Best twelve on the older racing at the opening price, and how they did on the newer

| rule | slice | older: bets | at BSP | at open | newer: bets | at BSP | at open |
|---|---|---|---|---|---|---|---|
| ev 0.35 | metro | 184 | +82.2% ±45.1% | +161.1% ±57.0% | 129 | +19.0% ±29.2% | +95.0% ±51.5% |
| ev 0.50 | field <=8 | 359 | +8.3% ±15.9% | +148.2% ±40.9% | 230 | +15.5% ±21.3% | +98.6% ±35.0% |
| ev 0.50 | metro | 81 | +36.0% ±47.1% | +142.4% ±88.1% | 67 | -11.8% ±38.7% | +17.7% ±36.3% |
| ev 0.50 | we rate <$5 | 181 | +22.3% ±15.0% | +130.0% ±26.0% | 153 | -8.2% ±15.8% | +38.3% ±19.9% |
| ev 0.50 | price $16+ | 326 | -0.8% ±24.0% | +127.9% ±50.9% | 187 | +34.1% ±45.8% | +117.2% ±60.1% |
| ev 0.35 | Saturdays | 194 | +24.8% ±28.9% | +125.9% ±53.1% | 88 | +31.5% ±34.0% | +136.8% ±70.7% |
| ev 0.50 | our top pick | 113 | +37.0% ±21.1% | +125.9% ±29.1% | 100 | +13.5% ±19.6% | +71.8% ±24.5% |
| ev 0.50 | we rate $10+ | 276 | -1.3% ±27.5% | +114.8% ±57.4% | 160 | +42.2% ±53.0% | +108.2% ±67.0% |
| ev 0.50 | weekdays | 579 | +7.6% ±14.7% | +114.5% ±28.6% | 414 | +21.2% ±22.8% | +98.8% ±30.2% |
| ev 0.35 | field <=8 | 560 | +7.9% ±13.4% | +111.4% ±28.3% | 332 | +16.4% ±17.4% | +103.3% ±30.9% |
| ev 0.20 | field 13+ | 96 | +0.8% ±33.1% | +110.2% ±70.6% | 98 | -17.6% ±22.3% | +47.8% ±43.7% |
| ev 0.50 | raced horses | 642 | +5.0% ±13.8% | +110.1% ±27.7% | 442 | +19.8% ±21.7% | +98.8% ±28.9% |

### Beating the morning price, ranked by how far clear of luck on the newer racing

| rule | slice | older: bets | at open | newer: bets | at open | at BSP | standard errors clear |
|---|---|---|---|---|---|---|---|
| ev 0.25 | all | 1782 | +58.1% | 1204 | +87.8% ±18.9% | +18.0% | 4.6 |
| ev 0.25 | raced horses | 1713 | +58.9% | 1156 | +91.1% ±19.6% | +19.5% | 4.6 |
| ev 0.20 | raced horses | 2109 | +53.3% | 1427 | +76.1% ±16.7% | +11.3% | 4.6 |
| ev 0.20 | all | 2196 | +55.2% | 1481 | +73.2% ±16.1% | +10.0% | 4.5 |
| ev 0.35 | raced horses | 1146 | +81.1% | 764 | +101.8% ±22.4% | +22.7% | 4.5 |
| ev 0.15 | raced horses | 2629 | +49.9% | 1780 | +65.0% ±14.3% | +5.6% | 4.5 |
| ev 0.35 | all | 1194 | +80.1% | 800 | +96.6% ±21.5% | +19.7% | 4.5 |
| ev 0.15 | all | 2741 | +51.9% | 1850 | +61.6% ±13.8% | +3.8% | 4.5 |
| ev 0.10 | raced horses | 3262 | +41.9% | 2219 | +50.8% ±11.9% | +1.8% | 4.3 |
| ev 0.25 | country and provincial | 1487 | +49.1% | 996 | +91.1% ±21.5% | +20.2% | 4.2 |
| ev 0.25 | weekdays | 1461 | +55.5% | 1061 | +85.4% ±20.3% | +17.7% | 4.2 |
| ev 0.20 | country and provincial | 1808 | +48.4% | 1222 | +76.9% ±18.3% | +13.1% | 4.2 |
| ev 0.10 | all | 3404 | +43.3% | 2305 | +48.3% ±11.5% | +0.5% | 4.2 |
| ev 0.20 | our top pick | 347 | +50.4% | 289 | +56.0% ±13.5% | +19.4% | 4.1 |
| ev 0.20 | weekdays | 1775 | +54.6% | 1303 | +71.8% ±17.4% | +10.3% | 4.1 |
| ev 0.35 | country and provincial | 1010 | +65.4% | 671 | +96.9% ±23.7% | +19.8% | 4.1 |
| ev 0.35 | weekdays | 1000 | +71.2% | 712 | +91.6% ±22.5% | +18.2% | 4.1 |
| ev 0.05 | raced horses | 4045 | +32.1% | 2693 | +41.1% ±10.2% | -1.1% | 4.0 |
| ev 0.15 | country and provincial | 2236 | +47.5% | 1503 | +63.6% ±15.9% | +5.1% | 4.0 |
| ev 0.15 | weekdays | 2215 | +49.4% | 1602 | +60.2% ±15.1% | +4.0% | 4.0 |
