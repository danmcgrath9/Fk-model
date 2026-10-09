# Forward test: the model's whole book at opening prices, settled

Every bet the current rules flag at each meeting's opening prices (not just the bets taken or tweeted).
Live stakes from stake_rule.py ($100 a unit, most 5u); flat = 1u a bet. CLV = opening price over Betfair SP (above 1 = we beat the close).

| Meeting | Bets | Won | Staked | P/L live | P/L flat | Avg CLV | Beat BSP |
|---|---|---|---|---|---|---|---|
| Mon 5 Oct Pakenham | 6 | 0 | 6.53u | -6.53u | -6.00u | 1.31 | 4/6 |
| Tue 6 Oct Mildura (G4) | 2 | 1 | 2.22u | +3.91u | +2.20u | 0.68 | 0/2 |
| Wed 7 Oct Geelong (Soft) | 5 | 2 | 7.84u | +14.65u | +4.30u | 1.26 | 3/5 |
| Thu 8 Oct Kyneton (G4) | 9 | 1 | 13.04u | -6.28u | -4.40u | 1.12 | 5/9 |
| Fri 9 Oct Ballarat (G4) | 5 | 0 | 3.93u | -3.93u | -5.00u | 0.72 | 1/5 |
| Fri 9 Oct Cranbourne (G4) | 2 | 0 | 1.58u | -1.58u | -2.00u | 1.06 | 1/2 |
| **Total** | **29** | **4** | **35.14u** | **+0.24u (+1%)** | **-10.90u** | **1.08** | **14/29** |

## Every bet

| Meeting | Race | Horse | Open | Ours | Stake | Finish | BSP | P/L |
|---|---|---|---|---|---|---|---|---|
| Mon 5 Oct Pakenham | R2 | Sneaky Russian | $7 | $5.71 | 0.83u | 2 | $5.90 | -0.83 |
| Mon 5 Oct Pakenham | R3 | Genomic | $10 | $4.85 | 2.27u | 4 | $3.58 | -2.27 |
| Mon 5 Oct Pakenham | R5 | Doublet | $19 | $12.95 | 0.82u | 6 | $16.40 | -0.82 |
| Mon 5 Oct Pakenham | R5 | Cowboykickedfive | $16 | $10.73 | 1.04u | 3 | $19.50 | -1.04 |
| Mon 5 Oct Pakenham | R5 | Latassa | $13 | $10.46 | 0.67u | 2 | $16.00 | -0.67 |
| Mon 5 Oct Pakenham | R8 | Sky Watcher | $10 | $7.28 | 0.9u | 2 | $9.23 | -0.90 |
| Tue 6 Oct Mildura (G4) | R5 | Piwhane | $10 | $7.61 | 0.76u | 3 | $15.00 | -0.76 |
| Tue 6 Oct Mildura (G4) | R6 | Verona Rupes | $4.2 | $3.47 | 1.46u | 1 | $6.00 | +4.67 |
| Tue 6 Oct Mildura (G4) | R7 | Boulderoo | $13 | $10.64 | 0.41u | scratched | | 0 |
| Wed 7 Oct Geelong (Soft) | R2 | Nightowl | $15 | $9.67 | 0.82u | 6 | $12.00 | -0.82 |
| Wed 7 Oct Geelong (Soft) | R3 | Silky Seth | $3.8 | $3.14 | 1.67u | 2 | $6.73 | -1.67 |
| Wed 7 Oct Geelong (Soft) | R4 | Mr Natural | $3.8 | $2.94 | 2.3u | 1 | $2.82 | +6.44 |
| Wed 7 Oct Geelong (Soft) | R7 | Mount Sabyinyo | $14 | $10.52 | 0.55u | 2 | $14.14 | -0.55 |
| Wed 7 Oct Geelong (Soft) | R8 | Stay Humble | $5.5 | $3.30 | 2.5u | 1 | $2.57 | +11.25 |
| Thu 8 Oct Kyneton (G4) | R1 | Corviglia | $4.6 | $3.71 | 1.47u | 1 | $6.00 | +5.29 |
| Thu 8 Oct Kyneton (G4) | R1 | Windhowler | $19 | $10.03 | 0.98u | 7 | $34.00 | -0.98 |
| Thu 8 Oct Kyneton (G4) | R3 | Oceans Blue | $3.3 | $2.50 | 2.5u | 2 | $1.86 | -2.50 |
| Thu 8 Oct Kyneton (G4) | R6 | Ranakye | $9.5 | $5.41 | 1.8u | 11 | $9.06 | -1.80 |
| Thu 8 Oct Kyneton (G4) | R6 | Yellowknife | $12 | $6.44 | 1.56u | 2 | $11.45 | -1.56 |
| Thu 8 Oct Kyneton (G4) | R6 | Rose Of Shalaa | $11 | $7.55 | 0.97u | 9 | $5.12 | -0.97 |
| Thu 8 Oct Kyneton (G4) | R7 | Ataegina | $5 | $4.08 | 1.25u | 3 | $7.58 | -1.25 |
| Thu 8 Oct Kyneton (G4) | R8 | Brutalrule | $7.5 | $5.80 | 0.99u | 7 | $6.02 | -0.99 |
| Thu 8 Oct Kyneton (G4) | R9 | Blue Moon Summit | $18 | $7.48 | 1.52u | 6 | $22.53 | -1.52 |
| Fri 9 Oct Ballarat (G4) | R5 | Old Time Rock | $17 | $12.61 | 0.47u | 7 | $80.00 | -0.47 |
| Fri 9 Oct Ballarat (G4) | R6 | Russian Sky | $11 | $7.55 | 1.45u | 3 | $14.50 | -1.45 |
| Fri 9 Oct Ballarat (G4) | R8 | Chantra | $17 | $11.36 | 0.65u | 5 | $16.00 | -0.65 |
| Fri 9 Oct Ballarat (G4) | R8 | Mister Martini | $19 | $14.72 | 0.35u | 2 | $22.00 | -0.35 |
| Fri 9 Oct Ballarat (G4) | R9 | Aka Daka | $13 | $8.20 | 1.01u | 2 | $18.00 | -1.01 |
| Fri 9 Oct Cranbourne (G4) | R4 | Sisterly | $34 | $14.85 | 1.09u | 5 | $24.86 | -1.09 |
| Fri 9 Oct Cranbourne (G4) | R6 | Art 'n' Soul | $16 | $11.93 | 0.49u | 7 | $21.00 | -0.49 |

## Read, 9 Oct (29 bets)

4 winners against 4.8 expected at our prices (sd 1.9) and 3.8 at the market's BSP. The winners were the short ones
(Verona Rupes, Mr Natural, Stay Humble, Corviglia); every bet at $9.50 or longer lost, which is why flat stakes are -10.9u
while live stakes (bigger on the shorter, higher-edge bets) are square. Our prices said +14.7u flat was the expectation,
so we are about 1.3 sd under it: a bad week, not yet a signal. Beat BSP on 14 of 29; Ballarat drifted on 4 of 5 (the
drifters-lose finding again). Opening = the first Form King snapshot with a market up (Cranbourne: Thursday 9:30am, so
Sisterly and Art 'n' Soul, not the later Piastri and Small Town Hero). Kyneton's v6 is the race-morning file.
