# NBL player props, step 1: projections and a stand-in-line backtest

**Every betting result below is against STAND-IN lines, not real ones.** No NBL prop lines are held yet (The Odds API key is not set up, and its NBL prop history may start only in September 2026). A stand-in line is the player's own recent average moved by one fixed amount, chosen on 2022-23 so a blind over wins half the time, at 1.87 each way. Books are said to set lines from recent averages, but they also see team news and some will price better, so these figures are an upper bound on a real edge, and may be far above it.

Which games count: the player dressed and played (an unplayed prop is void), 5+ earlier games, and he usually plays 12+ minutes. Betting tables keep only lines a book would post: at least points 7.5, rebounds 2.5, assists 1.5, threes 0.5, points+rebounds+assists 11.5 (this floor was set after looking at the confirm seasons and before the final check). Seasons are named by the year they start. Fit 2016-2021, tune 2022, confirm 2023 and 2024, final check 2025 and 2026 (2026 = this season to 18 Oct 2026).

## Projection accuracy

Minutes, tuning season: our minutes model misses by 4.26 minutes a game, the player's decayed average by 4.63.

| market | model chosen on 2022 | miss per player-game, 2022: ours | last-10 average | spread (NB a) |
|---|---|---|---|---|
| points | blend | 4.37 | 4.48 | 0.301 |
| rebounds | struct | 1.84 | 1.90 | 0.098 |
| assists | struct | 1.17 | 1.22 | 0.108 |
| threes | direct | 0.84 | 0.85 | 0.156 |
| points+rebounds+assists | struct | 5.65 | 5.82 | 0.186 |

| season | rows | points: ours / last 10 | rebounds: ours / last 10 | assists: ours / last 10 | threes: ours / last 10 | points+rebounds+assists: ours / last 10 |
|---|---|---|---|---|---|---|
| 2023 | 2398 | 4.37 / 4.53 | 1.87 / 1.95 | 1.15 / 1.18 | 0.82 / 0.82 | 5.52 / 5.78 |
| 2024 | 2522 | 4.69 / 4.82 | 1.81 / 1.89 | 1.19 / 1.21 | 0.86 / 0.89 | 5.89 / 6.10 |
| 2025 | 2693 | 4.57 / 4.74 | 1.85 / 1.89 | 1.26 / 1.30 | 0.87 / 0.88 | 5.80 / 6.01 |
| 2026 | 450 | 5.01 / 5.25 | 1.89 / 1.99 | 1.33 / 1.34 | 0.98 / 0.99 | 6.36 / 6.68 |

## Is the over chance honest? (confirm seasons, against the last-10 stand-in)

| market | our over chance | bets | over won |
|---|---|---|---|
| points | 0% to 30% | 358 | 29% |
| points | 30% to 40% | 1256 | 42% |
| points | 40% to 50% | 1760 | 50% |
| points | 50% to 60% | 907 | 58% |
| points | 60% to 70% | 432 | 62% |
| points | 70% to 100% | 207 | 72% |
| rebounds | 0% to 30% | 351 | 27% |
| rebounds | 30% to 40% | 846 | 37% |
| rebounds | 40% to 50% | 1351 | 46% |
| rebounds | 50% to 60% | 1259 | 56% |
| rebounds | 60% to 70% | 777 | 62% |
| rebounds | 70% to 100% | 336 | 73% |
| assists | 0% to 30% | 225 | 28% |
| assists | 30% to 40% | 620 | 39% |
| assists | 40% to 50% | 1101 | 45% |
| assists | 50% to 60% | 1188 | 53% |
| assists | 60% to 70% | 1061 | 64% |
| assists | 70% to 100% | 725 | 79% |
| threes | 0% to 30% | 521 | 27% |
| threes | 30% to 40% | 991 | 32% |
| threes | 40% to 50% | 1184 | 44% |
| threes | 50% to 60% | 1038 | 55% |
| threes | 60% to 70% | 494 | 58% |
| threes | 70% to 100% | 692 | 95% |
| points+rebounds+assists | 0% to 30% | 350 | 28% |
| points+rebounds+assists | 30% to 40% | 1052 | 42% |
| points+rebounds+assists | 40% to 50% | 1728 | 49% |
| points+rebounds+assists | 50% to 60% | 996 | 58% |
| points+rebounds+assists | 60% to 70% | 516 | 64% |
| points+rebounds+assists | 70% to 100% | 278 | 75% |

## Betting against stand-in lines

Bet a side when our chance of it is at least the stated figure; 1.87 breaks even at 53.5%. ROI per unit staked; the 90% interval comes from resampling whole rounds (weeks). Confirm seasons first, then the final check.

| market | stand-in | seasons | bet at | bets | overs / unders | hit rate | ROI | 90% interval |
|---|---|---|---|---|---|---|---|---|
| points | last 10 | 2023-2024 | 56% | 2,096 | 125 / 1,971 | 57.6% | +7.8% | +4.5% to +11.1% |
| points | last 10 | 2023-2024 | 60% | 1,379 | 47 / 1,332 | 60.6% | +13.2% | +9.5% to +17.0% |
| points | last 10 | 2025-2026 | 56% | 1,350 | 108 / 1,242 | 59.6% | +11.4% | +7.3% to +15.4% |
| points | last 10 | 2025-2026 | 60% | 873 | 28 / 845 | 62.5% | +17.0% | +12.0% to +21.7% |
| points | last 5 | 2023-2024 | 56% | 2,117 | 232 / 1,885 | 61.6% | +15.2% | +12.5% to +18.0% |
| points | last 5 | 2023-2024 | 60% | 1,556 | 107 / 1,449 | 63.2% | +18.3% | +15.3% to +21.6% |
| points | last 5 | 2025-2026 | 56% | 1,404 | 230 / 1,174 | 62.0% | +15.9% | +11.8% to +20.0% |
| points | last 5 | 2025-2026 | 60% | 972 | 96 / 876 | 62.2% | +16.4% | +11.9% to +21.0% |
| rebounds | last 10 | 2023-2024 | 56% | 2,501 | 857 / 1,644 | 63.6% | +18.9% | +16.2% to +21.7% |
| rebounds | last 10 | 2023-2024 | 60% | 1,665 | 512 / 1,153 | 66.5% | +24.4% | +21.1% to +27.8% |
| rebounds | last 10 | 2025-2026 | 56% | 1,532 | 556 / 976 | 62.2% | +16.3% | +12.7% to +19.7% |
| rebounds | last 10 | 2025-2026 | 60% | 1,010 | 323 / 687 | 65.0% | +21.5% | +16.7% to +26.3% |
| rebounds | last 5 | 2023-2024 | 56% | 2,788 | 717 / 2,071 | 65.3% | +22.1% | +19.4% to +24.7% |
| rebounds | last 5 | 2023-2024 | 60% | 2,038 | 430 / 1,608 | 67.4% | +26.0% | +22.5% to +29.1% |
| rebounds | last 5 | 2025-2026 | 56% | 1,746 | 520 / 1,226 | 64.5% | +20.7% | +17.0% to +24.4% |
| rebounds | last 5 | 2025-2026 | 60% | 1,292 | 336 / 956 | 67.0% | +25.3% | +21.4% to +29.6% |
| assists | last 10 | 2023-2024 | 56% | 1,647 | 481 / 1,166 | 61.4% | +14.9% | +11.2% to +18.8% |
| assists | last 10 | 2023-2024 | 60% | 1,069 | 271 / 798 | 64.3% | +20.2% | +15.8% to +24.6% |
| assists | last 10 | 2025-2026 | 56% | 1,147 | 366 / 781 | 62.3% | +16.6% | +12.9% to +20.2% |
| assists | last 10 | 2025-2026 | 60% | 726 | 190 / 536 | 64.5% | +20.5% | +15.1% to +25.4% |
| assists | last 5 | 2023-2024 | 56% | 1,962 | 488 / 1,474 | 62.9% | +17.6% | +14.3% to +20.7% |
| assists | last 5 | 2023-2024 | 60% | 1,457 | 319 / 1,138 | 66.0% | +23.3% | +19.9% to +26.7% |
| assists | last 5 | 2025-2026 | 56% | 1,329 | 329 / 1,000 | 62.6% | +17.1% | +13.5% to +20.4% |
| assists | last 5 | 2025-2026 | 60% | 970 | 185 / 785 | 64.5% | +20.7% | +17.0% to +23.9% |
| threes | last 10 | 2023-2024 | 56% | 2,966 | 952 / 2,014 | 64.5% | +20.5% | +17.7% to +23.4% |
| threes | last 10 | 2023-2024 | 60% | 2,103 | 591 / 1,512 | 66.9% | +25.1% | +22.0% to +28.2% |
| threes | last 10 | 2025-2026 | 56% | 1,898 | 676 / 1,222 | 64.8% | +21.1% | +17.3% to +24.5% |
| threes | last 10 | 2025-2026 | 60% | 1,372 | 471 / 901 | 66.5% | +24.3% | +19.8% to +28.7% |
| threes | last 5 | 2023-2024 | 56% | 3,149 | 939 / 2,210 | 66.4% | +24.2% | +21.7% to +26.8% |
| threes | last 5 | 2023-2024 | 60% | 2,427 | 640 / 1,787 | 69.4% | +29.8% | +26.8% to +32.7% |
| threes | last 5 | 2025-2026 | 56% | 2,029 | 686 / 1,343 | 67.1% | +25.5% | +22.1% to +28.4% |
| threes | last 5 | 2025-2026 | 60% | 1,603 | 516 / 1,087 | 68.9% | +28.8% | +25.2% to +32.1% |
| points+rebounds+assists | last 10 | 2023-2024 | 56% | 2,080 | 305 / 1,775 | 59.1% | +10.6% | +7.7% to +13.8% |
| points+rebounds+assists | last 10 | 2023-2024 | 60% | 1,323 | 165 / 1,158 | 62.9% | +17.6% | +14.3% to +21.2% |
| points+rebounds+assists | last 10 | 2025-2026 | 56% | 1,336 | 255 / 1,081 | 61.0% | +14.1% | +10.7% to +17.6% |
| points+rebounds+assists | last 10 | 2025-2026 | 60% | 817 | 122 / 695 | 63.9% | +19.5% | +15.5% to +23.6% |
| points+rebounds+assists | last 5 | 2023-2024 | 56% | 2,311 | 375 / 1,936 | 61.3% | +14.6% | +12.2% to +17.2% |
| points+rebounds+assists | last 5 | 2023-2024 | 60% | 1,612 | 193 / 1,419 | 64.0% | +19.6% | +16.9% to +22.4% |
| points+rebounds+assists | last 5 | 2025-2026 | 56% | 1,474 | 353 / 1,121 | 62.3% | +16.6% | +13.1% to +20.1% |
| points+rebounds+assists | last 5 | 2025-2026 | 60% | 1,002 | 189 / 813 | 65.4% | +22.2% | +18.8% to +25.7% |

Blind check: with the shift chosen on 2022, how often the over won in each later season (50% means the stand-in is fair):

| market | stand-in | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|
| points | last 10 | 50% | 50% | 50% | 49% |
| points | last 5 | 51% | 50% | 51% | 52% |
| rebounds | last 10 | 49% | 51% | 51% | 47% |
| rebounds | last 5 | 47% | 48% | 48% | 49% |
| assists | last 10 | 53% | 56% | 55% | 57% |
| assists | last 5 | 53% | 54% | 53% | 56% |
| threes | last 10 | 50% | 51% | 52% | 53% |
| threes | last 5 | 49% | 50% | 50% | 51% |
| points+rebounds+assists | last 10 | 50% | 51% | 51% | 50% |
| points+rebounds+assists | last 5 | 51% | 51% | 51% | 54% |

Shifts (chosen on 2022): points last 10 -0.55, points last 5 -0.75, rebounds last 10 -0.25, rebounds last 5 -0.15, assists last 10 -0.35, assists last 5 -0.35, threes last 10 -0.15, threes last 5 -0.15, points+rebounds+assists last 10 -0.75, points+rebounds+assists last 5 -0.75.

**Why the table above flatters us.** A line set at a rounded recent average and offered at 1.87 both ways is lopsided for small counts (a player averaging 1.4 threes faces a 1.5 line he clears well under half the time), and any distribution beats it. Real books shade the price on a lopsided line. The next table is the fairer test.

## Betting against a naive stand-in book (the fairer test)

Same stand-in lines, but the book prices both sides itself from the player's recent average alone (negative binomial around the average, its scale and spread fitted on 2022), with a 7% overround. This is a book that reads form the plain way. We bet a side when our chance times its price is at least 1 + the stated edge. A real book that also reads team news, minutes and matchups will be harder to beat than this one.

| market | stand-in | seasons | edge at least | bets | overs / unders | hit rate | average price | ROI | 90% interval |
|---|---|---|---|---|---|---|---|---|---|
| points | last 10 | 2023-2024 | 3% | 1,567 | 504 / 1,063 | 61.9% | 1.81 | +12.5% | +8.6% to +16.6% |
| points | last 10 | 2023-2024 | 8% | 975 | 294 / 681 | 64.4% | 1.81 | +16.5% | +11.3% to +21.3% |
| points | last 10 | 2025-2026 | 3% | 1,129 | 461 / 668 | 62.5% | 1.84 | +14.9% | +10.5% to +19.3% |
| points | last 10 | 2025-2026 | 8% | 696 | 284 / 412 | 65.1% | 1.85 | +20.2% | +15.1% to +25.3% |
| points | last 5 | 2023-2024 | 3% | 1,922 | 659 / 1,263 | 64.4% | 1.82 | +17.2% | +14.6% to +19.8% |
| points | last 5 | 2023-2024 | 8% | 1,386 | 449 / 937 | 67.2% | 1.81 | +21.6% | +18.4% to +25.0% |
| points | last 5 | 2025-2026 | 3% | 1,334 | 572 / 762 | 63.8% | 1.85 | +18.4% | +15.0% to +21.8% |
| points | last 5 | 2025-2026 | 8% | 968 | 413 / 555 | 65.0% | 1.85 | +20.4% | +16.8% to +24.1% |
| rebounds | last 10 | 2023-2024 | 3% | 2,524 | 1,317 / 1,207 | 62.2% | 1.90 | +17.2% | +14.3% to +20.1% |
| rebounds | last 10 | 2023-2024 | 8% | 1,845 | 984 / 861 | 63.8% | 1.91 | +21.0% | +17.5% to +24.5% |
| rebounds | last 10 | 2025-2026 | 3% | 1,613 | 914 / 699 | 59.0% | 1.92 | +11.6% | +8.3% to +14.7% |
| rebounds | last 10 | 2025-2026 | 8% | 1,141 | 654 / 487 | 59.6% | 1.94 | +13.5% | +8.8% to +18.1% |
| rebounds | last 5 | 2023-2024 | 3% | 2,781 | 1,387 / 1,394 | 62.2% | 1.93 | +18.2% | +15.4% to +21.1% |
| rebounds | last 5 | 2023-2024 | 8% | 2,224 | 1,135 / 1,089 | 63.7% | 1.95 | +21.8% | +18.6% to +25.2% |
| rebounds | last 5 | 2025-2026 | 3% | 1,806 | 973 / 833 | 61.8% | 1.94 | +17.8% | +14.3% to +21.5% |
| rebounds | last 5 | 2025-2026 | 8% | 1,442 | 804 / 638 | 63.2% | 1.96 | +21.6% | +17.6% to +25.9% |
| assists | last 10 | 2023-2024 | 3% | 1,557 | 629 / 928 | 59.3% | 1.91 | +11.5% | +8.3% to +15.0% |
| assists | last 10 | 2023-2024 | 8% | 1,087 | 421 / 666 | 60.3% | 1.92 | +13.7% | +9.3% to +18.3% |
| assists | last 10 | 2025-2026 | 3% | 1,092 | 446 / 646 | 60.3% | 1.92 | +15.0% | +10.1% to +19.6% |
| assists | last 10 | 2025-2026 | 8% | 759 | 311 / 448 | 64.8% | 1.93 | +25.1% | +20.4% to +29.5% |
| assists | last 5 | 2023-2024 | 3% | 1,904 | 699 / 1,205 | 62.0% | 1.88 | +15.2% | +11.8% to +18.4% |
| assists | last 5 | 2023-2024 | 8% | 1,513 | 547 / 966 | 64.1% | 1.89 | +19.6% | +16.2% to +23.0% |
| assists | last 5 | 2025-2026 | 3% | 1,343 | 502 / 841 | 62.1% | 1.90 | +17.1% | +13.1% to +21.4% |
| assists | last 5 | 2025-2026 | 8% | 1,035 | 375 / 660 | 64.5% | 1.91 | +22.4% | +18.2% to +26.6% |
| threes | last 10 | 2023-2024 | 3% | 2,889 | 1,968 / 921 | 52.8% | 2.43 | +16.9% | +12.6% to +21.2% |
| threes | last 10 | 2023-2024 | 8% | 2,251 | 1,609 / 642 | 53.0% | 2.55 | +22.3% | +17.0% to +27.4% |
| threes | last 10 | 2025-2026 | 3% | 1,884 | 1,333 / 551 | 54.0% | 2.33 | +16.4% | +11.6% to +21.3% |
| threes | last 10 | 2025-2026 | 8% | 1,445 | 1,080 / 365 | 52.9% | 2.46 | +19.9% | +14.3% to +25.7% |
| threes | last 5 | 2023-2024 | 3% | 3,195 | 2,077 / 1,118 | 57.1% | 2.53 | +30.0% | +26.2% to +33.5% |
| threes | last 5 | 2023-2024 | 8% | 2,631 | 1,799 / 832 | 56.9% | 2.66 | +36.0% | +31.8% to +40.0% |
| threes | last 5 | 2025-2026 | 3% | 2,043 | 1,375 / 668 | 58.6% | 2.47 | +33.1% | +28.1% to +37.8% |
| threes | last 5 | 2025-2026 | 8% | 1,718 | 1,214 / 504 | 57.9% | 2.58 | +37.2% | +31.9% to +42.5% |
| points+rebounds+assists | last 10 | 2023-2024 | 3% | 1,832 | 680 / 1,152 | 62.3% | 1.83 | +14.5% | +11.2% to +18.0% |
| points+rebounds+assists | last 10 | 2023-2024 | 8% | 1,206 | 454 / 752 | 65.0% | 1.84 | +19.7% | +15.6% to +24.4% |
| points+rebounds+assists | last 10 | 2025-2026 | 3% | 1,261 | 585 / 676 | 64.1% | 1.86 | +19.3% | +15.2% to +23.6% |
| points+rebounds+assists | last 10 | 2025-2026 | 8% | 858 | 410 / 448 | 65.5% | 1.87 | +22.3% | +17.2% to +27.5% |
| points+rebounds+assists | last 5 | 2023-2024 | 3% | 2,106 | 747 / 1,359 | 64.0% | 1.83 | +17.0% | +14.2% to +19.7% |
| points+rebounds+assists | last 5 | 2023-2024 | 8% | 1,612 | 570 / 1,042 | 65.9% | 1.82 | +20.5% | +17.5% to +23.4% |
| points+rebounds+assists | last 5 | 2025-2026 | 3% | 1,456 | 677 / 779 | 64.6% | 1.86 | +20.5% | +17.5% to +23.6% |
| points+rebounds+assists | last 5 | 2025-2026 | 8% | 1,092 | 518 / 574 | 66.3% | 1.86 | +23.7% | +19.8% to +27.5% |

## Where the edge comes from (naive book, last-10 stand-in, edge 3%)

If shuffled projections also won, the test would be broken. If a plain projection (half the last-10 average, half the decayed per-minute rate x usual minutes) wins nearly as much, the edge is mostly "regress the recent average", which a real book may already do.

| market | seasons | ours: bets, ROI | shuffled projections: bets, ROI | plain projection: bets, ROI |
|---|---|---|---|---|
| points | 2023-2024 | 1,567, +12.5% | 2,677, -2.7% | 308, +20.9% |
| points | 2025-2026 | 1,129, +14.9% | 1,838, -1.7% | 216, +32.9% |
| rebounds | 2023-2024 | 2,524, +17.2% | 3,491, -5.2% | 1,070, +14.6% |
| rebounds | 2025-2026 | 1,613, +11.6% | 2,329, -2.8% | 620, +14.1% |
| assists | 2023-2024 | 1,557, +11.5% | 2,302, -8.8% | 499, +14.5% |
| assists | 2025-2026 | 1,092, +15.0% | 1,676, -7.8% | 267, +30.3% |
| threes | 2023-2024 | 2,889, +16.9% | 3,805, +3.2% | 1,270, +29.6% |
| threes | 2025-2026 | 1,884, +16.4% | 2,394, +5.5% | 787, +29.2% |
| points+rebounds+assists | 2023-2024 | 1,832, +14.5% | 2,896, -2.1% | 493, +20.1% |
| points+rebounds+assists | 2025-2026 | 1,261, +19.3% | 2,012, -5.5% | 326, +19.7% |

## By line size and side (naive book, last-10 stand-in, edge 3%, all seasons shown above)

| market | line | side | bets | hit rate | ROI | 90% interval |
|---|---|---|---|---|---|---|
| points | 7.5 to 10.5 | over | 616 | 64.1% | +33.0% | +26.7% to +39.5% |
| points | 7.5 to 10.5 | under | 651 | 63.6% | +8.2% | +2.8% to +13.7% |
| points | 10.5 to 14.5 | over | 284 | 61.6% | +30.1% | +20.0% to +40.5% |
| points | 10.5 to 14.5 | under | 501 | 58.5% | -2.1% | -7.5% to +3.2% |
| points | 14.5 to 34.5 | over | 65 | 58.5% | +25.1% | +2.5% to +45.6% |
| points | 14.5 to 34.5 | under | 579 | 62.3% | +3.0% | -2.0% to +8.3% |
| rebounds | 2.5 to 3.5 | over | 1,655 | 58.2% | +16.2% | +12.7% to +19.5% |
| rebounds | 2.5 to 3.5 | under | 612 | 64.4% | +17.0% | +11.3% to +23.0% |
| rebounds | 3.5 to 4.5 | over | 308 | 60.1% | +23.0% | +13.4% to +32.6% |
| rebounds | 3.5 to 4.5 | under | 356 | 65.4% | +14.1% | +6.9% to +21.3% |
| rebounds | 4.5 to 11.5 | over | 268 | 57.8% | +19.0% | +9.2% to +29.9% |
| rebounds | 4.5 to 11.5 | under | 938 | 62.9% | +8.2% | +4.7% to +12.2% |
| assists | 1.5 to 2.5 | over | 935 | 58.3% | +16.8% | +11.3% to +21.9% |
| assists | 1.5 to 2.5 | under | 814 | 62.0% | +15.6% | +10.6% to +20.5% |
| assists | 2.5 to 9.5 | over | 140 | 60.0% | +21.5% | +6.1% to +37.5% |
| assists | 2.5 to 9.5 | under | 760 | 59.1% | +3.8% | -0.8% to +8.6% |
| threes | 0.5 to 1.5 | over | 3,123 | 48.5% | +19.8% | +15.6% to +24.3% |
| threes | 0.5 to 1.5 | under | 1,010 | 64.1% | +14.7% | +9.8% to +19.7% |
| threes | 1.5 to 5.5 | over | 178 | 41.0% | -5.2% | -17.7% to +7.1% |
| threes | 1.5 to 5.5 | under | 462 | 66.9% | +8.5% | +2.1% to +14.4% |
| points+rebounds+assists | 11.5 to 15.5 | over | 723 | 64.3% | +28.6% | +23.1% to +34.1% |
| points+rebounds+assists | 11.5 to 15.5 | under | 567 | 63.0% | +11.0% | +5.8% to +16.3% |
| points+rebounds+assists | 15.5 to 21.5 | over | 432 | 65.0% | +32.6% | +24.7% to +40.3% |
| points+rebounds+assists | 15.5 to 21.5 | under | 528 | 59.8% | +3.0% | -2.5% to +8.8% |
| points+rebounds+assists | 21.5 to 43.5 | over | 110 | 68.2% | +41.7% | +26.2% to +58.7% |
| points+rebounds+assists | 21.5 to 43.5 | under | 733 | 62.1% | +5.2% | +0.5% to +10.0% |

## What the structural model learned (Poisson, log scale, fitted 2016-2021)

| market | const | log_opp | log_pace | blowout | min_out | b2b | home |
|---|---|---|---|---|---|---|---|
| points | -0.030 | +0.515 | +0.630 | +0.012 | -0.005 | +0.000 | +0.031 |
| rebounds | -0.015 | +0.440 | +0.093 | +0.010 | +0.007 | +0.000 | +0.018 |
| assists | -0.026 | +0.555 | +0.781 | +0.035 | -0.011 | +0.000 | +0.052 |
| threes | -0.035 | +0.557 | +0.512 | +0.087 | -0.005 | +0.000 | +0.005 |
| points+rebounds+assists | -0.026 | +0.515 | +0.544 | +0.015 | -0.003 | +0.000 | +0.031 |

log_opp: what the opponent has allowed lately against the league (1.0 = it passes straight through). log_pace: expected possessions against the league. blowout: expected margin size (per 10 points). min_out: usual minutes of teammates who dressed last game and not this one (per 30).
