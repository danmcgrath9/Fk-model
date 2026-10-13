# Forward test: the model's whole book at opening prices, settled

Every bet the current rules flag at each meeting's opening prices (not just the bets taken or tweeted).
Live stakes from stake_rule.py ($100 a unit, most 5u); flat = 1u a bet. CLV = opening price over Betfair SP (above 1 = we beat the close).

| Meeting | Bets | Won | Staked | P/L live | P/L flat | Avg CLV | Beat BSP |
|---|---|---|---|---|---|---|---|
| Mon 5 Oct Pakenham | 3 | 0 | 3.99u | -3.99u | -3.00u | 1.68 | 3/3 |
| Tue 6 Oct Mildura (G4) | 1 | 0 | 0.76u | -0.76u | -1.00u | 0.67 | 0/1 |
| Wed 7 Oct Geelong (Soft) | 4 | 2 | 7.29u | +9.32u | +2.93u | 1.33 | 3/4 |
| Thu 8 Oct Kyneton (G4) | 7 | 1 | 9.72u | -3.24u | -2.59u | 1.17 | 4/7 |
| Fri 9 Oct Ballarat (G4) | 1 | 0 | 0.86u | -0.86u | -1.00u | 2.29 | 1/1 |
| Fri 9 Oct Cranbourne (G4) | 1 | 0 | 0.49u | -0.49u | -1.00u | 0.76 | 0/1 |
| Sat 10 Oct Caulfield (G4) | 2 | 0 | 2.23u | -2.23u | -2.00u | 0.73 | 0/2 |
| Sun 11 Oct Seymour (G4) | 9 | 0 | 13.98u | -13.98u | -9.00u | 0.95 | 4/9 |
| Tue 13 Oct Kilmore (S5) | 1 | 0 | 0.58u | -0.58u | -1.00u | 1.09 | 1/1 |
| **Total** | **29** | **3** | **39.90u** | **-16.80u (-42%)** | **-17.66u** | **1.15** | **16/29** |

## Every bet

| Meeting | Race | Horse | Open | Ours | Stake | Finish | BSP | Deduction | P/L |
|---|---|---|---|---|---|---|---|---|---|
| Mon 5 Oct Pakenham | R3 | Genomic | $10 | $4.85 | 2.27u | 4 | $3.58 |  | -2.27 |
| Mon 5 Oct Pakenham | R5 | Doublet | $19 | $12.95 | 0.82u | 6 | $16.40 |  | -0.82 |
| Mon 5 Oct Pakenham | R8 | Sky Watcher | $10 | $7.28 | 0.9u | 2 | $9.23 |  | -0.90 |
| Tue 6 Oct Mildura (G4) | R5 | Piwhane | $10 | $7.61 | 0.76u | 3 | $15.00 |  | -0.76 |
| Wed 7 Oct Geelong (Soft) | R2 | Nightowl | $15 | $9.67 | 0.82u | 6 | $12.00 | 15c | -0.82 |
| Wed 7 Oct Geelong (Soft) | R3 | Silky Seth | $3.8 | $3.14 | 1.67u | 2 | $6.73 |  | -1.67 |
| Wed 7 Oct Geelong (Soft) | R4 | Mr Natural | $3.8 | $2.94 | 2.3u | 1 | $2.82 | 8c | +5.93 |
| Wed 7 Oct Geelong (Soft) | R8 | Stay Humble | $5.5 | $3.30 | 2.5u | 1 | $2.57 | 48c | +5.88 |
| Thu 8 Oct Kyneton (G4) | R1 | Corviglia | $4.6 | $3.71 | 1.47u | 1 | $6.00 | 5c | +5.01 |
| Thu 8 Oct Kyneton (G4) | R1 | Windhowler | $19 | $10.03 | 0.98u | 7 | $34.00 | 5c | -0.98 |
| Thu 8 Oct Kyneton (G4) | R3 | Oceans Blue | $3.3 | $2.50 | 2.5u | 2 | $1.86 | 12c | -2.50 |
| Thu 8 Oct Kyneton (G4) | R6 | Yellowknife | $12 | $6.44 | 1.56u | 2 | $11.45 | 37c | -1.56 |
| Thu 8 Oct Kyneton (G4) | R6 | Rose Of Shalaa | $11 | $7.55 | 0.97u | 9 | $5.12 | 37c | -0.97 |
| Thu 8 Oct Kyneton (G4) | R7 | Ataegina | $5 | $4.08 | 1.25u | 3 | $7.58 |  | -1.25 |
| Thu 8 Oct Kyneton (G4) | R8 | Brutalrule | $7.5 | $5.80 | 0.99u | 7 | $6.02 | 14c | -0.99 |
| Fri 9 Oct Ballarat (G4) | R8 | She's Stargazing | $41 | $13.59 | 0.86u | 11 | $17.89 |  | -0.86 |
| Fri 9 Oct Cranbourne (G4) | R6 | Art 'n' Soul | $16 | $11.93 | 0.49u | 7 | $21.00 |  | -0.49 |
| Sat 10 Oct Caulfield (G4) | R4 | Campaldino | $26 | $8.46 | 1.41u | 11 | $33.98 | 4c | -1.41 |
| Sat 10 Oct Caulfield (G4) | R6 | Grand Larceny | $16 | $10.04 | 0.82u | 4 | $22.80 |  | -0.82 |
| Sun 11 Oct Seymour (G4) | R1 | More Foxie | $5 | $3.16 | 2.5u | 7 | $4.86 | 22c | -2.50 |
| Sun 11 Oct Seymour (G4) | R5 | Yahoo Bar | $8.5 | $6.80 | 0.74u | 2 | $10.50 | 14c | -0.74 |
| Sun 11 Oct Seymour (G4) | R6 | Ulfberht | $17 | $7.94 | 1.36u | 7 | $26.00 | 27c | -1.36 |
| Sun 11 Oct Seymour (G4) | R7 | Bajaria | $3 | $2.42 | 3.75u | 3 | $2.96 | 9c | -3.75 |
| Sun 11 Oct Seymour (G4) | R8 | Castellar | $12 | $8.66 | 0.75u | 7 | $9.60 | 15c | -0.75 |
| Sun 11 Oct Seymour (G4) | R9 | Justadeel | $11 | $8.95 | 0.51u | 7 | $18.30 | 18c | -0.51 |
| Sun 11 Oct Seymour (G4) | R10 | Chest Of Gold | $26 | $12.03 | 0.88u | 13 | $17.13 | 37c | -0.88 |
| Sun 11 Oct Seymour (G4) | R10 | Chicago Blues | $14 | $8.60 | 0.99u | 8 | $16.50 | 37c | -0.99 |
| Sun 11 Oct Seymour (G4) | R10 | Savoyard | $2.6 | $2.04 | 2.5u | 5 | $3.05 | 37c | -2.50 |
| Tue 13 Oct Kilmore (S5) | R7 | Winter Nights | $18 | $12.30 | 0.58u | 3 | $16.44 | 18c | -0.58 |
