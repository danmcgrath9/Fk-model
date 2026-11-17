# Back-test against Betfair SP

Fitted 2026-11-17 06:41 UTC over 5367 resulted races (53260 runners), 2025-07-01 to 2026-11-16. Out of sample = fitted on the first 3756 races by date, scored on the last 1611.

Each model is a conditional logit fitted to minimise the cross-entropy against a target: the BSP-implied chances, or ('@winners') the actual result. 'KL to BSP' is how far it sits from Betfair SP, the sharpest price anyone gets and so the stand-in for the truth. **The bar is not zero, it is the morning market**, which sits at 0.1465 out of sample: that is the price we bet into, so a model closer to BSP than it is has beaten the market it is betting against. 'log loss' is scored on the actual winners and 'top pick won' is the share of races the model's highest-rated runner won.

| model | KL to BSP (in / out) | vs the morning market | ridge | log loss vs winners (in / out) | top pick won (in / out) |
|---|---|---|---|---|---|
| bsp_itself | 0.0000 / 0.0000 | - | - | 1.7780 / 1.8074 | 34.9% / 33.5% |
| opening_market | 0.1206 / 0.1465 | the bar | - | 1.9062 / 1.9610 | 29.7% / 28.4% |
| neural_only | 0.2747 / 0.2734 | +0.1269 | 1e-08 | 2.0606 / 2.0983 | 23.9% / 22.3% |
| kitchen_sink | 0.1799 / 0.1796 | +0.0331 | 1 | 1.9688 / 1.9978 | 27.4% / 26.7% |
| all_form_plus_open_market | 0.1133 / 0.1374 | BEATS IT | 0.01 | 1.8970 / 1.9489 | 30.2% / 29.4% |
| all_form_plus_open_market @winners | 0.1139 / 0.1375 | BEATS IT | 1 | 1.8964 / 1.9496 | 29.9% / 29.5% |
| market_plus_class | 0.1128 / 0.1367 | BEATS IT | 1 | 1.8975 / 1.9488 | 30.2% / 29.7% |
| market_plus_distance | 0.1127 / 0.1366 | BEATS IT | 1 | 1.8974 / 1.9488 | 30.1% / 29.8% |
| market_plus_speed | 0.1125 / 0.1367 | BEATS IT | 1 | 1.8974 / 1.9484 | 30.1% / 29.6% |
| market_plus_position | 0.1126 / 0.1365 | BEATS IT | 1 | 1.8977 / 1.9486 | 30.2% / 29.4% |
| market_plus_everything | 0.1123 / 0.1365 | BEATS IT | 1 | 1.8975 / 1.9483 | 30.0% / 29.8% |
| market_the_lot | 0.1122 / 0.1365 | BEATS IT | 1 | 1.8971 / 1.9482 | 30.0% / 29.6% |
| market_shaped | 0.1121 / 0.1367 | BEATS IT | 1 | 1.8966 / 1.9486 | 30.0% / 29.6% |
| market_shaped_all | 0.1116 / 0.1364 | BEATS IT | 1 | 1.8966 / 1.9481 | 30.0% / 29.6% |
| market_kitchen_sink | 0.1074 / 0.1288 | BEATS IT | 1 | 1.8932 / 1.9401 | 30.0% / 30.1% |
| market_kitchen_sink @winners | 0.1123 / 0.1341 | BEATS IT | 1 | 1.8873 / 1.9462 | 30.4% / 29.5% |
| market_plus_experience | 0.1122 / 0.1360 | BEATS IT | 1 | 1.8963 / 1.9483 | 30.0% / 29.5% |
| market_kitchen_sink_exp | 0.1070 / 0.1283 | BEATS IT | 1 | 1.8924 / 1.9399 | 29.9% / 29.9% |
| memory_plus_market | 0.1159 / 0.1413 | BEATS IT | 1 | 1.9006 / 1.9569 | 30.2% / 28.8% |
| market_plus_memory | 0.1107 / 0.1338 | BEATS IT | 1 | 1.8949 / 1.9468 | 30.4% / 29.4% |
| market_kitchen_sink_memory | 0.1056 / 0.1265 | BEATS IT | 1 | 1.8912 / 1.9385 | 29.7% / 29.5% |
| market_kitchen_sink_memory_intent **(deployed)** | 0.1043 / 0.1255 | BEATS IT | 1 | 1.8890 / 1.9392 | 30.1% / 29.1% |
| projection_sim | 0.3262 / 0.3345 | +0.1880 | - | 2.1068 / 2.1392 | 24.9% / 24.1% |

Deployed: **market_kitchen_sink_memory_intent**, the model closest to BSP out of sample, refitted on all 5367 races. It BEATS the morning market. The morning price is a legitimate input: we bet into it, so using it and landing closer to BSP than it does is exactly what beating the market means. EXP is the one thing barred, because Form King derives it from the market without saying which one and it scores like a figure that already knows the close. '@winners' marks a model fitted to the actual result rather than to the closing price.

## Coefficients of the deployed model

- neural_rel: +0.1116
- last_rel: +0.0256
- peak_rel: -0.0070
- peak12_rel: +0.0112
- wfa_rel: -0.0332
- wfa_best_rel: -0.0457
- ohr_rel: +0.0007
- dist_rel: +0.0197
- dist_win: +0.2167
- last_vs_lws: +0.0256
- best_vs_lws: +0.0493
- trend_slope: +0.0022
- starts_log: -0.0342
- last_dist_rel: -0.0013
- best_dist_rel: +0.0055
- dist_change: +0.0030
- speed_rel: +0.0035
- speed_best_rel: +0.0001
- finish_speed_rel: +0.0074
- last600_rel: -0.0039
- to600_rel: +0.0015
- settle_share: +0.0094
- pos800_share: -0.2034
- pos_gain: -0.1520
- late_gain: +0.2135
- early_pos: +0.1197
- early_x_tempo: -0.0336
- style_x_tempo: +0.0267
- map_vs_habit: -0.1592
- barrier_share: -0.0707
- days_log: -0.0365
- run_in_prep: -0.0046
- weight_rel: -0.0091
- wfa_diff: +0.0530
- beaten_3: +0.0002
- prize_log: -0.0030
- track_win: +0.3407
- going_win: +0.4837
- class_win: +0.0000
- td_win: +0.1478
- wet_win: +0.2325
- up_win: +0.1363
- jockey_win: +0.0231
- trainer_win: +0.0077
- jt_combo_win: +0.0000
- open_logit: +0.8589
- market_prob: -0.4864
- market_x_neural: -0.0480
- first_starter: +0.4691
- unrated: +0.0559
- trial_margin: -0.0079
- trialled_recently: +0.0150
- first_starter_x_market: +0.2454
- mkt_class: +0.0526
- beat_market: -0.2503
- beat_market_last: +0.0315
- field_strength: +0.0022
- strength_last: +0.0008
- trainer_only: +0.0176
- jockey_only: -0.0211
- apprentice_claim: -0.0586
- days_since_win_log: +0.0096
- dual_acceptor: +0.0140
- emergency: +0.1374

projection_sim parameters on the training races: recent_runs 4, decay 0.7, scope_bonus 1.0, trend_weight 0.0, shape_weight 0.0, late_weight 0.5, sd_floor 3.0, light_sd 1.5, sd_scale 3.0, unrated_gap 7.0, unrated_sd 3.0, neural_weight 15.0

Runners with no rated run (projected at the field mean less the unrated gap): 3761 of 53260.

Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the open_logit = the log of the opening-market chance and market_prob the chance itself, carried together so the fit can bend the market's own curve (short prices are historically underbet and long ones overbet, and log-chance alone cannot correct that); market_x_neural = the market read against Neural. The move from the open to the price NOW is deliberately absent: a race pulled after it ran carries its FINAL price, so it would be reading the answer. career peak and the 12-month peak; speed_rel, speed_best_rel = points below the race's best of Form King's speed figure (100 = class par) read over the last 4 races newest-weighted, and of the best one; finish_speed_rel = the same over finishing speed (last 600 as a share of the run to the 600); last600_rel, to600_rel = the last 600m and the run to it against the class standard, in lengths; settle_share, pos800_share = where the horse settles and where it sits with 800m to run, as a share of its own field (0 = on the lead, 1 = last) read over its recent races and centred on today's field; pos_gain, late_gain = positions made up from settling and from the 400m to the post, on the same share; style_x_tempo = that settling share against the expected tempo, so a backmarker in a slow-run race reads negative; map_vs_habit = how far today's speedmap asks the horse to race from where it usually does; wfa_rel, wfa_best_rel = points below the best of the latest and the best WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean rating of runs within 200m of today's trip; dist_win = the record at the distance as a shrunk win rate, against the race mean; last_vs_lws, best_vs_lws = the latest and the best rated run against the race's Likely Winning Standard (class); trend_slope = rating points per run over the last six runs; starts_log = log of career starts against the race mean (scope); open_logit = log of the opening-market chance (comparison only, never deployed, so Value keeps meaning disagreement with the market).

## Calibration of the deployed model

| rated chance | runners | mean rated | share that won |
|---|---|---|---|
| 0% to 5% | 19993 | 2.5% | 2.4% |
| 5% to 10% | 13331 | 7.3% | 7.2% |
| 10% to 20% | 12819 | 14.2% | 14.6% |
| 20% to 30% | 4601 | 24.2% | 24.3% |
| 30% to 50% | 2189 | 36.7% | 35.6% |
| 50% to 100% | 284 | 57.8% | 58.8% |

## The plans, replayed over 5367 races the fit never saw

Five blocks by date, each priced by a model fitted on the other four. Every bet is chosen against the OPENING market. The two profit columns are the SAME bets on two settlement bases: paid at Betfair SP, which is what betting into the jump gets you, and paid at Form King's AVERAGE OPENING price (avgOpen).

**Read the opening-price column as an upper bound, not a result.** avgOpen is an average of the first prices bookmakers put up, which nobody can take as a single bet, and it is the one price history holds. The live paper book bets at the price on the page when the morning run happens, which is later and sharper than the open, and there the value selections have drifted and lost (see the paper book). Profit is judged at Betfair SP here and at the struck price in the live book; this column only shows how much the open itself was beatable.

| plan | bets | winners | staked | at BSP: profit | return | at the average opening price: profit | return |
|---|---|---|---|---|---|---|---|
| top_pick | 5367 | 1599 | 5367.0 | -63.4 | -1.2% | -102.8 | -1.9% |
| value_flags | 1623 | 504 | 1623.0 | -33.4 | -2.1% | +293.7 | +18.1% |
| value_under_8 | 1608 | 503 | 1608.0 | -33.9 | -2.1% | +296.7 | +18.5% |
| top_pick_to_win_1 | 5350 | 1594 | 3186.2 | +553.5 | +17.4% | -481.8 | -15.1% |
| kelly_quarter | 12047 | 1728 | 9067.2 | +2.3 | +0.0% | +4099.6 | +45.2% |
| value_ev20 | 4956 | 774 | 4956.0 | +279.6 | +5.6% | +3165.9 | +63.9% |
| value_ev05 | 9670 | 1435 | 9670.0 | +239.7 | +2.5% | +3682.4 | +38.1% |
| value_ev10 | 7730 | 1159 | 7730.0 | +155.6 | +2.0% | +3587.3 | +46.4% |
| value_tiered | 9670 | 1435 | 22356.0 | +674.9 | +3.0% | +10435.6 | +46.7% |
| value_ev20_kelly | 4956 | 774 | 6642.3 | +58.3 | +0.9% | +3868.5 | +58.2% |

## Choosing the value rule: value_flags

gap = our chance beats the opening market's by more than the threshold in percentage points (the live rule is gap 0.05). ev = our chance times the average opening price is more than 1 plus the threshold. Each rule is picked on the OLDER 3 fifths of the racing by its return at Betfair SP (at least 30 bets), then shown on the NEWER two fifths it never saw. Returns are one unit a bet, before commission.

| rule | threshold | older: bets | at BSP | at avg opening price | newer: bets | at BSP | at avg opening price |
|---|---|---|---|---|---|---|---|
| gap | 0.02 | 4056 | +0.1% | +15.6% | 2522 | -5.5% | +14.9% |
| gap | 0.03 | 2484 | -1.9% | +18.1% | 1543 | -5.1% | +19.5% |
| gap (live) | 0.05 | 987 | +1.0% | +19.4% | 628 | -7.7% | +16.8% |
| gap | 0.08 | 278 | -5.1% | +16.9% | 191 | -7.6% | +16.5% |
| gap | 0.10 | 112 | -9.4% | -0.7% | 83 | -3.9% | +15.9% |
| ev | 0.05 | 6222 | -0.6% | +32.3% | 3958 | +9.0% | +43.3% |
| ev | 0.10 | 4960 | +1.9% | +42.0% | 3177 | +7.8% | +52.0% |
| ev | 0.20 | 3162 | -3.5% | +53.5% | 2042 | +17.5% | +76.5% |
| ev | 0.30 | 2056 | -0.9% | +66.5% | 1311 | +17.2% | +90.5% |
| ev **(chosen)** | 0.50 | 928 | +11.3% | +106.3% | 599 | +15.0% | +102.6% |

## Choosing the value rule: value_under_8

gap = our chance beats the opening market's by more than the threshold in percentage points (the live rule is gap 0.05). ev = our chance times the average opening price is more than 1 plus the threshold. Each rule is picked on the OLDER 3 fifths of the racing by its return at Betfair SP (at least 30 bets), then shown on the NEWER two fifths it never saw. Returns are one unit a bet, before commission.

| rule | threshold | older: bets | at BSP | at avg opening price | newer: bets | at BSP | at avg opening price |
|---|---|---|---|---|---|---|---|
| gap **(chosen)** | 0.02 | 3358 | +3.0% | +14.7% | 2098 | -6.6% | +8.2% |
| gap | 0.03 | 2306 | -0.9% | +16.9% | 1445 | -5.6% | +15.0% |
| gap (live) | 0.05 | 980 | +0.2% | +19.0% | 619 | -6.4% | +18.5% |
| gap | 0.08 | 278 | -5.1% | +16.9% | 191 | -7.6% | +16.5% |
| gap | 0.10 | 112 | -9.4% | -0.7% | 83 | -3.9% | +15.9% |
| ev | 0.05 | 2784 | +0.3% | +32.8% | 1739 | -0.5% | +31.4% |
| ev | 0.10 | 2247 | -2.3% | +37.1% | 1419 | -2.8% | +33.6% |
| ev | 0.20 | 1446 | -3.8% | +45.3% | 953 | -4.3% | +43.6% |
| ev | 0.30 | 966 | -8.1% | +51.5% | 635 | -7.0% | +49.4% |
| ev | 0.50 | 460 | -7.6% | +78.8% | 302 | -0.8% | +74.0% |

## The strategy search: where, if anywhere, the bets make money

162 strategies: each betting rule (ev = our chance x the opening price must beat 1 by the threshold; gap = our chance must beat the market's by the threshold in points) crossed with a slice of the racing (price band, field size, first starters, metro or not). Every one is scored on the OLDER three fifths of the racing and then on the NEWER two fifths it never saw. One unit a bet, before commission. '±' is one standard error: a return inside about two of them is indistinguishable from luck. With this many tried, some look good on the older racing by chance alone, so only the newer column counts.

- Profitable at Betfair SP in BOTH halves: 55 of 162
- Profitable at the average opening price in BOTH halves: 155 of 162 (upper bound: an average, not a takeable price)
- Profitable at Betfair SP on the newer racing by more than two standard errors, and profitable on the older: 0
- Profitable at the average opening price on the newer racing by more than two standard errors, and on the older: 113


### Best twelve on the older racing at Betfair SP, and how they did on the newer

| rule | slice | older: bets | at BSP | at open | newer: bets | at BSP | at open |
|---|---|---|---|---|---|---|---|
| ev 0.50 | metro | 115 | +64.6% ±58.1% | +128.8% ±67.5% | 74 | -0.2% ±37.3% | +39.0% ±41.2% |
| ev 0.35 | metro | 248 | +59.9% ±35.2% | +126.4% ±43.8% | 162 | +18.9% ±25.9% | +100.6% ±46.4% |
| ev 0.25 | metro | 427 | +43.2% ±25.0% | +86.8% ±28.5% | 273 | +13.7% ±19.6% | +77.6% ±32.6% |
| gap 0.05 | price $8-16 | 89 | +39.6% ±37.8% | +71.6% ±39.7% | 52 | -48.8% ±20.6% | +8.7% ±42.6% |
| ev 0.50 | we rate $10+ | 371 | +33.7% ±28.7% | +139.7% ±49.9% | 224 | +37.0% ±40.1% | +130.0% ±57.5% |
| ev 0.50 | price $16+ | 433 | +28.7% ±25.0% | +148.6% ±44.6% | 263 | +29.3% ±34.6% | +136.9% ±51.3% |
| ev 0.20 | metro | 564 | +28.6% ±19.9% | +64.5% ±22.6% | 341 | +9.3% ±17.2% | +67.0% ±27.7% |
| ev 0.15 | first starters | 154 | +24.4% ±28.3% | +83.0% ±38.0% | 88 | -31.5% ±21.4% | +7.3% ±29.4% |
| ev 0.20 | first starters | 135 | +24.3% ±30.3% | +79.4% ±39.0% | 74 | -24.5% ±24.7% | +16.8% ±33.2% |
| ev 0.50 | our top pick | 160 | +19.2% ±16.3% | +99.8% ±23.5% | 122 | +4.9% ±17.0% | +61.6% ±21.8% |
| ev 0.50 | weekdays | 784 | +18.0% ±14.7% | +116.6% ±24.8% | 548 | +15.3% ±18.3% | +103.7% ±27.0% |
| ev 0.05 | first starters | 254 | +16.7% ±26.3% | +40.3% ±25.2% | 133 | -26.0% ±18.7% | +1.4% ±22.4% |

### Best twelve on the older racing at the opening price, and how they did on the newer

| rule | slice | older: bets | at BSP | at open | newer: bets | at BSP | at open |
|---|---|---|---|---|---|---|---|
| ev 0.50 | price $16+ | 433 | +28.7% ±25.0% | +148.6% ±44.6% | 263 | +29.3% ±34.6% | +136.9% ±51.3% |
| ev 0.50 | field <=8 | 464 | +14.9% ±16.4% | +143.5% ±36.1% | 282 | +15.7% ±18.8% | +103.4% ±31.7% |
| ev 0.50 | we rate $10+ | 371 | +33.7% ±28.7% | +139.7% ±49.9% | 224 | +37.0% ±40.1% | +130.0% ±57.5% |
| ev 0.50 | metro | 115 | +64.6% ±58.1% | +128.8% ±67.5% | 74 | -0.2% ±37.3% | +39.0% ±41.2% |
| ev 0.35 | metro | 248 | +59.9% ±35.2% | +126.4% ±43.8% | 162 | +18.9% ±25.9% | +100.6% ±46.4% |
| ev 0.50 | weekdays | 784 | +18.0% ±14.7% | +116.6% ±24.8% | 548 | +15.3% ±18.3% | +103.7% ±27.0% |
| ev 0.50 | raced horses | 875 | +14.1% ±13.6% | +111.2% ±23.6% | 578 | +15.2% ±17.6% | +104.0% ±26.1% |
| ev 0.50 | we rate <$5 | 246 | +11.1% ±12.1% | +108.6% ±21.1% | 188 | -16.8% ±13.6% | +26.8% ±17.4% |
| ev 0.50 | all | 920 | +12.3% ±13.0% | +108.1% ±22.7% | 599 | +15.0% ±17.1% | +102.6% ±25.3% |
| ev 0.35 | price $16+ | 736 | +12.3% ±18.4% | +107.5% ±31.0% | 434 | +24.4% ±25.9% | +143.2% ±44.6% |
| ev 0.50 | country and provincial | 805 | +4.8% ±12.3% | +105.1% ±24.0% | 525 | +17.2% ±18.8% | +111.6% ±28.3% |
| ev 0.35 | field <=8 | 749 | +6.3% ±12.0% | +100.9% ±24.0% | 425 | +15.2% ±15.2% | +113.4% ±33.7% |

### Beating the morning price, ranked by how far clear of luck on the newer racing

| rule | slice | older: bets | at open | newer: bets | at open | at BSP | standard errors clear |
|---|---|---|---|---|---|---|---|
| ev 0.15 | raced horses | 3772 | +50.4% | 2472 | +67.8% ±12.1% | +15.8% | 5.6 |
| ev 0.15 | all | 3926 | +51.6% | 2560 | +65.7% ±11.7% | +14.2% | 5.6 |
| ev 0.20 | all | 3154 | +53.8% | 2042 | +76.5% ±13.9% | +17.5% | 5.5 |
| ev 0.20 | raced horses | 3019 | +52.7% | 1968 | +78.7% ±14.3% | +19.1% | 5.5 |
| ev 0.10 | all | 4952 | +42.2% | 3177 | +52.0% ±9.8% | +7.8% | 5.3 |
| ev 0.05 | raced horses | 5960 | +32.1% | 3825 | +44.8% ±8.5% | +10.2% | 5.3 |
| ev 0.10 | raced horses | 4750 | +41.5% | 3073 | +53.4% ±10.1% | +8.9% | 5.3 |
| ev 0.05 | all | 6214 | +32.5% | 3958 | +43.3% ±8.2% | +9.0% | 5.3 |
| ev 0.15 | country and provincial | 3196 | +52.2% | 2103 | +68.6% ±13.4% | +16.3% | 5.1 |
| ev 0.15 | weekdays | 3242 | +53.8% | 2236 | +63.8% ±12.7% | +14.4% | 5.0 |
| ev 0.05 | we rate $5-10 | 1934 | +32.7% | 1198 | +51.9% ±10.4% | +12.2% | 5.0 |
| ev 0.20 | country and provincial | 2590 | +51.5% | 1701 | +78.4% ±15.7% | +19.1% | 5.0 |
| ev 0.25 | all | 2575 | +63.1% | 1654 | +79.3% ±15.9% | +17.3% | 5.0 |
| ev 0.25 | raced horses | 2472 | +62.7% | 1593 | +81.8% ±16.5% | +18.7% | 5.0 |
| ev 0.20 | weekdays | 2604 | +55.1% | 1800 | +74.2% ±15.0% | +17.7% | 5.0 |
| ev 0.15 | we rate $5-10 | 1222 | +43.2% | 787 | +69.1% ±14.0% | +14.8% | 4.9 |
| ev 0.10 | country and provincial | 3972 | +43.4% | 2580 | +55.9% ±11.3% | +10.5% | 4.9 |
| ev 0.10 | weekdays | 4022 | +44.9% | 2731 | +53.2% ±10.8% | +10.4% | 4.9 |
| ev 0.05 | country and provincial | 4909 | +34.5% | 3168 | +46.1% ±9.5% | +10.1% | 4.8 |
| ev 0.10 | we rate $5-10 | 1551 | +37.5% | 984 | +56.8% ±11.9% | +9.5% | 4.8 |
