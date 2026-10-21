# NBL player props, step 1: projections and a stand-in-line backtest

**Every betting result below is against STAND-IN lines, not real ones.** No NBL prop lines are held yet (The Odds API key is not set up, and its NBL prop history may start only in September 2026). A stand-in line is the player's own recent average moved by one fixed amount, chosen on 2022-23 so a blind over wins half the time, at 1.87 each way. Books are said to set lines from recent averages, but they also see team news and some will price better, so these figures are an upper bound on a real edge, and may be far above it.

Which games count: the player dressed and played (an unplayed prop is void), 5+ earlier games, and he usually plays 12+ minutes. Betting tables keep only lines a book would post: at least points 7.5, rebounds 2.5, assists 1.5, threes 0.5, points+rebounds+assists 11.5 (this floor was set after looking at the confirm seasons and before the final check). Seasons are named by the year they start. Fit 2016-2021, tune 2022, confirm 2023 and 2024, final check 2025 and 2026 (2026 = this season to 18 Oct 2026).

**Honesty note.** The final-check seasons were scored once with the first version (21 Oct 2026). Since then per-stat memory and a spread that changes with the projection were adopted, both chosen on 2016-2022 and confirmed on 2023-2024 only (nbl/docs/RESEARCH.md); this is a second look at 2025-2026.

## Projection accuracy

Minutes, tuning season: our minutes model misses by 4.25 minutes a game, the player's decayed average by 4.63.

| market | model chosen on 2022 | miss per player-game, 2022: ours | last-10 average | spread a(mu) = a0 mu^k |
|---|---|---|---|---|
| points | blend | 4.37 | 4.48 | 6.951 mu^-1.45 |
| rebounds | struct | 1.82 | 1.90 | 0.492 mu^-1.13 |
| assists | struct | 1.17 | 1.22 | 0.255 mu^-0.93 |
| threes | blend | 0.84 | 0.85 | 0.234 mu^-1.32 |
| points+rebounds+assists | blend | 5.62 | 5.82 | 7.934 mu^-1.42 |

| season | rows | points: ours / last 10 | rebounds: ours / last 10 | assists: ours / last 10 | threes: ours / last 10 | points+rebounds+assists: ours / last 10 |
|---|---|---|---|---|---|---|
| 2023 | 2398 | 4.34 / 4.53 | 1.86 / 1.95 | 1.15 / 1.18 | 0.81 / 0.82 | 5.50 / 5.78 |
| 2024 | 2522 | 4.69 / 4.82 | 1.80 / 1.89 | 1.18 / 1.21 | 0.86 / 0.89 | 5.92 / 6.10 |
| 2025 | 2693 | 4.57 / 4.74 | 1.84 / 1.89 | 1.25 / 1.30 | 0.87 / 0.88 | 5.79 / 6.01 |
| 2026 | 450 | 5.00 / 5.25 | 1.88 / 1.99 | 1.33 / 1.34 | 0.97 / 0.99 | 6.36 / 6.68 |

## Is the over chance honest? (confirm seasons, against the last-10 stand-in)

| market | our over chance | bets | over won |
|---|---|---|---|
| points | 0% to 30% | 426 | 30% |
| points | 30% to 40% | 1320 | 41% |
| points | 40% to 50% | 1773 | 50% |
| points | 50% to 60% | 961 | 59% |
| points | 60% to 70% | 342 | 69% |
| points | 70% to 100% | 98 | 83% |
| rebounds | 0% to 30% | 328 | 23% |
| rebounds | 30% to 40% | 955 | 37% |
| rebounds | 40% to 50% | 1467 | 48% |
| rebounds | 50% to 60% | 1287 | 56% |
| rebounds | 60% to 70% | 672 | 65% |
| rebounds | 70% to 100% | 211 | 77% |
| assists | 0% to 30% | 255 | 26% |
| assists | 30% to 40% | 699 | 41% |
| assists | 40% to 50% | 1211 | 45% |
| assists | 50% to 60% | 1270 | 57% |
| assists | 60% to 70% | 931 | 66% |
| assists | 70% to 100% | 554 | 81% |
| threes | 0% to 30% | 704 | 26% |
| threes | 30% to 40% | 1071 | 35% |
| threes | 40% to 50% | 1152 | 45% |
| threes | 50% to 60% | 942 | 56% |
| threes | 60% to 70% | 391 | 59% |
| threes | 70% to 100% | 660 | 97% |
| points+rebounds+assists | 0% to 30% | 413 | 28% |
| points+rebounds+assists | 30% to 40% | 1062 | 42% |
| points+rebounds+assists | 40% to 50% | 1716 | 51% |
| points+rebounds+assists | 50% to 60% | 1078 | 55% |
| points+rebounds+assists | 60% to 70% | 477 | 68% |
| points+rebounds+assists | 70% to 100% | 174 | 82% |

## Betting against stand-in lines

Bet a side when our chance of it is at least the stated figure; 1.87 breaks even at 53.5%. ROI per unit staked; the 90% interval comes from resampling whole rounds (weeks). Confirm seasons first, then the final check.

| market | stand-in | seasons | bet at | bets | overs / unders | hit rate | ROI | 90% interval |
|---|---|---|---|---|---|---|---|---|
| points | last 10 | 2023-2024 | 56% | 2,049 | 218 / 1,831 | 59.5% | +11.3% | +8.0% to +14.8% |
| points | last 10 | 2023-2024 | 60% | 1,409 | 95 / 1,314 | 62.0% | +15.9% | +12.0% to +19.7% |
| points | last 10 | 2025-2026 | 56% | 1,328 | 227 / 1,101 | 60.9% | +13.9% | +10.2% to +17.6% |
| points | last 10 | 2025-2026 | 60% | 867 | 90 / 777 | 63.0% | +17.8% | +12.3% to +23.5% |
| points | last 5 | 2023-2024 | 56% | 2,196 | 402 / 1,794 | 62.9% | +17.6% | +15.1% to +20.2% |
| points | last 5 | 2023-2024 | 60% | 1,680 | 240 / 1,440 | 64.8% | +21.1% | +18.5% to +23.8% |
| points | last 5 | 2025-2026 | 56% | 1,459 | 374 / 1,085 | 62.6% | +17.0% | +13.3% to +20.8% |
| points | last 5 | 2025-2026 | 60% | 1,078 | 228 / 850 | 62.4% | +16.7% | +12.9% to +20.7% |
| rebounds | last 10 | 2023-2024 | 56% | 2,565 | 854 / 1,711 | 64.0% | +19.6% | +16.4% to +22.9% |
| rebounds | last 10 | 2023-2024 | 60% | 1,723 | 535 / 1,188 | 67.7% | +26.7% | +23.1% to +30.3% |
| rebounds | last 10 | 2025-2026 | 56% | 1,563 | 563 / 1,000 | 60.5% | +13.2% | +9.2% to +17.0% |
| rebounds | last 10 | 2025-2026 | 60% | 1,008 | 332 / 676 | 65.1% | +21.7% | +17.0% to +26.0% |
| rebounds | last 5 | 2023-2024 | 56% | 2,873 | 726 / 2,147 | 65.4% | +22.4% | +19.8% to +24.8% |
| rebounds | last 5 | 2023-2024 | 60% | 2,186 | 476 / 1,710 | 67.4% | +26.0% | +22.8% to +29.0% |
| rebounds | last 5 | 2025-2026 | 56% | 1,817 | 543 / 1,274 | 64.4% | +20.5% | +16.6% to +24.5% |
| rebounds | last 5 | 2025-2026 | 60% | 1,362 | 368 / 994 | 68.3% | +27.7% | +23.7% to +31.7% |
| assists | last 10 | 2023-2024 | 56% | 1,682 | 553 / 1,129 | 61.4% | +14.8% | +11.3% to +18.4% |
| assists | last 10 | 2023-2024 | 60% | 1,180 | 362 / 818 | 63.4% | +18.5% | +14.1% to +22.9% |
| assists | last 10 | 2025-2026 | 56% | 1,183 | 388 / 795 | 62.0% | +16.0% | +11.2% to +20.7% |
| assists | last 10 | 2025-2026 | 60% | 761 | 215 / 546 | 63.9% | +19.4% | +14.2% to +23.9% |
| assists | last 5 | 2023-2024 | 56% | 2,020 | 551 / 1,469 | 63.4% | +18.6% | +15.7% to +21.6% |
| assists | last 5 | 2023-2024 | 60% | 1,590 | 407 / 1,183 | 65.3% | +22.2% | +18.9% to +25.4% |
| assists | last 5 | 2025-2026 | 56% | 1,424 | 369 / 1,055 | 62.1% | +16.2% | +12.4% to +19.6% |
| assists | last 5 | 2025-2026 | 60% | 1,068 | 234 / 834 | 64.1% | +19.9% | +16.1% to +23.3% |
| threes | last 10 | 2023-2024 | 56% | 3,029 | 767 / 2,262 | 64.0% | +19.6% | +17.1% to +22.5% |
| threes | last 10 | 2023-2024 | 60% | 2,231 | 456 / 1,775 | 66.7% | +24.7% | +21.9% to +27.5% |
| threes | last 10 | 2025-2026 | 56% | 1,937 | 586 / 1,351 | 66.8% | +24.9% | +21.0% to +28.5% |
| threes | last 10 | 2025-2026 | 60% | 1,480 | 398 / 1,082 | 67.8% | +26.7% | +22.3% to +30.9% |
| threes | last 5 | 2023-2024 | 56% | 3,224 | 794 / 2,430 | 65.9% | +23.2% | +20.6% to +25.9% |
| threes | last 5 | 2023-2024 | 60% | 2,555 | 536 / 2,019 | 68.8% | +28.6% | +25.9% to +31.2% |
| threes | last 5 | 2025-2026 | 56% | 2,073 | 617 / 1,456 | 68.5% | +28.0% | +24.4% to +31.1% |
| threes | last 5 | 2025-2026 | 60% | 1,690 | 441 / 1,249 | 69.7% | +30.3% | +26.3% to +34.0% |
| points+rebounds+assists | last 10 | 2023-2024 | 56% | 2,077 | 425 / 1,652 | 60.8% | +13.7% | +10.5% to +17.2% |
| points+rebounds+assists | last 10 | 2023-2024 | 60% | 1,362 | 228 / 1,134 | 63.4% | +18.6% | +14.8% to +22.9% |
| points+rebounds+assists | last 10 | 2025-2026 | 56% | 1,387 | 331 / 1,056 | 61.6% | +15.1% | +11.5% to +18.8% |
| points+rebounds+assists | last 10 | 2025-2026 | 60% | 925 | 166 / 759 | 63.0% | +17.9% | +13.2% to +22.6% |
| points+rebounds+assists | last 5 | 2023-2024 | 56% | 2,381 | 503 / 1,878 | 62.0% | +16.0% | +13.6% to +18.5% |
| points+rebounds+assists | last 5 | 2023-2024 | 60% | 1,762 | 313 / 1,449 | 64.8% | +21.1% | +18.3% to +24.0% |
| points+rebounds+assists | last 5 | 2025-2026 | 56% | 1,586 | 421 / 1,165 | 63.2% | +18.1% | +14.2% to +21.9% |
| points+rebounds+assists | last 5 | 2025-2026 | 60% | 1,188 | 273 / 915 | 65.1% | +21.7% | +17.6% to +25.5% |

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
| points | last 10 | 2023-2024 | 3% | 1,807 | 686 / 1,121 | 61.8% | 1.84 | +13.9% | +10.5% to +17.3% |
| points | last 10 | 2023-2024 | 8% | 1,254 | 487 / 767 | 62.9% | 1.85 | +16.2% | +11.2% to +21.0% |
| points | last 10 | 2025-2026 | 3% | 1,285 | 637 / 648 | 61.8% | 1.88 | +16.2% | +11.7% to +20.7% |
| points | last 10 | 2025-2026 | 8% | 906 | 464 / 442 | 63.4% | 1.89 | +19.4% | +14.4% to +24.6% |
| points | last 5 | 2023-2024 | 3% | 2,126 | 819 / 1,307 | 64.5% | 1.84 | +18.4% | +16.0% to +20.8% |
| points | last 5 | 2023-2024 | 8% | 1,672 | 648 / 1,024 | 66.1% | 1.84 | +21.4% | +18.3% to +24.6% |
| points | last 5 | 2025-2026 | 3% | 1,504 | 733 / 771 | 62.8% | 1.88 | +18.3% | +14.8% to +21.7% |
| points | last 5 | 2025-2026 | 8% | 1,194 | 596 / 598 | 64.5% | 1.88 | +21.6% | +18.2% to +24.9% |
| rebounds | last 10 | 2023-2024 | 3% | 2,468 | 1,230 / 1,238 | 63.5% | 1.89 | +19.0% | +15.9% to +22.2% |
| rebounds | last 10 | 2023-2024 | 8% | 1,805 | 938 / 867 | 65.6% | 1.90 | +23.9% | +20.4% to +27.6% |
| rebounds | last 10 | 2025-2026 | 3% | 1,605 | 884 / 721 | 60.0% | 1.92 | +13.5% | +9.9% to +17.0% |
| rebounds | last 10 | 2025-2026 | 8% | 1,178 | 660 / 518 | 60.9% | 1.93 | +15.4% | +10.5% to +20.0% |
| rebounds | last 5 | 2023-2024 | 3% | 2,795 | 1,328 / 1,467 | 62.9% | 1.92 | +18.9% | +16.1% to +21.7% |
| rebounds | last 5 | 2023-2024 | 8% | 2,246 | 1,091 / 1,155 | 64.2% | 1.93 | +22.0% | +18.7% to +25.1% |
| rebounds | last 5 | 2025-2026 | 3% | 1,870 | 983 / 887 | 62.7% | 1.93 | +19.2% | +15.4% to +23.4% |
| rebounds | last 5 | 2025-2026 | 8% | 1,470 | 791 / 679 | 64.6% | 1.95 | +23.6% | +19.4% to +27.9% |
| assists | last 10 | 2023-2024 | 3% | 1,634 | 715 / 919 | 59.8% | 1.90 | +12.3% | +9.2% to +15.6% |
| assists | last 10 | 2023-2024 | 8% | 1,220 | 516 / 704 | 61.5% | 1.92 | +16.3% | +12.5% to +20.3% |
| assists | last 10 | 2025-2026 | 3% | 1,148 | 451 / 697 | 60.3% | 1.92 | +14.5% | +9.2% to +19.8% |
| assists | last 10 | 2025-2026 | 8% | 843 | 327 / 516 | 61.8% | 1.93 | +18.6% | +13.0% to +24.4% |
| assists | last 5 | 2023-2024 | 3% | 1,950 | 745 / 1,205 | 62.1% | 1.88 | +15.4% | +12.0% to +18.7% |
| assists | last 5 | 2023-2024 | 8% | 1,591 | 596 / 995 | 64.2% | 1.89 | +19.6% | +15.9% to +23.2% |
| assists | last 5 | 2025-2026 | 3% | 1,419 | 515 / 904 | 62.1% | 1.89 | +16.4% | +12.2% to +20.8% |
| assists | last 5 | 2025-2026 | 8% | 1,136 | 387 / 749 | 63.6% | 1.89 | +19.6% | +14.9% to +24.3% |
| threes | last 10 | 2023-2024 | 3% | 2,687 | 1,584 / 1,103 | 54.7% | 2.39 | +20.0% | +15.2% to +24.7% |
| threes | last 10 | 2023-2024 | 8% | 2,040 | 1,281 / 759 | 55.0% | 2.52 | +25.7% | +20.2% to +30.9% |
| threes | last 10 | 2025-2026 | 3% | 1,759 | 1,119 / 640 | 56.5% | 2.29 | +20.1% | +15.6% to +24.8% |
| threes | last 10 | 2025-2026 | 8% | 1,336 | 886 / 450 | 56.1% | 2.41 | +24.8% | +19.8% to +30.1% |
| threes | last 5 | 2023-2024 | 3% | 3,098 | 1,823 / 1,275 | 58.5% | 2.50 | +32.2% | +28.4% to +35.8% |
| threes | last 5 | 2023-2024 | 8% | 2,551 | 1,599 / 952 | 58.6% | 2.62 | +38.1% | +33.7% to +42.0% |
| threes | last 5 | 2025-2026 | 3% | 2,024 | 1,269 / 755 | 59.9% | 2.45 | +34.6% | +30.3% to +38.7% |
| threes | last 5 | 2025-2026 | 8% | 1,687 | 1,113 / 574 | 58.9% | 2.56 | +38.3% | +33.7% to +42.8% |
| points+rebounds+assists | last 10 | 2023-2024 | 3% | 1,996 | 849 / 1,147 | 60.9% | 1.85 | +12.9% | +9.6% to +16.7% |
| points+rebounds+assists | last 10 | 2023-2024 | 8% | 1,420 | 598 / 822 | 64.2% | 1.85 | +18.9% | +15.0% to +23.0% |
| points+rebounds+assists | last 10 | 2025-2026 | 3% | 1,455 | 684 / 771 | 62.6% | 1.87 | +17.1% | +13.8% to +20.4% |
| points+rebounds+assists | last 10 | 2025-2026 | 8% | 1,082 | 504 / 578 | 64.3% | 1.87 | +20.2% | +16.8% to +23.6% |
| points+rebounds+assists | last 5 | 2023-2024 | 3% | 2,319 | 896 / 1,423 | 63.6% | 1.84 | +17.1% | +14.6% to +19.6% |
| points+rebounds+assists | last 5 | 2023-2024 | 8% | 1,841 | 698 / 1,143 | 65.8% | 1.84 | +20.7% | +18.1% to +23.3% |
| points+rebounds+assists | last 5 | 2025-2026 | 3% | 1,626 | 743 / 883 | 64.2% | 1.86 | +19.5% | +16.6% to +22.5% |
| points+rebounds+assists | last 5 | 2025-2026 | 8% | 1,288 | 587 / 701 | 66.8% | 1.86 | +24.3% | +20.8% to +27.5% |

## Where the edge comes from (naive book, last-10 stand-in, edge 3%)

If shuffled projections also won, the test would be broken. If a plain projection (half the last-10 average, half the decayed per-minute rate x usual minutes) wins nearly as much, the edge is mostly "regress the recent average", which a real book may already do.

| market | seasons | ours: bets, ROI | shuffled projections: bets, ROI | plain projection: bets, ROI |
|---|---|---|---|---|
| points | 2023-2024 | 1,807, +13.9% | 2,740, -3.4% | 828, +17.3% |
| points | 2025-2026 | 1,285, +16.2% | 1,896, -1.8% | 635, +23.3% |
| rebounds | 2023-2024 | 2,468, +19.0% | 3,516, -5.4% | 931, +20.0% |
| rebounds | 2025-2026 | 1,605, +13.5% | 2,315, -3.6% | 714, +15.6% |
| assists | 2023-2024 | 1,634, +12.3% | 2,321, -8.4% | 736, +11.6% |
| assists | 2025-2026 | 1,148, +14.5% | 1,704, -8.8% | 394, +24.9% |
| threes | 2023-2024 | 2,687, +20.0% | 3,815, +3.0% | 1,294, +29.0% |
| threes | 2025-2026 | 1,759, +20.1% | 2,421, +4.3% | 816, +23.4% |
| points+rebounds+assists | 2023-2024 | 1,996, +12.9% | 2,953, -1.4% | 985, +15.9% |
| points+rebounds+assists | 2025-2026 | 1,455, +17.1% | 2,064, -6.3% | 682, +20.5% |

## By line size and side (naive book, last-10 stand-in, edge 3%, all seasons shown above)

| market | line | side | bets | hit rate | ROI | 90% interval |
|---|---|---|---|---|---|---|
| points | 7.5 to 10.5 | over | 664 | 66.4% | +37.8% | +31.0% to +44.6% |
| points | 7.5 to 10.5 | under | 698 | 61.5% | +4.5% | -0.1% to +9.3% |
| points | 10.5 to 14.5 | over | 444 | 59.7% | +26.0% | +19.0% to +33.3% |
| points | 10.5 to 14.5 | under | 486 | 59.1% | -1.2% | -6.8% to +4.4% |
| points | 14.5 to 34.5 | over | 215 | 56.3% | +20.7% | +6.6% to +33.4% |
| points | 14.5 to 34.5 | under | 585 | 62.9% | +3.8% | -1.1% to +8.8% |
| rebounds | 2.5 to 3.5 | over | 1,186 | 60.1% | +19.6% | +15.2% to +24.0% |
| rebounds | 2.5 to 3.5 | under | 879 | 65.5% | +18.3% | +13.8% to +22.8% |
| rebounds | 3.5 to 4.5 | over | 330 | 59.4% | +20.6% | +10.2% to +30.4% |
| rebounds | 3.5 to 4.5 | under | 380 | 66.1% | +15.0% | +7.8% to +22.6% |
| rebounds | 4.5 to 11.5 | over | 598 | 55.0% | +11.7% | +5.2% to +18.5% |
| rebounds | 4.5 to 11.5 | under | 700 | 66.3% | +13.8% | +9.2% to +18.3% |
| assists | 1.5 to 2.5 | over | 867 | 59.3% | +17.9% | +12.3% to +23.6% |
| assists | 1.5 to 2.5 | under | 1,013 | 60.7% | +12.2% | +7.6% to +16.5% |
| assists | 2.5 to 9.5 | over | 299 | 58.2% | +16.4% | +6.6% to +27.1% |
| assists | 2.5 to 9.5 | under | 603 | 60.7% | +6.8% | +1.7% to +12.2% |
| threes | 0.5 to 1.5 | over | 2,557 | 49.9% | +26.2% | +21.2% to +31.4% |
| threes | 0.5 to 1.5 | under | 1,263 | 62.4% | +12.3% | +8.2% to +16.6% |
| threes | 1.5 to 5.5 | over | 146 | 46.6% | +5.0% | -7.8% to +17.0% |
| threes | 1.5 to 5.5 | under | 480 | 68.8% | +12.0% | +6.6% to +17.6% |
| points+rebounds+assists | 11.5 to 15.5 | over | 675 | 65.2% | +30.2% | +24.4% to +35.8% |
| points+rebounds+assists | 11.5 to 15.5 | under | 662 | 61.6% | +8.6% | +3.6% to +13.7% |
| points+rebounds+assists | 15.5 to 21.5 | over | 573 | 62.7% | +27.9% | +20.7% to +34.1% |
| points+rebounds+assists | 15.5 to 21.5 | under | 569 | 59.6% | +2.5% | -2.8% to +7.8% |
| points+rebounds+assists | 21.5 to 43.5 | over | 285 | 58.6% | +21.3% | +11.6% to +31.1% |
| points+rebounds+assists | 21.5 to 43.5 | under | 687 | 60.1% | +1.8% | -3.0% to +7.0% |

## What the structural model learned (Poisson, log scale, fitted 2016-2021)

| market | const | log_opp | log_pace | blowout | min_out | b2b | home |
|---|---|---|---|---|---|---|---|
| points | -0.031 | +0.512 | +0.589 | +0.011 | -0.004 | +0.000 | +0.032 |
| rebounds | -0.021 | +0.432 | -0.031 | +0.008 | +0.009 | +0.000 | +0.019 |
| assists | -0.022 | +0.549 | +0.832 | +0.037 | -0.008 | +0.000 | +0.054 |
| threes | -0.029 | +0.555 | +0.498 | +0.079 | -0.003 | +0.000 | +0.005 |
| points+rebounds+assists | -0.027 | +0.501 | +0.484 | +0.014 | -0.001 | +0.000 | +0.032 |

log_opp: what the opponent has allowed lately against the league (1.0 = it passes straight through). log_pace: expected possessions against the league. blowout: expected margin size (per 10 points). min_out: usual minutes of teammates who dressed last game and not this one (per 30).
