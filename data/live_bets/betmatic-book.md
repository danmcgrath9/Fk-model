# BetMatic book (paper until BetMatic is live)

Every meeting run as if a pre-open order file (betmatic_orders.py) had gone to BetMatic: orders fill at Form King's
opening price when it is at or over their minimum odds; $100 a unit; settled with scratching deductions. See the
BetMatic standard in TIPPING_RULES.md.

| Meeting | Race | Horse | Orders filled | Price | Stake | Result | P/L (u) |
|---|---|---|---|---|---|---|---|
| 2026-10-14 Caulfield (G4) | R2 | True Rebel | 2 of 7 | $8.00 | 1.01u | 2nd (nose), SP $2.80 | -1.01 |
| 2026-10-14 Caulfield (G4) | R4 | Savisanta | 3 of 7 | $10.00 | 0.91u | 3rd, SP $5 | -0.91 |
| 2026-10-14 Caulfield (G4) | R5 | Jett Smash | 1 of 6 | $4.40 | 1.47u | lost, SP $2.50 | -1.47 |
| 2026-10-14 Caulfield (G4) | R7 | Darkbonee | 1 of 7 | $4.80 | 1.30u | 2nd (head), SP $3.10 | -1.30 |
| 2026-10-14 Caulfield (G4) | R8 | Verdoux | 3 of 7 | $26.00 | 0.35u | 5th, SP $12 | -0.35 |
| 2026-10-15 Warrnambool (G4) | R3 | Who I Think I Am | 2 of 2 | $6.00 | 2.50u | WON (SP $4.40) | +12.50 |
| 2026-10-15 Warrnambool (G4) | R6 | Buzitup | 1 of 2 | $11.00 | 0.71u | WON (SP $7, 13c deduction) | +6.18 |
| 2026-10-15 Warrnambool (G4) | R7 | Both Sides Now | 1 of 2 | $15.00 | 0.50u | lost (Cute Girl won) | -0.50 |
| 2026-10-16 Cranbourne (G4) | R6 | Hollandia | 1 of 2 | $21.00 | 0.34u | | |
| 2026-10-17 Caulfield (G4) | R2 | Autumn In Grinzing | 2 of 2 | $41.00 | 0.44u | | |
| 2026-10-17 Caulfield (G4) | R2 | Voynichese | 1 of 2 | $9.50 | 0.91u | | |
| 2026-10-17 Caulfield (G4) | R3 | Stardom | 1 of 2 | $15.00 | 0.54u | | |
| 2026-10-17 Caulfield (G4) | R4 | Aemond | 2 of 2 | $13.00 | 0.85u | | |
| 2026-10-17 Caulfield (G4) | R6 | Hidden Motive | 1 of 2 | $13.00 | 0.58u | | |
| 2026-10-17 Caulfield (G4) | R7 | Over The Bridge | 2 of 2 | $6.00 | 2.00u | | |
| 2026-10-17 Caulfield (G4) | R7 | Saintly Dancer | 2 of 2 | $7.00 | 1.64u | | |
| 2026-10-17 Caulfield (G4) | R8 | Threads | 1 of 2 | $15.00 | 0.46u | | |
| 2026-10-17 Caulfield (G4) | R9 | Cosmic Crusader | 1 of 2 | $5.00 | 1.54u | | |
| 2026-10-17 Caulfield (G4) | R9 | Kingswood | 2 of 2 | $25.00 | 0.59u | | |
| 2026-10-17 Caulfield (G4) | R10 | Shadhavar | 2 of 2 | $7.50 | 1.88u | | |

Order files (data/live_bets/DAYPREFIX-betmatic-preopen.csv) rebuilt 14 Oct with the 8-step staking (each step sized at the
next step's price, t_betmatic_tiers.py: +18% profit on the holdout over the first 3-step version), from the model's own
prices before the market (Caulfield from Monday evening's price file, Warrnambool from Tuesday's). Caulfield 14 Oct:
250 orders on 37 runners, 10 filled, 5.04u; Katoto's orders void (scratched); deductions TAB actually applied at its opening price
(founder's account): R2 20c, R4 2c, R5 2c, R7 0c, R8 0c (the estimate was 31c, 5c, 9c, 0c, 3c; actuals now override it,
data/live_bets/DAYPREFIX-deductions-actual.txt).
Caulfield 14 Oct settled (founder, 14 Oct): no winner, -5.04u. Every fill was taken well over its starting price (price after
TAB deduction against SP: True Rebel $6.60/$2.80, Savisanta $9.82/$5, Jett Smash $4.32/$2.50, Darkbonee $4.80/$3.10,
Verdoux $26/$12): about 2x the SP on average. True Rebel beaten a nose. Warrnambool 15 Oct: 199 orders on 31 runners, 7
filled, 3.54u; Kid Dynamite (R8) missed by under 1%.
Cranbourne 16 Oct (Form King open, Wed 5:00pm): 3 orders filled on 3 runners, but Truant (R1, $5.50) and Naked Light (R2, $11) sit in races
where a first starter opens $6 or shorter, so the race rule voids them: 1 bet, Hollandia 0.34u. Caulfield 17 Oct (Form King open, Wed 3:48pm):
17 orders on 11 runners, 11.43u; none opened past its maximum price (Autumn In Grinzing $41 against a $41.06 ceiling, the closest).

## 9:30am top-ups (paper, tracked from 14 Oct 2026)
Each race day at 9:30am, after scratchings: prices refreshed, our market re-priced on the final field, and every bet that
was value at its open and is still at or over take-at at the 9:30am price topped up to the full sheet stake, less what
the BetMatic orders already got (research/form_gbm/topup.py, DAYPREFIX-topups.csv). No deduction (struck after the
scratchings). The backtest says the top-up slice loses (t_topup.py: -7.6% holdout at BSP; t_topup_timed.py: 6 top-ups on
41 timed races, -27%), so this is a live sample to confirm or overturn that, not a rule.

| Meeting | Race | Horse | Opened | 9:30am price | Ours (final field) | BetMatic stake | Top-up | Result | P/L (u) |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-15 Warrnambool | R3 | Who I Think I Am | $6.00 | $4.60 | $3.73 | 2.50u | 0.40u | WON | +1.44 |
| 2026-10-16 Cranbourne | R1 | Locard | $7.50 | $8.00 | $4.62 | 0.00u | 3.17u | | |
| 2026-10-16 Cranbourne | R8 | Hustle In Heels | $5.50 | $5.50 | $4.49 | 0.00u | 2.21u | | |
| 2026-10-17 Caulfield | R9 | Kingswood | $25.00 | $26.00 | $13.03 | 0.59u | 0.18u | | |
| 2026-10-17 Avoca | R3 | Miss Home Body | $10.50 | $9.00 | $6.47 | 0.00u | 1.58u | | |

Warrnambool 15 Oct (re-priced 9:34am Thursday, 11 scratched, jockeys and gear in): 6 value-at-open runners on the final field, 1 top-up, Who I Think I Am 0.40u at $4.60; the rest are under take-at now.
Caulfield 14 Oct (re-priced 8:45am): 5 value-at-open runners on the final field, all under take-at at race-morning prices, so no top-ups.

Rebuilt 14 Oct (founder: "Rebuild anything that's live... to update our paper bets"), the three unsettled meetings, with
the final-field guard (betmatic_orders.py drops emergencies and scratchings and re-spreads the probability) and 3 price
steps: Warrnambool 15 Oct (was 8 steps, 199 orders; now 61 orders on 31 runners, 3.71u: Buzitup 0.66u to 0.71u, Both
Sides Now 0.38u to 0.50u, Who I Think I Am unchanged at 2.50u; its file was already priced without its emergency, Tue
11:37am, before the 5:17pm open). Caulfield 17 Oct: Pillow Fight (R10) was already scratched in the Wed 3:48pm opening
snapshot, so R10 is re-priced without him: Shadhavar 1.78u to 1.88u, 11.43u in all. Cranbourne 16 Oct unchanged (1 bet,
Hollandia 0.34u). Every change uses only what was known at the open. The files sent before are in git history.

Cranbourne 16 Oct (re-priced 9:34am Fri on the final field, v10; the BetMatic orders were never sent, so the stage-1 stake is 0): 7 value-at-open runners, 2 top-ups (5.38u), the other 5 under take-at at the 9:30 price.

Saturday 17 Oct (re-priced 9:35am Sat on the final field, v10; Caulfield with jockeys in): Caulfield 13 value-at-open runners, 1 top-up (Kingswood 0.18u at $26); Cosmic Crusader also flagged a 2.05u top-up at $5.50 and is NOT logged, because the founder removed him on Friday (the model under-rates the overseas runners, so it over-rates him). Bendigo 4 value-at-open, Wodonga 3, all under take-at now: no top-ups. Avoca 3 value-at-open, 1 top-up (Miss Home Body 1.58u at $9; her BetMatic orders fired early and were skipped on balance, so the stage-1 stake is 0).
