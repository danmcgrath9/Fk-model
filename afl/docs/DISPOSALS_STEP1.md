# AFL disposals, step 1: projection and a stand-in-line backtest

**Stand-in lines, not market lines.** No history of real AFL prop lines has been found. Each line below is built from the player's own recent average, moved by one fixed amount (chosen on the tuning season so a blind over wins half the time), at 1.87 each way. That is roughly how books are said to set them, but real books also see team news, and some lines will be sharper. Treat every ROI here as an upper bound on what real lines would give; the real test is against recorded openers from round 1 2027.

Fitted on 2013-2023 (93,000 player-games). Every choice made on 2024 (9,191). 2025 and 2026 scored once, untouched until then. Rows: established players (5+ games on record), named subs excluded.

## Which projection, chosen on the tuning season

| projection | mean log-likelihood per player-game (higher is better) | spread a |
|---|---|---|
| disposals directly | -2.9646 | 0.026 |
| time on ground x disposals per full game | -2.9662 | 0.026 |
| average of the two | -2.9645 | 0.026 |

Chosen: **average of the two**. Spread: variance = mean + 0.026 x mean squared (negative binomial).

## Accuracy, unseen seasons

| season | player-games | projection miss (avg disposals) | last-10 average | last-5 average | season average |
|---|---|---|---|---|---|
| 2025 | 9,047 | 3.74 | 3.86 | 3.98 | 3.94 |
| 2026 | 9,474 | 3.72 | 3.85 | 3.91 | 3.89 |

## Betting against stand-in lines, unseen seasons

Bet when the projection gives a side more than the stated chance; 1.87 breaks even at 53.5%. ROI is profit per unit staked; the interval resamples whole rounds (90%).

| season | stand-in line | bet when chance over | bets | overs / unders | hit rate | ROI | 90% interval |
|---|---|---|---|---|---|---|---|
| 2025 | last-10 average | 53.5% | 6,742 | 3,331 / 3,411 | 60.2% | +12.5% | +10.7% to +14.4% |
| 2025 | last-10 average | 56.0% | 5,275 | 2,667 / 2,608 | 62.0% | +16.0% | +13.7% to +18.4% |
| 2025 | last-10 average | 60.0% | 3,249 | 1,792 / 1,457 | 64.7% | +20.9% | +18.3% to +23.6% |
| 2025 | last-5 average | 53.5% | 7,284 | 3,493 / 3,791 | 63.8% | +19.4% | +17.5% to +21.3% |
| 2025 | last-5 average | 56.0% | 6,122 | 2,963 / 3,159 | 65.0% | +21.6% | +19.4% to +23.8% |
| 2025 | last-5 average | 60.0% | 4,388 | 2,239 / 2,149 | 67.4% | +26.0% | +23.4% to +28.6% |
| 2025 | season average | 53.5% | 6,574 | 2,842 / 3,732 | 61.9% | +15.7% | +13.1% to +18.8% |
| 2025 | season average | 56.0% | 5,283 | 2,299 / 2,984 | 63.5% | +18.8% | +15.7% to +22.2% |
| 2025 | season average | 60.0% | 3,475 | 1,620 / 1,855 | 67.4% | +26.0% | +22.5% to +29.5% |
| 2026 | last-10 average | 53.5% | 7,216 | 3,211 / 4,005 | 60.7% | +13.6% | +11.4% to +15.7% |
| 2026 | last-10 average | 56.0% | 5,751 | 2,603 / 3,148 | 62.4% | +16.6% | +14.0% to +19.4% |
| 2026 | last-10 average | 60.0% | 3,674 | 1,804 / 1,870 | 65.3% | +22.2% | +19.4% to +24.9% |
| 2026 | last-5 average | 53.5% | 7,682 | 3,284 / 4,398 | 62.6% | +17.1% | +15.4% to +18.8% |
| 2026 | last-5 average | 56.0% | 6,507 | 2,780 / 3,727 | 64.0% | +19.7% | +17.6% to +21.7% |
| 2026 | last-5 average | 60.0% | 4,706 | 2,023 / 2,683 | 66.3% | +24.0% | +21.9% to +26.0% |
| 2026 | season average | 53.5% | 6,904 | 2,665 / 4,239 | 61.8% | +15.5% | +13.2% to +18.1% |
| 2026 | season average | 56.0% | 5,582 | 2,117 / 3,465 | 63.2% | +18.1% | +15.2% to +21.2% |
| 2026 | season average | 60.0% | 3,666 | 1,406 / 2,260 | 65.9% | +23.2% | +19.7% to +26.6% |

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
| (-30.0, -3.0] | 174 | -3.66 | -4.31 | 28.7% |
| (-3.0, -1.5] | 1,331 | -2.02 | -1.70 | 36.4% |
| (-1.5, -0.5] | 3,392 | -0.92 | -0.89 | 40.8% |
| (-0.5, 0.5] | 5,777 | +0.01 | -0.12 | 47.3% |
| (0.5, 1.5] | 4,502 | +0.94 | +0.74 | 55.0% |
| (1.5, 3.0] | 2,491 | +2.07 | +1.66 | 62.7% |
| (3.0, 30.0] | 854 | +4.08 | +3.84 | 78.7% |

## By line size, 56%+ bets against last-10 lines (both seasons)

| line | bets | hit rate | ROI | 90% interval |
|---|---|---|---|---|
| under 15 | 5,752 | 63.7% | +19.1% | +16.9% to +21.1% |
| 15.5 to 19.5 | 2,637 | 61.3% | +14.6% | +11.3% to +17.9% |
| 20.5 to 24.5 | 1,544 | 60.9% | +14.0% | +9.9% to +17.9% |
| 25.5 and up | 1,093 | 58.5% | +9.3% | +5.3% to +13.6% |

## Calibration: projected chance of going over a last-10 line against what happened (both seasons)

| projected chance over | player-games | average projected | actually over |
|---|---|---|---|
| (0.0, 0.3] | 386 | 27.0% | 26.9% |
| (0.3, 0.4] | 2,941 | 36.2% | 38.3% |
| (0.4, 0.45] | 3,069 | 42.6% | 43.5% |
| (0.45, 0.5] | 3,356 | 47.5% | 47.2% |
| (0.5, 0.55] | 3,036 | 52.4% | 52.3% |
| (0.55, 0.6] | 2,137 | 57.4% | 56.9% |
| (0.6, 0.7] | 2,234 | 64.2% | 62.5% |
| (0.7, 1.0] | 1,362 | 78.1% | 74.0% |

## What the models lean on (share of gain, top 10)

| direct model | | time on ground model | | per-full-game rate model | |
|---|---|---|---|---|---|
| D_ewm | 67.7% | TOG_l10 | 50.9% | rate_l10 | 49.4% |
| rate_l10 | 8.7% | TOG_l3 | 24.9% | rate_l20 | 26.1% |
| D_l10 | 6.0% | TOG_last | 9.4% | rate_l5 | 11.9% |
| D_season | 2.6% | ITC_pg | 1.1% | D_season | 1.6% |
| rate_l20 | 2.3% | M_pg | 1.1% | D_ewm | 1.0% |
| share_of_pool | 1.4% | OP_pg | 0.8% | venue_rel | 0.7% |
| rate_l5 | 1.1% | outs_D | 0.7% | team_pool_D | 0.5% |
| D_l20 | 0.6% | D_sd10 | 0.6% | league_game_D | 0.5% |
| venue_rel | 0.6% | round_no | 0.5% | exp_margin | 0.4% |
| team_pool_D | 0.6% | games_prior | 0.5% | opp_conc_D_l8 | 0.3% |
