# Back-test against Betfair SP

Fitted 2026-09-23 08:34 UTC over 3260 resulted races (32071 runners), 2025-11-04 to 2026-09-22. Out of sample = fitted on the first 2282 races by date, scored on the last 978.

Each model is a conditional logit fitted to minimise the cross-entropy against a target: the BSP-implied chances, or ('@winners') the actual result. 'KL to BSP' is how far it sits from Betfair SP, the sharpest price anyone gets and so the stand-in for the truth. **The bar is not zero, it is the morning market**, which sits at 0.1370 out of sample: that is the price we bet into, so a model closer to BSP than it is has beaten the market it is betting against. 'log loss' is scored on the actual winners and 'top pick won' is the share of races the model's highest-rated runner won.

| model | KL to BSP (in / out) | vs the morning market | ridge | log loss vs winners (in / out) | top pick won (in / out) |
|---|---|---|---|---|---|
| bsp_itself | 0.0000 / 0.0000 | - | - | 1.7596 / 1.8200 | 35.3% / 34.4% |
| opening_market | 0.1273 / 0.1370 | the bar | - | 1.9029 / 1.9662 | 29.6% / 28.8% |
| neural_only | 0.2778 / 0.2517 | +0.1147 | 0.01 | 2.0519 / 2.1086 | 23.2% / 22.8% |
| kitchen_sink | 0.1816 / 0.1737 | +0.0367 | 1 | 1.9538 / 2.0152 | 28.4% / 26.3% |
| all_form_plus_open_market | 0.1185 / 0.1286 | BEATS IT | 1 | 1.8887 / 1.9552 | 30.0% / 29.1% |
| all_form_plus_open_market @winners | 0.1217 / 0.1452 | +0.0082 | 1 | 1.8855 / 1.9604 | 29.8% / 29.3% |
| market_plus_class | 0.1181 / 0.1287 | BEATS IT | 1e-08 | 1.8897 / 1.9548 | 30.2% / 30.0% |
| market_plus_distance | 0.1180 / 0.1287 | BEATS IT | 0.01 | 1.8895 / 1.9544 | 30.3% / 29.6% |
| market_plus_speed | 0.1176 / 0.1287 | BEATS IT | 0.01 | 1.8896 / 1.9547 | 30.1% / 29.4% |
| market_plus_position | 0.1180 / 0.1286 | BEATS IT | 1e-08 | 1.8897 / 1.9545 | 30.0% / 29.6% |
| market_plus_everything | 0.1174 / 0.1286 | BEATS IT | 0.01 | 1.8894 / 1.9542 | 29.7% / 29.6% |
| market_the_lot | 0.1173 / 0.1286 | BEATS IT | 0.01 | 1.8886 / 1.9548 | 29.7% / 29.3% |
| market_shaped | 0.1173 / 0.1287 | BEATS IT | 1e-08 | 1.8879 / 1.9564 | 30.0% / 29.8% |
| market_shaped_all | 0.1166 / 0.1286 | BEATS IT | 0.01 | 1.8876 / 1.9557 | 29.5% / 29.6% |
| market_kitchen_sink | 0.1119 / 0.1227 | BEATS IT | 1 | 1.8836 / 1.9511 | 29.6% / 29.9% |
| market_kitchen_sink @winners | 0.1211 / 0.1367 | BEATS IT | 1 | 1.8722 / 1.9558 | 30.6% / 30.2% |
| market_plus_experience | 0.1175 / 0.1276 | BEATS IT | 1e-08 | 1.8884 / 1.9541 | 29.8% / 29.2% |
| market_kitchen_sink_exp **(deployed)** | 0.1115 / 0.1219 | BEATS IT | 1 | 1.8830 / 1.9505 | 29.5% / 30.4% |
| projection_sim | 0.3288 / 0.3291 | +0.1921 | - | 2.0978 / 2.1445 | 24.7% / 25.7% |

Deployed: **market_kitchen_sink_exp**, the model closest to BSP out of sample, refitted on all 3260 races. It BEATS the morning market. The morning price is a legitimate input: we bet into it, so using it and landing closer to BSP than it does is exactly what beating the market means. EXP is the one thing barred, because Form King derives it from the market without saying which one and it scores like a figure that already knows the close. '@winners' marks a model fitted to the actual result rather than to the closing price.

## Coefficients of the deployed model

- neural_rel: +0.0992
- last_rel: +0.0222
- peak_rel: +0.0057
- peak12_rel: +0.0134
- wfa_rel: -0.0266
- wfa_best_rel: -0.0693
- ohr_rel: -0.0005
- dist_rel: +0.0247
- dist_win: +0.0881
- last_vs_lws: +0.0222
- best_vs_lws: +0.0587
- trend_slope: -0.0042
- starts_log: -0.0166
- last_dist_rel: -0.0035
- best_dist_rel: +0.0047
- dist_change: +0.0013
- speed_rel: +0.0041
- speed_best_rel: -0.0008
- finish_speed_rel: +0.0107
- last600_rel: -0.0054
- to600_rel: +0.0025
- settle_share: -0.0428
- pos800_share: -0.1650
- pos_gain: -0.0989
- late_gain: +0.1889
- early_pos: +0.1102
- early_x_tempo: -0.0454
- style_x_tempo: +0.0408
- map_vs_habit: -0.1380
- barrier_share: -0.0447
- days_log: -0.0474
- run_in_prep: -0.0047
- weight_rel: +0.0094
- wfa_diff: +0.0611
- beaten_3: -0.0010
- prize_log: -0.0268
- track_win: +0.2968
- going_win: +0.4290
- class_win: -0.0000
- td_win: +0.1397
- wet_win: +0.0000
- up_win: +0.0310
- jockey_win: +0.0248
- trainer_win: +0.0078
- jt_combo_win: +0.0000
- open_logit: +0.8813
- market_prob: -0.4124
- market_x_neural: -0.0634
- first_starter: +0.3639
- unrated: -0.0637
- trial_margin: -0.0092
- trialled_recently: +0.0254
- first_starter_x_market: +0.2001

projection_sim parameters on the training races: recent_runs 4, decay 0.7, scope_bonus 1.0, trend_weight 0.0, shape_weight 0.0, late_weight 0.5, sd_floor 3.0, light_sd 1.5, sd_scale 3.0, unrated_gap 7.0, unrated_sd 3.0, neural_weight 15.0

Runners with no rated run (projected at the field mean less the unrated gap): 2334 of 32071.

Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the open_logit = the log of the opening-market chance and market_prob the chance itself, carried together so the fit can bend the market's own curve (short prices are historically underbet and long ones overbet, and log-chance alone cannot correct that); market_x_neural = the market read against Neural. The move from the open to the price NOW is deliberately absent: a race pulled after it ran carries its FINAL price, so it would be reading the answer. career peak and the 12-month peak; speed_rel, speed_best_rel = points below the race's best of Form King's speed figure (100 = class par) read over the last 4 races newest-weighted, and of the best one; finish_speed_rel = the same over finishing speed (last 600 as a share of the run to the 600); last600_rel, to600_rel = the last 600m and the run to it against the class standard, in lengths; settle_share, pos800_share = where the horse settles and where it sits with 800m to run, as a share of its own field (0 = on the lead, 1 = last) read over its recent races and centred on today's field; pos_gain, late_gain = positions made up from settling and from the 400m to the post, on the same share; style_x_tempo = that settling share against the expected tempo, so a backmarker in a slow-run race reads negative; map_vs_habit = how far today's speedmap asks the horse to race from where it usually does; wfa_rel, wfa_best_rel = points below the best of the latest and the best WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean rating of runs within 200m of today's trip; dist_win = the record at the distance as a shrunk win rate, against the race mean; last_vs_lws, best_vs_lws = the latest and the best rated run against the race's Likely Winning Standard (class); trend_slope = rating points per run over the last six runs; starts_log = log of career starts against the race mean (scope); open_logit = log of the opening-market chance (comparison only, never deployed, so Value keeps meaning disagreement with the market).

## Calibration of the deployed model

| rated chance | runners | mean rated | share that won |
|---|---|---|---|
| 0% to 5% | 11790 | 2.5% | 2.4% |
| 5% to 10% | 8078 | 7.3% | 7.3% |
| 10% to 20% | 7900 | 14.2% | 14.3% |
| 20% to 30% | 2805 | 24.2% | 24.7% |
| 30% to 50% | 1306 | 36.6% | 35.5% |
| 50% to 100% | 171 | 57.3% | 60.2% |

## The plans, replayed over 3260 races the fit never saw

Five blocks by date, each priced by a model fitted on the other four. Every bet is chosen against the OPENING market. The two profit columns are the SAME bets on two settlement bases: paid at Betfair SP, which is what betting into the jump gets you, and paid at Form King's AVERAGE OPENING price (avgOpen).

**Read the opening-price column as an upper bound, not a result.** avgOpen is an average of the first prices bookmakers put up, which nobody can take as a single bet, and it is the one price history holds. The live paper book bets at the price on the page when the morning run happens, which is later and sharper than the open, and there the value selections have drifted and lost (see the paper book). Profit is judged at Betfair SP here and at the struck price in the live book; this column only shows how much the open itself was beatable.

| plan | bets | winners | staked | at BSP: profit | return | at the average opening price: profit | return |
|---|---|---|---|---|---|---|---|
| top_pick | 3260 | 977 | 3260.0 | +15.3 | +0.5% | -50.0 | -1.5% |
| value_flags | 818 | 272 | 818.0 | +12.4 | +1.5% | +229.9 | +28.1% |
| value_under_8 | 810 | 272 | 810.0 | +20.4 | +2.5% | +237.9 | +29.4% |
| top_pick_to_win_1 | 3251 | 975 | 2008.2 | +668.9 | +33.3% | -314.7 | -15.7% |
| kelly_quarter | 7434 | 1022 | 5298.3 | +44.0 | +0.8% | +2542.3 | +48.0% |

## Choosing the value rule: value_flags

gap = our chance beats the opening market's by more than the threshold in percentage points (the live rule is gap 0.05). ev = our chance times the average opening price is more than 1 plus the threshold. Each rule is picked on the OLDER 3 fifths of the racing by its return at Betfair SP (at least 30 bets), then shown on the NEWER two fifths it never saw. Returns are one unit a bet, before commission.

| rule | threshold | older: bets | at BSP | at avg opening price | newer: bets | at BSP | at avg opening price |
|---|---|---|---|---|---|---|---|
| gap | 0.02 | 2263 | -0.3% | +18.7% | 1468 | -8.5% | +9.0% |
| gap | 0.03 | 1331 | +5.5% | +25.0% | 873 | -7.9% | +16.1% |
| gap (live) | 0.05 | 454 | +8.9% | +38.3% | 359 | -7.0% | +16.7% |
| gap **(chosen)** | 0.08 | 126 | +20.7% | +54.6% | 115 | -11.6% | -1.4% |
| gap | 0.10 | 51 | +6.9% | +40.3% | 60 | +1.6% | +6.2% |
| ev | 0.05 | 3547 | -6.4% | +29.6% | 2358 | -3.9% | +38.1% |
| ev | 0.10 | 2842 | -4.8% | +37.0% | 1894 | +2.6% | +52.0% |
| ev | 0.20 | 1762 | -2.9% | +56.8% | 1239 | +15.8% | +85.3% |
| ev | 0.30 | 1168 | -0.8% | +70.7% | 833 | +22.6% | +103.8% |
| ev | 0.50 | 546 | +1.4% | +111.0% | 383 | +28.7% | +125.5% |

## Choosing the value rule: value_under_8

gap = our chance beats the opening market's by more than the threshold in percentage points (the live rule is gap 0.05). ev = our chance times the average opening price is more than 1 plus the threshold. Each rule is picked on the OLDER 3 fifths of the racing by its return at Betfair SP (at least 30 bets), then shown on the NEWER two fifths it never saw. Returns are one unit a bet, before commission.

| rule | threshold | older: bets | at BSP | at avg opening price | newer: bets | at BSP | at avg opening price |
|---|---|---|---|---|---|---|---|
| gap | 0.02 | 1848 | +2.9% | +17.4% | 1259 | -5.5% | +9.6% |
| gap | 0.03 | 1229 | +6.0% | +23.6% | 825 | -8.4% | +13.0% |
| gap (live) | 0.05 | 451 | +9.6% | +39.2% | 354 | -5.6% | +18.3% |
| gap **(chosen)** | 0.08 | 126 | +20.7% | +54.6% | 115 | -11.6% | -1.4% |
| gap | 0.10 | 51 | +6.9% | +40.3% | 60 | +1.6% | +6.2% |
| ev | 0.05 | 1569 | +3.6% | +39.4% | 1047 | +1.8% | +32.8% |
| ev | 0.10 | 1233 | -2.8% | +39.5% | 869 | +6.9% | +42.7% |
| ev | 0.20 | 773 | -3.5% | +50.7% | 606 | +8.1% | +51.9% |
| ev | 0.30 | 530 | -2.0% | +65.5% | 426 | +1.7% | +59.0% |
| ev | 0.50 | 253 | +17.5% | +123.2% | 207 | +6.3% | +84.7% |

## The strategy search: where, if anywhere, the bets make money

66 strategies: each betting rule (ev = our chance x the opening price must beat 1 by the threshold; gap = our chance must beat the market's by the threshold in points) crossed with a slice of the racing (price band, field size, first starters, metro or not). Every one is scored on the OLDER three fifths of the racing and then on the NEWER two fifths it never saw. One unit a bet, before commission. '±' is one standard error: a return inside about two of them is indistinguishable from luck. With this many tried, some look good on the older racing by chance alone, so only the newer column counts.

- Profitable at Betfair SP in BOTH halves: 9 of 66
- Profitable at the average opening price in BOTH halves: 61 of 66 (upper bound: an average, not a takeable price)
- Profitable at Betfair SP on the newer racing by more than two standard errors, and profitable on the older: 0


### Best twelve on the older racing at Betfair SP, and how they did on the newer

| rule | slice | older: bets | at BSP | at open | newer: bets | at BSP | at open |
|---|---|---|---|---|---|---|---|
| ev 0.35 | metro | 134 | +75.6% ±57.3% | +147.1% ±69.8% | 117 | +11.1% ±30.4% | +46.2% ±33.4% |
| ev 0.20 | metro | 324 | +59.8% ±35.7% | +98.9% ±37.2% | 243 | -7.0% ±18.2% | +48.0% ±31.8% |
| ev 0.20 | first starters | 70 | +29.9% ±46.8% | +109.4% ±62.4% | 48 | -35.7% ±31.8% | -9.6% ±37.1% |
| ev 0.10 | first starters | 116 | +24.0% ±32.6% | +93.0% ±45.7% | 72 | -49.1% ±22.0% | -26.9% ±26.3% |
| gap 0.10 | country and provincial | 46 | +18.6% ±23.6% | +55.6% ±29.6% | 55 | +1.0% ±27.1% | +2.2% ±22.9% |
| ev 0.10 | metro | 558 | +16.9% ±21.5% | +45.2% ±22.7% | 391 | -1.4% ±15.1% | +42.8% ±23.2% |
| ev 0.05 | first starters | 134 | +15.7% ±28.6% | +82.4% ±40.4% | 88 | -40.1% ±23.2% | -22.0% ±25.2% |
| gap 0.05 | metro | 61 | +15.6% ±20.3% | +43.5% ±26.3% | 48 | +14.2% ±22.2% | +64.6% ±29.8% |
| gap 0.05 | field <=8 | 180 | +15.3% ±13.1% | +59.2% ±19.0% | 113 | -3.9% ±19.2% | +1.6% ±17.4% |
| gap 0.03 | field 13+ | 99 | +12.8% ±22.5% | +26.0% ±23.0% | 102 | -21.3% ±19.6% | -14.7% ±20.4% |
| gap 0.03 | price $8-16 | 237 | +10.5% ±19.8% | +47.9% ±23.2% | 134 | -6.3% ±21.2% | +61.3% ±33.3% |
| gap 0.05 | price <$4 | 234 | +10.0% ±9.4% | +18.6% ±9.3% | 177 | -0.7% ±11.3% | +3.3% ±10.3% |

### Best twelve on the older racing at the opening price, and how they did on the newer

| rule | slice | older: bets | at BSP | at open | newer: bets | at BSP | at open |
|---|---|---|---|---|---|---|---|
| ev 0.35 | metro | 134 | +75.6% ±57.3% | +147.1% ±69.8% | 117 | +11.1% ±30.4% | +46.2% ±33.4% |
| ev 0.20 | field 13+ | 66 | -23.4% ±32.5% | +120.2% ±96.3% | 82 | +12.4% ±33.8% | +64.4% ±50.0% |
| ev 0.20 | first starters | 70 | +29.9% ±46.8% | +109.4% ±62.4% | 48 | -35.7% ±31.8% | -9.6% ±37.1% |
| ev 0.35 | field <=8 | 445 | -3.6% ±13.9% | +105.5% ±33.3% | 310 | +20.1% ±18.8% | +104.0% ±32.6% |
| ev 0.20 | metro | 324 | +59.8% ±35.7% | +98.9% ±37.2% | 243 | -7.0% ±18.2% | +48.0% ±31.8% |
| ev 0.10 | first starters | 116 | +24.0% ±32.6% | +93.0% ±45.7% | 72 | -49.1% ±22.0% | -26.9% ±26.3% |
| ev 0.35 | price $16+ | 432 | -6.2% ±22.6% | +89.1% ±40.5% | 260 | +18.0% ±34.5% | +109.7% ±50.2% |
| ev 0.05 | first starters | 134 | +15.7% ±28.6% | +82.4% ±40.4% | 88 | -40.1% ±23.2% | -22.0% ±25.2% |
| ev 0.20 | price $16+ | 749 | +3.1% ±18.8% | +75.7% ±28.7% | 469 | +24.2% ±25.8% | +146.9% ±46.7% |
| ev 0.20 | field <=8 | 718 | -2.0% ±11.4% | +75.5% ±22.5% | 463 | +9.6% ±15.0% | +103.1% ±34.6% |
| ev 0.35 | all | 951 | -8.9% ±11.5% | +68.0% ±20.0% | 687 | +14.4% ±15.5% | +81.4% ±21.9% |
| ev 0.35 | raced horses | 910 | -9.1% ±11.9% | +67.4% ±20.7% | 656 | +18.2% ±16.2% | +86.6% ±22.8% |
