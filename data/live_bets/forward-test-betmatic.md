# Forward test: the BetMatic method only, settled

Every meeting since 5 Oct run as BetMatic would have run it: the pre-open order file from the model's first price for the
meeting (made before the race, never re-made), filled at the opening price, 8 price steps, first-starter race rule,
scratched runners void, winnings less scratching deductions. $100 a unit. CLV = opening price / Betfair SP.

| Meeting | Orders | Horses filled | Won | Staked | P/L | Avg CLV | Beat BSP |
|---|---|---|---|---|---|---|---|
| Mon 5 Oct Pakenham | 133 | 2 | 0 | 1.11u | -1.11u | 1.91 | 2/2 |
| Tue 6 Oct Mildura | 155 | 4 | 1 | 2.65u | +3.58u | 1.57 | 2/4 |
| Wed 7 Oct Geelong | 190 | 8 | 4 | 11.91u | +23.27u | 1.65 | 7/8 |
| Thu 8 Oct Kyneton | 176 | 3 | 0 | 2.20u | -2.20u | 1.27 | 2/3 |
| Fri 9 Oct Ballarat | 270 | 4 | 0 | 3.33u | -3.33u | 2.20 | 4/4 |
| Fri 9 Oct Cranbourne | 231 | 2 | 1 | 2.81u | +3.43u | 1.22 | 1/2 |
| Sat 10 Oct Caulfield | 200 | 1 | 0 | 0.60u | -0.60u | 0.53 | 0/1 |
| Sun 11 Oct Seymour | 270 | 4 | 0 | 4.26u | -4.26u | 1.60 | 2/4 |
| Tue 13 Oct Kilmore | 159 | 4 | 1 | 3.74u | +7.50u | 2.05 | 3/4 |
| Wed 14 Oct Caulfield | not run yet | | | | | | |
| Thu 15 Oct Warrnambool | not run yet | | | | | | |
| Fri 16 Oct Cranbourne | not run yet | | | | | | |
| Sat 17 Oct Caulfield | not run yet | | | | | | |
| **Total** | **1784** | **32** | **7** | **32.61u** | **+26.28u (+81%)** | **1.67** | **23/32** |

Of these, 3 opened at or past the ceiling (3x our price, $8 for EARLY runners), where the rules would not bet: 3.97u staked, -3.97u. With a maximum price on the order: 29 bets, 28.64u, +30.25u (+106%).

## Every fill

| Meeting | Race | Horse | Ours | Min odds | Opened | Steps filled | Stake | Finish | BSP | Deduction | P/L |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Mon 5 Oct Pakenham | R3 | Genomic | $6.66 | $8.80 | $9 | 1 of 7 | 0.62u | 4 | $3.58 |  | -0.62 |
| Mon 5 Oct Pakenham | R8 | Sky Watcher | $8.20 | $10.97 | $12 | 1 of 7 | 0.49u | 2 | $9.23 |  | -0.49 |
| Tue 6 Oct Mildura | R1 | Apocalypse | $4.99 | $6.50 | $7.5 | 2 of 7 | 1.06u | 1 | $2.65 | 25c | +5.17 |
| Tue 6 Oct Mildura | R5 | Blue Typhoon | $7.22 | $9.60 | $11 | 2 of 7 | 0.68u | 8 | $5.98 |  | -0.68 |
| Tue 6 Oct Mildura | R5 | Piwhane | $7.61 | $10.13 | $11 | 1 of 7 | 0.53u | 3 | $15.00 |  | -0.53 |
| Tue 6 Oct Mildura | R7 | Attain | $10.23 | $13.84 | $15 | 1 of 7 | 0.38u | 9 | $16.86 | 12c | -0.38 |
| Wed 7 Oct Geelong | R1 | Locked In | $10.00 | $13.51 | $15 | 2 of 7 | 0.71u | 4 | $8.26 |  | -0.71 |
| Wed 7 Oct Geelong | R1 | Obsidian Stone | $8.15 | $10.89 | $15 | 4 of 7 | 1.15u | 8 | $8.82 |  | -1.15 |
| Wed 7 Oct Geelong | R2 | Nightowl | $9.91 | $13.37 | $15 | 2 of 7 | 0.48u | 6 | $12.00 | 15c | -0.48 |
| Wed 7 Oct Geelong | R3 | Silky Seth | $3.14 | $4.00 | $4.6 | 2 of 5 | 1.88u | 2 | $6.73 |  | -1.88 |
| Wed 7 Oct Geelong | R3 | Hedjet | $2.35 | $2.94 | $3.6 | 2 of 2 | 2.50u | 1 | $1.77 |  | +6.50 |
| Wed 7 Oct Geelong | R4 | Mr Natural | $2.65 | $3.34 | $4.6 | 3 of 3 | 2.50u | 1 | $2.82 | 8c | +8.29 |
| Wed 7 Oct Geelong | R6 | Insain Harry | $9.23 | $12.42 | $15 | 3 of 7 | 0.59u | 1 | $8.64 | 13c | +7.21 |
| Wed 7 Oct Geelong | R8 | Stay Humble | $3.44 | $4.40 | $6 | 4 of 7 | 2.10u | 1 | $2.57 | 48c | +5.49 |
| Thu 8 Oct Kyneton | R1 | Windhowler | $10.54 | $14.27 | $21 | 5 of 7 | 0.62u | 7 | $34.00 | 5c | -0.62 |
| Thu 8 Oct Kyneton | R6 | Lim's Ida | $11.64 | $15.85 | $26 | 6 of 7 | 0.60u | 3 | $19.00 | 37c | -0.60 |
| Thu 8 Oct Kyneton | R9 | Blue Moon Summit | $7.65 | $10.19 | $41 | 7 of 7 | 0.98u | 6 | $22.53 | 4c | -0.98 | opened past the 3x ceiling
| Fri 9 Oct Ballarat | R1 | Alltogethernow | $7.14 | $9.48 | $15.57 | 6 of 7 | 1.02u | 10 | $10.50 |  | -1.02 |
| Fri 9 Oct Ballarat | R10 | The Muffin Man | $6.69 | $8.84 | $11.5 | 4 of 7 | 0.96u | 2 | $4.00 |  | -0.96 |
| Fri 9 Oct Ballarat | R2 | Top Rich | $7.15 | $9.49 | $15.11 | 5 of 7 | 0.96u | 2 | $4.45 |  | -0.96 |
| Fri 9 Oct Ballarat | R3 | Explosive Magic | $9.87 | $13.33 | $14.5 | 1 of 7 | 0.39u | 3 | $13.90 |  | -0.39 |
| Fri 9 Oct Cranbourne | R1 | Kotahitanga | $1.92 | $2.39 | $3 | 1 of 1 | 2.50u | 1 | $1.90 | 25c | +3.74 |
| Fri 9 Oct Cranbourne | R6 | Art 'n' Soul | $12.23 | $16.69 | $18 | 1 of 7 | 0.31u | 7 | $21.00 |  | -0.31 |
| Sat 10 Oct Caulfield | R10 | War Machine | $12.09 | $16.49 | $17 | 1 of 7 | 0.31u | scratched | | | 0 |
| Sat 10 Oct Caulfield | R4 | Sunset Park | $12.79 | $17.50 | $18 | 1 of 7 | 0.29u | scratched | | | 0 |
| Sat 10 Oct Caulfield | R4 | Campaldino | $10.17 | $13.74 | $18 | 4 of 7 | 0.60u | 11 | $33.98 | 4c | -0.60 |
| Sun 11 Oct Seymour | R1 | More Foxie | $3.35 | $4.28 | $4.4 | 1 of 7 | 1.45u | 7 | $4.86 | 22c | -1.45 |
| Sun 11 Oct Seymour | R5 | Yahoo Bar | $7.92 | $10.57 | $14 | 4 of 7 | 0.79u | 2 | $10.50 | 14c | -0.79 |
| Sun 11 Oct Seymour | R6 | Bel Lupa | $5.02 | $6.54 | $19 | 7 of 7 | 1.58u | 6 | $5.20 | 27c | -1.58 | opened past the 3x ceiling
| Sun 11 Oct Seymour | R6 | Ulfberht | $8.96 | $12.04 | $13 | 1 of 7 | 0.44u | 7 | $26.00 | 27c | -0.44 |
| Sun 11 Oct Seymour | R8 | Wingsandpropellers | $7.71 | $10.28 | $26 | 7 of 7 | 0.98u | scratched | | | 0 |
| Sun 11 Oct Seymour | R8 | Bacash | $11.64 | $15.85 | $17 | 1 of 7 | 0.33u | scratched | | | 0 |
| Tue 13 Oct Kilmore | R3 | Succaforyou | $5.19 | $6.78 | $9 | 4 of 7 | 1.28u | 7 | $7.91 |  | -1.28 |
| Tue 13 Oct Kilmore | R5 | Knock Of Beers | $5.55 | $7.28 | $21 | 7 of 7 | 1.41u | 8 | $5.77 | 24c | -1.41 | opened past the 3x ceiling
| Tue 13 Oct Kilmore | R7 | Celestial Splendor | $9.39 | $12.64 | $19 | 5 of 7 | 0.71u | 1 | $7.80 | 18c | +10.53 |
| Tue 13 Oct Kilmore | R7 | Winter Nights | $11.18 | $15.18 | $16 | 1 of 7 | 0.34u | 3 | $16.44 | 18c | -0.34 |
