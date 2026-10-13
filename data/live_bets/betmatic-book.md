# BetMatic book (paper until BetMatic is live)

Every meeting run as if a pre-open order file (betmatic_orders.py) had gone to BetMatic: orders fill at Form King's
opening price when it is at or over their minimum odds; $100 a unit; settled with scratching deductions. See the
BetMatic standard in TIPPING_RULES.md.

| Meeting | Race | Horse | Orders filled | Price | Stake | Result | P/L (u) |
|---|---|---|---|---|---|---|---|
| 2026-10-14 Caulfield (G4) | R2 | True Rebel | 2 of 7 | $8.00 | 1.01u | | |
| 2026-10-14 Caulfield (G4) | R4 | Savisanta | 3 of 7 | $10.00 | 0.91u | | |
| 2026-10-14 Caulfield (G4) | R5 | Jett Smash | 1 of 6 | $4.40 | 1.47u | | |
| 2026-10-14 Caulfield (G4) | R7 | Darkbonee | 1 of 7 | $4.80 | 1.30u | | |
| 2026-10-14 Caulfield (G4) | R8 | Verdoux | 3 of 7 | $26.00 | 0.35u | | |
| 2026-10-15 Warrnambool (G4) | R3 | Who I Think I Am | 4 of 4 | $6.00 | 2.50u | | |
| 2026-10-15 Warrnambool (G4) | R6 | Buzitup | 2 of 7 | $11.00 | 0.66u | | |
| 2026-10-15 Warrnambool (G4) | R7 | Both Sides Now | 1 of 7 | $15.00 | 0.38u | | |

Order files (data/live_bets/DAYPREFIX-betmatic-preopen.csv) rebuilt 14 Oct with the 8-step staking (each step sized at the
next step's price, t_betmatic_tiers.py: +18% profit on the holdout over the first 3-step version), from the model's own
prices before the market (Caulfield from Monday evening's price file, Warrnambool from Tuesday's). Caulfield 14 Oct:
250 orders on 37 runners, 10 filled, 5.04u; Katoto's orders void (scratched); deductions measured on race morning R2 31c
(Katoto, Boys Bounce, Refuse To Curtsy), R4 5c, R5 9c, R7 0c, R8 3c. Warrnambool 15 Oct: 199 orders on 31 runners, 7
filled, 3.54u; Kid Dynamite (R8) missed by under 1%.
