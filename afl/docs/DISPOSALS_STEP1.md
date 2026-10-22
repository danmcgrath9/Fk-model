# AFL disposals, step 1: projection and a stand-in-line backtest

**Stand-in lines, not market lines.** No history of real AFL prop lines has been found. Each line below is built from the player's own recent average, moved by one fixed amount (chosen on the tuning season so a blind over wins half the time), at 1.87 each way. That is roughly how books are said to set them, but real books also see team news, and some lines will be sharper. Treat every ROI here as an upper bound on what real lines would give; the real test is against recorded openers from round 1 2027.

Fitted on 2013-2023 (93,000 player-games). Every choice made on 2024 (9,191). 2025 and 2026 scored once, untouched until then. Rows: established players (5+ games on record), named subs excluded.

## Which projection, chosen on the tuning season

| projection | mean log-likelihood per player-game (higher is better) | spread a |
|---|---|---|
| disposals directly | -2.9639 | 0.026 |
| time on ground x disposals per full game | -2.9655 | 0.026 |
| average of the two | -2.9636 | 0.026 |

Chosen: **average of the two**. Spread: variance = mean + 0.026 x mean squared (negative binomial).

## Accuracy, unseen seasons

| season | player-games | projection miss (avg disposals) | last-10 average | last-5 average | season average |
|---|---|---|---|---|---|
| 2025 | 9,047 | 3.74 | 3.86 | 3.98 | 3.94 |
| 2026 | 9,474 | 3.71 | 3.85 | 3.91 | 3.89 |

## Betting against stand-in lines, unseen seasons

Bet when the projection gives a side more than the stated chance; 1.87 breaks even at 53.5%. ROI is profit per unit staked; the interval resamples whole rounds (90%).

| season | stand-in line | bet when chance over | bets | overs / unders | hit rate | ROI | 90% interval |
|---|---|---|---|---|---|---|---|
| 2025 | last-10 average | 53.5% | 6,731 | 3,247 / 3,484 | 60.3% | +12.9% | +11.0% to +14.8% |
| 2025 | last-10 average | 56.0% | 5,302 | 2,624 / 2,678 | 62.4% | +16.6% | +14.4% to +18.9% |
| 2025 | last-10 average | 60.0% | 3,310 | 1,794 / 1,516 | 64.7% | +21.1% | +18.3% to +23.9% |
| 2025 | last-5 average | 53.5% | 7,335 | 3,472 / 3,863 | 63.9% | +19.6% | +17.9% to +21.3% |
| 2025 | last-5 average | 56.0% | 6,175 | 2,948 / 3,227 | 65.2% | +22.0% | +20.0% to +24.0% |
| 2025 | last-5 average | 60.0% | 4,433 | 2,218 / 2,215 | 67.9% | +26.9% | +24.2% to +29.6% |
| 2025 | season average | 53.5% | 6,604 | 2,796 / 3,808 | 61.8% | +15.6% | +12.9% to +18.5% |
| 2025 | season average | 56.0% | 5,333 | 2,283 / 3,050 | 63.5% | +18.8% | +15.9% to +21.9% |
| 2025 | season average | 60.0% | 3,524 | 1,611 / 1,913 | 67.5% | +26.2% | +22.7% to +29.7% |
| 2026 | last-10 average | 53.5% | 7,222 | 3,240 / 3,982 | 60.8% | +13.7% | +11.5% to +15.9% |
| 2026 | last-10 average | 56.0% | 5,755 | 2,614 / 3,141 | 62.4% | +16.6% | +14.3% to +18.9% |
| 2026 | last-10 average | 60.0% | 3,739 | 1,821 / 1,918 | 65.4% | +22.4% | +19.6% to +25.1% |
| 2026 | last-5 average | 53.5% | 7,712 | 3,316 / 4,396 | 62.9% | +17.6% | +15.6% to +19.4% |
| 2026 | last-5 average | 56.0% | 6,538 | 2,778 / 3,760 | 63.8% | +19.4% | +17.4% to +21.3% |
| 2026 | last-5 average | 60.0% | 4,768 | 2,043 / 2,725 | 66.3% | +23.9% | +21.7% to +26.0% |
| 2026 | season average | 53.5% | 6,928 | 2,707 / 4,221 | 61.6% | +15.1% | +12.6% to +17.8% |
| 2026 | season average | 56.0% | 5,606 | 2,136 / 3,470 | 63.2% | +18.1% | +15.3% to +21.0% |
| 2026 | season average | 60.0% | 3,708 | 1,425 / 2,283 | 66.5% | +24.3% | +20.9% to +27.7% |

Shift applied to each stand-in (chosen on 2024): last-10 average +0.05, last-5 average +0.05, season average +0.05.

A blind bet on every over and every under against the same lines, unseen seasons (a line method with no lean sits near 50/50):

| season | stand-in line | under hit rate | over hit rate |
|---|---|---|---|
| 2025 | last-10 average | 49.4% | 50.6% |
| 2025 | last-5 average | 50.2% | 49.8% |
| 2025 | season average | 51.1% | 48.9% |
| 2026 | last-10 average | 49.6% | 50.4% |
| 2026 | last-5 average | 50.7% | 49.3% |
| 2026 | season average | 52.0% | 48.0% |

## Where the projection disagrees with a last-10 line, and what happened (both seasons)

| projection minus last-10 average | player-games | projection gap | actual minus last-10 | went over the line |
|---|---|---|---|---|
| (-30.0, -3.0] | 188 | -3.67 | -4.14 | 28.2% |
| (-3.0, -1.5] | 1,379 | -2.03 | -1.68 | 36.3% |
| (-1.5, -0.5] | 3,403 | -0.93 | -0.95 | 40.6% |
| (-0.5, 0.5] | 5,748 | +0.01 | -0.11 | 47.5% |
| (0.5, 1.5] | 4,456 | +0.94 | +0.74 | 54.7% |
| (1.5, 3.0] | 2,481 | +2.07 | +1.77 | 63.6% |
| (3.0, 30.0] | 866 | +4.11 | +3.78 | 78.1% |

## By line size, 56%+ bets against last-10 lines (both seasons)

| line | bets | hit rate | ROI | 90% interval |
|---|---|---|---|---|
| under 15 | 5,760 | 63.8% | +19.4% | +17.3% to +21.3% |
| 15.5 to 19.5 | 2,646 | 61.0% | +14.0% | +10.7% to +17.3% |
| 20.5 to 24.5 | 1,540 | 61.9% | +15.7% | +11.7% to +19.7% |
| 25.5 and up | 1,111 | 58.8% | +9.9% | +5.8% to +14.1% |

## Calibration: projected chance of going over a last-10 line against what happened (both seasons)

| projected chance over | player-games | average projected | actually over |
|---|---|---|---|
| (0.0, 0.3] | 419 | 27.0% | 28.9% |
| (0.3, 0.4] | 3,015 | 36.1% | 38.0% |
| (0.4, 0.45] | 3,043 | 42.6% | 43.2% |
| (0.45, 0.5] | 3,321 | 47.5% | 47.6% |
| (0.5, 0.55] | 2,981 | 52.3% | 52.6% |
| (0.55, 0.6] | 2,127 | 57.4% | 56.6% |
| (0.6, 0.7] | 2,250 | 64.2% | 62.6% |
| (0.7, 1.0] | 1,365 | 78.1% | 74.4% |

## What the models lean on (share of gain, top 10)

| direct model | | time on ground model | | per-full-game rate model | |
|---|---|---|---|---|---|
| D_ewm | 65.8% | TOG_l10 | 49.4% | rate_l10 | 50.1% |
| rate_l10 | 8.5% | TOG_l3 | 23.7% | rate_l20 | 27.1% |
| D_l10 | 5.9% | TOG_last | 9.2% | rate_l5 | 11.4% |
| D_season | 2.6% | exp_blowout | 1.4% | D_season | 1.5% |
| rate_l20 | 2.4% | ITC_pg | 1.2% | D_ewm | 1.0% |
| share_of_pool | 1.5% | M_pg | 1.1% | venue_rel | 0.7% |
| rate_l5 | 1.0% | OP_pg | 0.8% | team_pool_D | 0.5% |
| venue_rel | 0.7% | opp_T_l8 | 0.7% | league_game_D | 0.4% |
| team_pool_D | 0.6% | outs_D | 0.7% | exp_margin | 0.4% |
| D_l20 | 0.6% | round_no | 0.6% | opp_conc_D_l8 | 0.3% |
