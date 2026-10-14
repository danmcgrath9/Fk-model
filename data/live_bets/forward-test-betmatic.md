# Forward test: the BetMatic method only, settled

Every meeting since 5 Oct run as BetMatic would have run it: the pre-open order file from the model's first price for the
meeting (made before the race, never re-made), filled at the opening price, the order file's price steps (3 from 14 Oct), first-starter race rule,
scratched runners void, winnings less scratching deductions. $100 a unit. CLV = opening price / Betfair SP.

| Meeting | Orders | Horses filled | Won | Staked | P/L | Avg CLV | Beat BSP |
|---|---|---|---|---|---|---|---|
| Mon 5 Oct Pakenham | 38 | 2 | 0 | 1.43u | -1.43u | 1.91 | 2/2 |
| Tue 6 Oct Mildura | 46 | 4 | 1 | 3.04u | +3.60u | 1.57 | 2/4 |
| Wed 7 Oct Geelong | 57 | 8 | 4 | 12.17u | +22.70u | 1.65 | 7/8 |
| Thu 8 Oct Kyneton | 54 | 3 | 0 | 1.97u | -1.97u | 1.27 | 2/3 |
| Fri 9 Oct Ballarat | 77 | 4 | 0 | 3.31u | -3.31u | 2.20 | 4/4 |
| Fri 9 Oct Cranbourne | 68 | 2 | 1 | 2.90u | +3.34u | 1.22 | 1/2 |
| Sat 10 Oct Caulfield | 60 | 1 | 0 | 0.62u | -0.62u | 0.53 | 0/1 |
| Sun 11 Oct Seymour | 80 | 4 | 0 | 4.60u | -4.60u | 1.60 | 2/4 |
| Tue 13 Oct Kilmore | 48 | 4 | 1 | 3.66u | +6.94u | 2.05 | 3/4 |
| Wed 14 Oct Caulfield | 250 | 5 | 0 | 5.04u | -5.04u | 0.00 | 0/0 |
| Thu 15 Oct Warrnambool | not run yet | | | | | | |
| Fri 16 Oct Cranbourne | not run yet | | | | | | |
| Sat 17 Oct Caulfield | not run yet | | | | | | |
| **Total** | **778** | **37** | **7** | **38.74u** | **+19.62u (+51%)** | **1.67** | **23/32** |

Of these, 3 opened at or past the ceiling (3x our price, $8 for EARLY runners), where the rules would not bet: 3.44u staked, -3.44u. With a maximum price on the order: 34 bets, 35.30u, +23.06u (+65%).

## Every fill

| Meeting | Race | Horse | Ours | Min odds | Opened | Steps filled | Stake | Finish | BSP | Deduction | P/L |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Mon 5 Oct Pakenham | R3 | Genomic | $6.66 | $8.80 | $9 | 1 of 2 | 0.80u | 4 | $3.58 |  | -0.80 |
| Mon 5 Oct Pakenham | R8 | Sky Watcher | $8.20 | $10.97 | $12 | 1 of 2 | 0.63u | 2 | $9.23 |  | -0.63 |
| Tue 6 Oct Mildura | R1 | Apocalypse | $4.99 | $6.50 | $7.5 | 1 of 2 | 1.13u | 1 | $2.65 | 25c | +5.51 |
| Tue 6 Oct Mildura | R5 | Blue Typhoon | $7.22 | $9.60 | $11 | 1 of 2 | 0.73u | 8 | $5.98 |  | -0.73 |
| Tue 6 Oct Mildura | R5 | Piwhane | $7.61 | $10.13 | $11 | 1 of 2 | 0.69u | 3 | $15.00 |  | -0.69 |
| Tue 6 Oct Mildura | R7 | Attain | $10.23 | $13.84 | $15 | 1 of 2 | 0.49u | 9 | $16.86 | 12c | -0.49 |
| Wed 7 Oct Geelong | R1 | Locked In | $10.00 | $13.51 | $15 | 1 of 2 | 0.76u | 4 | $8.26 |  | -0.76 |
| Wed 7 Oct Geelong | R1 | Obsidian Stone | $8.15 | $10.89 | $15 | 2 of 2 | 1.18u | 8 | $8.82 |  | -1.18 |
| Wed 7 Oct Geelong | R2 | Nightowl | $9.91 | $13.37 | $15 | 1 of 2 | 0.51u | 6 | $12.00 | 15c | -0.51 |
| Wed 7 Oct Geelong | R3 | Hedjet | $2.35 | $2.94 | $3.6 | 1 of 1 | 2.50u | 1 | $1.77 |  | +6.50 |
| Wed 7 Oct Geelong | R3 | Silky Seth | $3.14 | $4.00 | $4.6 | 1 of 2 | 2.01u | 2 | $6.73 |  | -2.01 |
| Wed 7 Oct Geelong | R4 | Mr Natural | $2.65 | $3.34 | $4.6 | 1 of 1 | 2.50u | 1 | $2.82 | 8c | +8.29 |
| Wed 7 Oct Geelong | R6 | Insain Harry | $9.23 | $12.42 | $15 | 1 of 2 | 0.55u | 1 | $8.64 | 13c | +6.72 |
| Wed 7 Oct Geelong | R8 | Stay Humble | $3.44 | $4.40 | $6 | 2 of 2 | 2.16u | 1 | $2.57 | 48c | +5.65 |
| Thu 8 Oct Kyneton | R1 | Windhowler | $10.54 | $14.27 | $21 | 2 of 2 | 0.59u | 7 | $34.00 | 5c | -0.59 |
| Thu 8 Oct Kyneton | R6 | Lim's Ida | $11.64 | $15.85 | $26 | 2 of 2 | 0.53u | 3 | $19.00 | 37c | -0.53 |
| Thu 8 Oct Kyneton | R9 | Blue Moon Summit | $7.65 | $10.19 | $41 | 2 of 2 | 0.85u | 6 | $22.53 | 4c | -0.85 | opened past the 3x ceiling
| Fri 9 Oct Ballarat | R1 | Alltogethernow | $7.14 | $9.48 | $15.57 | 2 of 2 | 0.91u | 10 | $10.50 |  | -0.91 |
| Fri 9 Oct Ballarat | R2 | Top Rich | $7.15 | $9.49 | $15.11 | 2 of 2 | 0.91u | 2 | $4.45 |  | -0.91 |
| Fri 9 Oct Ballarat | R3 | Explosive Magic | $9.87 | $13.33 | $14.5 | 1 of 2 | 0.51u | 3 | $13.90 |  | -0.51 |
| Fri 9 Oct Ballarat | R10 | The Muffin Man | $6.69 | $8.84 | $11.5 | 2 of 2 | 0.98u | 2 | $4.00 |  | -0.98 |
| Fri 9 Oct Cranbourne | R1 | Kotahitanga | $1.92 | $2.39 | $3 | 1 of 1 | 2.50u | 1 | $1.90 | 25c | +3.74 |
| Fri 9 Oct Cranbourne | R6 | Art 'n' Soul | $12.23 | $16.69 | $18 | 1 of 2 | 0.40u | 7 | $21.00 |  | -0.40 |
| Sat 10 Oct Caulfield | R4 | Campaldino | $10.17 | $13.74 | $18 | 2 of 2 | 0.62u | 11 | $33.98 | 4c | -0.62 |
| Sat 10 Oct Caulfield | R4 | Sunset Park | $12.79 | $17.50 | $18 | 1 of 2 | 0.38u | scratched | | | 0 |
| Sat 10 Oct Caulfield | R10 | War Machine | $12.09 | $16.49 | $17 | 1 of 2 | 0.41u | scratched | | | 0 |
| Sun 11 Oct Seymour | R1 | More Foxie | $3.35 | $4.28 | $4.4 | 1 of 2 | 1.85u | 7 | $4.86 | 22c | -1.85 |
| Sun 11 Oct Seymour | R5 | Yahoo Bar | $7.92 | $10.57 | $14 | 2 of 2 | 0.81u | 2 | $10.50 | 14c | -0.81 |
| Sun 11 Oct Seymour | R6 | Bel Lupa | $5.02 | $6.54 | $19 | 2 of 2 | 1.37u | 6 | $5.20 | 27c | -1.37 | opened past the 3x ceiling
| Sun 11 Oct Seymour | R6 | Ulfberht | $8.96 | $12.04 | $13 | 1 of 2 | 0.57u | 7 | $26.00 | 27c | -0.57 |
| Sun 11 Oct Seymour | R8 | Bacash | $11.64 | $15.85 | $17 | 1 of 2 | 0.43u | scratched | | | 0 |
| Sun 11 Oct Seymour | R8 | Wingsandpropellers | $7.71 | $10.28 | $26 | 2 of 2 | 0.84u | scratched | | | 0 |
| Tue 13 Oct Kilmore | R3 | Succaforyou | $5.19 | $6.78 | $9 | 2 of 2 | 1.32u | 7 | $7.91 |  | -1.32 |
| Tue 13 Oct Kilmore | R5 | Knock Of Beers | $5.55 | $7.28 | $21 | 2 of 2 | 1.22u | 8 | $5.77 | 24c | -1.22 | opened past the 3x ceiling
| Tue 13 Oct Kilmore | R7 | Celestial Splendor | $9.39 | $12.64 | $19 | 2 of 2 | 0.67u | 1 | $7.80 | 18c | +9.93 |
| Tue 13 Oct Kilmore | R7 | Winter Nights | $11.18 | $15.18 | $16 | 1 of 2 | 0.45u | 3 | $16.44 | 18c | -0.45 |
| Wed 14 Oct Caulfield | R2 | Katoto | $4.87 | $6.34 | $11 | 6 of 7 | 1.58u | scratched | | | 0 |
| Wed 14 Oct Caulfield | R2 | True Rebel | $5.17 | $6.75 | $8 | 2 of 7 | 1.01u | 2 |  | 20c | -1.01 |
| Wed 14 Oct Caulfield | R4 | Savisanta | $6.25 | $8.24 | $10 | 3 of 7 | 0.91u | 3 |  | 2c | -0.91 |
| Wed 14 Oct Caulfield | R5 | Jett Smash | $3.30 | $4.22 | $4.4 | 1 of 6 | 1.47u | 0 |  | 2c | -1.47 |
| Wed 14 Oct Caulfield | R7 | Darkbonee | $3.62 | $4.64 | $4.8 | 1 of 7 | 1.30u | 2 |  |  | -1.30 |
| Wed 14 Oct Caulfield | R8 | Verdoux | $14.54 | $20.02 | $26 | 3 of 7 | 0.35u | 5 |  |  | -0.35 |
