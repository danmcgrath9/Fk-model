# BetMatic book

Two books from 19 Oct 2026 (founder: "All I want is bets, wins, stake invested and ROI... a punter might be $10 and one
might be $100. For those paper bets that is. Now to keep an actual P&L let's just keep it to what I actually bet"):

- ACTUAL P&L: real money only, the bets TAB actually took (BetMatic's records and TAB's deductions), in dollars at the
  unit size actually used. Starts Wednesday 21 Oct at $25 a unit.
- PAPER: everything else (orders that did not fire, meetings before going live, 9:30am top-ups), in UNITS only: bets,
  wins, units staked, units P/L, ROI. No dollar figures, because a follower's unit can be $10 or $100.

## Actual P&L (real money)

| Date | Meeting | Unit | Bets | Won | Staked | Returned | P/L | ROI |
|---|---|---|---|---|---|---|---|---|
| 2026-10-21 | Geelong | $25 | 1 (Murshidi; Jenni You Think scratched, $49 refunded) | 1 | $126 (5.04u) | $1,386 | **+$1,260 (+50.40u)** | +1000% |

Placed so far (Mon 19 Oct, for Wednesday): Geelong R5 Murshidi (#7), $126 (5.04u) at $11, our price $3.81, both order steps filled at TAB's open 11:45am Monday. Tweeted by the founder the same morning as 5u at $11 (locked). Card posted Monday afternoon records it at $6.50 (5u), founder's call; the real-money line stays $126 at $11. Runs: no deduction in R5 (founder, Wed 21 Oct). **WON** (SP $3.70, BSP $3.94): $126 at $11 returns $1,386, +$1,260 (+50.40u). Taken at 2.8x BSP. Twitter: 5u at $11, +50u.
Geelong R6 Jenni You Think (#12), $49 (1.96u) at $12 before deductions, our price $8.73, first order step filled at TAB's open Monday (the second needed $14.64). SCRATCHED Wed 21 Oct morning (founder): void, $49 refunded, a no-bet on Twitter, not a loss. Firm tier, double stake. Geelong R4 Karren: no bet, TAB opened $2.60 under the $2.75 minimum.
Geelong R1-R3: NOTHING PLACED, BetMatic late again. R3 triggered 4:11:12pm Monday, the bot saw Alero $11 (min $13.03; opened $15) and Attachments $9.50 (min $14.15); the other 8 R3 orders had not triggered by 4:13pm, cancelled and resent as Now bets (nothing matched). R1/R2 show triggered but the bot never received them. Reported to BetMatic.
Blocked, paper only (to test the rule): Geelong R4 Mr Natural (#14), our price $10.08, blocked by the bounce rule (last start a new peak, 83.2 vs best 78.7); TAB opened $21, firmed to $7 by 3:30pm Monday. Karren drifted $2.60 to $2.70, still under $2.75: no bet. Then out to $3.70 by about 3:45pm Monday (a 5u bet under the after-open rule, $2.78+); founder's call, NO BET on a drift that big. Paper line to learn from: Karren, $3.70, would-be 5u.

Running total: settles Wednesday 21 Oct.

## Paper (units only)

Paper to 18 Oct (forward test, the stakes as sent): 61 bets, 14 won, 64.50u staked, +72.05u, ROI +112%.
Echuca 19 Oct (opening bets, paper because the market opened before going live): 4 bets, 2 won, 3.85u staked, +17.39u, ROI +452%. Price taken after deductions against BSP: 1.64x on average (Mickio $7.18 v $3.00, Lim's Ida $19.25 v $13.84, Wozza $9.10 v $4.93, Prestige Fantastic $21.50 v $23).
Paper to 19 Oct: 65 bets, 16 won, 68.35u staked, +89.44u, ROI +131%.
Kyneton 20 Oct (settled 21 Oct at the POSTED stakes, not the firm/drift ones): 4 bets (Sabrina scratched), 2 won, 6.77u staked, +7.88u, ROI +116%. Price taken after deductions against BSP: Tuzemak $3.43 v $1.81, Bourne Legacy $2.92 v $2.74, Bliss Bomb $4.65 v $2.80; Biratu pending (Form King has no R7 results yet, re-pulled 21 Oct, still empty).
Paper to 20 Oct: 69 bets, 18 won, 75.12u staked, +97.32u, ROI +130%. Beat BSP on 21 of 27 bets with a BSP, 1.57x BSP on average.

Each meeting run as if the pre-open order file (betmatic_orders.py) had fired: orders fill at Form King's opening price
when it is at or over their minimum odds; settled with scratching deductions. See the BetMatic standard in
TIPPING_RULES.md.

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
| 2026-10-17 Caulfield (G4) | R2 | Autumn In Grinzing | 2 of 2 | $41.00 | 0.44u | 6th, SP $16 | -0.44 |
| 2026-10-17 Caulfield (G4) | R2 | Voynichese | 1 of 2 | $9.50 | 0.91u | 7th, SP $8 | -0.91 |
| 2026-10-17 Caulfield (G4) | R3 | Stardom | 1 of 2 | $15.00 | 0.54u | 5th, SP $11 | -0.54 |
| 2026-10-17 Caulfield (G4) | R4 | Aemond | 2 of 2 | $13.00 | 0.85u | 9th, SP $7.50 | -0.85 |
| 2026-10-17 Caulfield (G4) | R6 | Hidden Motive | 1 of 2 | $13.00 | 0.58u | 9th, SP $9 | -0.58 |
| 2026-10-17 Caulfield (G4) | R7 | Over The Bridge | 2 of 2 | $6.00 | 2.00u | 11th, SP $5.50 | -2.00 |
| 2026-10-17 Caulfield (G4) | R7 | Saintly Dancer | 2 of 2 | $7.00 | 1.64u | WON (SP $4.60) | +9.74 |
| 2026-10-17 Caulfield (G4) | R8 | Threads | 1 of 2 | $15.00 | 0.46u | 7th, SP $3.90 | -0.46 |
| 2026-10-17 Caulfield (G4) | R9 | Cosmic Crusader | 1 of 2 | $5.00 | 1.54u | removed Fri 16 Oct, no bet (ran 4th, SP $4.80) | 0.00 |
| 2026-10-17 Caulfield (G4) | R9 | Kingswood | 2 of 2 | $25.00 | 0.59u | WON, Caulfield Cup (SP $26) | +14.16 |
| 2026-10-17 Caulfield (G4) | R10 | Shadhavar | 2 of 2 | $7.50 | 1.88u | WON (SP $3.60) | +10.68 |
| 2026-10-17 Bendigo (G4) | R2 | Genomic | 2 of 2 | $11.00 | 1.91u | 5th, SP $3.50 | -1.91 |
| 2026-10-17 Bendigo (G4) | R7 | Carnival Riches | 1 of 2 | $13.00 | 0.64u | WON (SP $6) | +7.68 |
| 2026-10-17 Wodonga (G4) | R3 | Moral Turpitude | 1 of 2 | $9.00 | 0.94u | 6th, SP $5 | -0.94 |
| 2026-10-17 Wodonga (G4) | R4 | Stand By Me Ned | 1 of 2 | $11.00 | 0.71u | 5th, SP $9 | -0.71 |
| 2026-10-17 Wodonga (G4) | R6 | Black Panther | 2 of 2 | $8.50 | 1.51u | 8th, SP $5.50 | -1.51 |
| 2026-10-18 Horsham (G4) | R5 | Bazzar | 1 of 2 | $6.00 | 1.55u | WON (SP $2.30, BSP $2.25) | +7.75 |
| 2026-10-18 Horsham (G4) | R8 | Surfy Pete | 2 of 2 | $9.00 | 1.43u | 9th, SP $3.70, BSP $4.35 | -1.43 |
| 2026-10-18 Moe (G4) | R5 | Sleeping Tiger | 2 of 2 | $9.50 | 1.34u | 3rd, SP $8.50, BSP $12 | -1.34 |
| 2026-10-18 Moe (G4) | R6 | Ze Bee Nine | 2 of 2 | $14.50 | 0.79u | 9th, SP $8.50, BSP $11.48 | -0.79 |
| 2026-10-18 Moe (G4) | R7 | Preservator | 1 of 2 | $7.33 | 1.00u | 6th, SP $9.50, BSP $8.67 | -1.00 |
| 2026-10-19 Echuca (G4) | R1 | Prestige Fantastic | open | $26.00 (18c ded.) | 0.47u | 8th, SP $18, BSP $23 | -0.47 |
| 2026-10-19 Echuca (G4) | R5 | Mickio | open | $7.50 ($7.18 after 5c ded.) | 1.86u | WON (SP $2.80, BSP $3.00) | +11.49 |
| 2026-10-19 Echuca (G4) | R6 | Lim's Ida | open | $26.00 ($19.25 after 27c ded.) | 0.41u | WON (SP $9, BSP $13.84) | +7.48 |
| 2026-10-19 Echuca (G4) | R7 | Here Comes Wozza | open | $11.00 ($9.10 after 19c ded.) | 1.11u | 9th, SP $4, BSP $4.93 | -1.11 |
| 2026-10-20 Kyneton (G3.5) | R1 | Tuzemak | posted | $3.50 ($3.43 after 3c ded.) | 2.50u | WON (SP $1.65, BSP $1.81) | +6.08 |
| 2026-10-20 Kyneton (G3.5) | R3 | Bourne Legacy | posted | $3.40 ($2.92 after 20c ded.) | 2.15u | 2nd, SP $2.70, BSP $2.74. Flagged: against the race first-starter rule | -2.15 |
| 2026-10-20 Kyneton (G3.5) | R3 | Sabrina | posted | $26.00 | 0.52u | scratched, refunded | 0.00 |
| 2026-10-20 Kyneton (G3.5) | R4 | Bliss Bomb | posted | $6.00 ($4.65 after 27c ded.) | 1.46u | 2nd, SP $2.60, BSP $2.80 | -1.46 |
| 2026-10-20 Kyneton (G3.5) | R7 | Biratu | posted | $11.00 ($9.20 after 18c ded.) | 0.66u | WON (founder); SP and BSP not yet in Form King, R7 unresulted on 21 Oct | +5.41 |

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
| 2026-10-17 Caulfield | R9 | Kingswood | $25.00 | $26.00 | $13.03 | 0.59u | 0.18u | WON (SP $26) | +4.50 |
| 2026-10-17 Avoca | R3 | Miss Home Body | $10.50 | $9.00 | $6.47 | 0.00u | 1.58u | 3rd, SP $10 | -1.58 |
| 2026-10-18 Horsham | R5 | Makarim | $16.00 | $16.00 | $11.46 | 0.00u | 0.57u | 7th, SP $14 | -0.57 |
| 2026-10-18 Horsham | R8 | Weather Delay | $7.00 | $7.50 | $5.50 | 0.00u | 1.21u | 3rd, SP $9 | -1.21 |
| 2026-10-18 Moe | R6 | Gatsby Crown | $8.50 | $10.00 | $7.08 | 0.00u | 0.98u | 10th, SP $10 | -0.98 |
| 2026-10-18 Moe | R6 | Ze Bee Nine | $14.50 | $14.00 | $9.40 | 0.79u | 0.01u | 9th, SP $8.50 | -0.01 |
| 2026-10-19 Echuca | R6 | Ice Quake | $8.50 | $7.00 | $5.30 | 0.00u | 1.95u | 2nd, SP $6.50, BSP $6.73 | -1.95 |
| 2026-10-21 Geelong | R2 | Superliv | $15.00 | $18.00 | $12.14 | 0.00u | 1.00u | 3rd, SP $13, BSP $17 | -1.00 |
| 2026-10-21 Geelong | R6 | Stay Humble | $5.50 | $5.50 | $3.96 | 0.00u | 3.11u | 3rd, SP $3.60, BSP $4.04 | -3.11 |
| 2026-10-21 Geelong | R7 | Litzdeel (Geelong Cup: internationals in the field, flagged) | $6.00 | $6.00 | $4.88 | 0.00u | 1.71u | 5th, SP $5.50, BSP $7 | -1.71 |
| 2026-10-21 Geelong | R8 | Keep Your Cool | $7.50 | $7.00 | $5.81 | 0.00u | 1.27u | 3rd, SP $8.50, BSP $11.88 | -1.27 |
| 2026-10-26 Wangaratta | R1 | Kinky Mistress | $5.00 | $3.60 | $2.77 | 0.00u | 4.22u | 2nd, SP $3.80, BSP $4.67 | -4.22 |
| 2026-10-26 Wangaratta | R3 | Princess Geisha | $15.50 | $14.00 | $11.15 | 0.00u | 0.73u | WON (SP $9.50, BSP $11.72) | +9.49 |
| 2026-10-26 Wangaratta | R3 | Somethingintheair | $13.50 | $15.00 | $11.09 | 0.00u | 0.91u | 3rd, SP $11, BSP $14.50 | -0.91 |
| 2026-10-26 Wangaratta | R3 | Brilliant Bull Ant | $13.50 | $16.00 | $10.34 | 0.00u | 1.27u | 6th, SP $9, BSP $12.50 | -1.27 |
| 2026-10-27 Swan Hill | R2 | Magna Sententia (R2 has first starters) | $4.00 | $3.50 | $2.90 | 0.00u | 3.09u | 3rd, SP $2.70, BSP $3.04 | -3.09 |
| 2026-10-27 Swan Hill | R7 | His Finest Hour | $6.50 | $7.00 | $5.20 | 0.00u | 2.08u | 7th, SP $4.60, BSP $5.98 | -2.08 |
| 2026-10-27 Swan Hill | R8 | Baganov | $10.00 | $10.00 | $7.90 | 0.00u | 1.08u | 10th, SP $10, BSP $12.50 | -1.08 |
| 2026-10-28 Bendigo | R2 | Centenary Florin | $3.70 | $4.40 | $2.94 | 0.00u | 5.11u | 4th, SP $4.20, BSP $5.12 | -5.11 |
| 2026-10-28 Bendigo | R8 | Litzdeel | $8.50 | $8.50 | $6.24 | 1.48u | 0.26u | 3rd, SP $9, BSP $10 | -0.26 |
| 2026-10-30 Pakenham | R8 | Shidan | $19.00 | $8.00 | $6.64 | 0.00u (opened over the $15.84 max) | 1.09u | | |

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

Saturday 17 Oct settled (results pulled Sat 10:43pm): 15 bets, 15.60u, four winners (Saintly Dancer, Kingswood in the Caulfield Cup at $25, Shadhavar, Carnival Riches). Caulfield +28.80u, Bendigo +5.77u, Wodonga -3.16u: +31.41u, ROI +201%. Deductions from the estimate (no TAB actuals, the orders were not live): Saintly Dancer 6c on the first order, Shadhavar 11c (three scratched in R10), Kingswood 0. Paper top-ups: Kingswood +4.50u, Miss Home Body -1.58u.

Sunday 18 Oct (Form King open: Horsham earlier in the week, Moe Sat night): Horsham 2 bets, 2.98u (Tikemyson's R7 orders void, scratched after winning at Avoca Saturday); Moe 3 bets, 3.13u (The Minstrel Boy opened $2.15, under his $3.50 take-at; Gatsby Crown missed by 9c at $8.50). Paper only: the TAB account was empty, live from Monday 19 Oct. 9:35am Sun re-price on the final field: Horsham 2 top-ups (Makarim 0.57u at $16, Weather Delay 1.21u at $7.50), Moe 2 (Gatsby Crown 0.98u at $10, Ze Bee Nine 0.01u at $14).

Geelong Wed 21 Oct (re-priced 9:45am on the final field: 33 out incl. Jenni You Think): 14 value-at-open runners, 4 top-ups (7.09u), the rest under take-at now. Murshidi (R5, our real bet at $11) firmed to $4.20; ours on the final field $4.66. Litzdeel is in the Geelong Cup, which had no pre-open orders because the internationals make the model unreliable, so his top-up is logged and flagged.

Sunday 18 Oct settled: 5 bets, 6.11u, one winner (Bazzar, taken $6, BSP $2.25). Horsham +6.32u, Moe -3.13u: +3.19u, ROI +52%. Price taken against BSP: 3 of 5 beat it (Bazzar, Surfy Pete, Ze Bee Nine); Sleeping Tiger ($9.50 vs BSP $12) and Preservator ($7.33 vs $8.67) drifted past our price. No deduction recorded on Bazzar (none estimated for R5). Paper top-ups -2.77u.

Friday 23 Oct (re-priced 9:35am Fri on the final field): Cranbourne 12 value-at-open runners, 1 top-up (Pariah Pearl R2 1.41u at $7.50); Eye For An Eye and Superstock already at full stake, Castellar scratched, the rest under take-at. Ballarat (paper, TAB empty at the open) 14 value-at-open runners, 3 top-ups logged (Wavelets R3 0.40u at $12, Circus Circus R5 1.23u at $11, Skjaldmo R7 2.96u at $13); Resonant R4 also flagged 4.93u at $3.10 and is NOT logged (founder left Ballarat R4 out on Wed); Russian Duchess scratched.

Monday 19 Oct Echuca (re-priced 9:33am Mon on the final field, v10; 36 scratched, 11 emergencies in): 9 value-at-open runners, 1 top-up (Ice Quake R6 1.95u at $7), the other 8 under take-at at the 9:30 price. Echuca's market opened Saturday, before going live, so its BetMatic orders never fired (all 70 cleared 10:36am Monday) and its opening bets are paper at Form King's open: 4 horses, 3.85u (Prestige Fantastic 0.47u at $26, Mickio 1.86u at $7.50, Lim's Ida 0.41u at $26, Here Comes Wozza 1.11u at $11).

## Pre-draw test: MV Gold Cup, Flemington R8, Sat 24 Oct (founder, 20 Oct 2026: "use this as a test for future bets")
Recorded Tue 20 Oct 4:38pm, before the barrier draw, on TAB's fixed prices, priced with barrier blank, The Euphrates out (Geelong Cup instead), Manzor Blue checked at market (no change). Paper, not placed.

| Horse | TAB | Ours (pre-draw) | Bet at | Stake |
|---|---|---|---|---|
| Aethelwulf | $8 | $3.16 | $4.65 / $5.81 | 7.76u |

After the draw (Tue 20 Oct 7pm, barriers from the published draw, re-priced with The Euphrates out): Aethelwulf drew 19,
14 of the 15 starters once the scratching and the four emergencies come out. Ours $3.24 on the draw and $3.24 with the
barrier blank on the same run, so the gate is worth nothing to him in our model; orders $4.77 / $5.96, 7.70u if both
fire (pre-draw 7.76u). Correction (Wed 21 Oct): the pre-draw $3.16 was the $3.52 run (The Euphrates still in, because its SCR line carried an
inline comment drop_scr.py does not read) with The Euphrates re-spread out afterwards; re-running with him dropped
rebuilds every field-relative input and gives $3.24. The comment now sits on its own line.
Jockeys, gear and weights still as at Tue 3pm; the Wed 8:30am re-pull checks them.
Cox Plate on the draw: Cosmic Crusader gate 8, ours $5.89 (blank $5.85); founder's bet $11 at Ladbrokes stands.
Wed 21 Oct 8:30am re-pull (Form King, R7/R8): barriers now the real draw in Form King, no weight or gear changes, one
jockey change (King Pedro: Mark Zahra to Damian Lane). Aethelwulf $3.22, orders $4.49 / $5.61, 8.36u if both fire
(stays tweeted at 3.9u, locked). Cosmic Crusader $5.75. Other moves came from Form King's overnight data refresh, not the
draw: every jockey's 12-month figures changed (Rachel King 943 rides at 21.9% to 559 at 14.5%; James McDonald 17.7% to
23.6%) and some neural ratings moved (Warwoven 59.0 to 54.5), so Warwoven $5.01 to $5.93, Aeliana $8.91 to $7.60,
Juja Kibo $8.17 to $7.13. Asked whether Form King changed the jockey window before trusting those moves.
Aethelwulf taken at TAB $8.50 on the draw (founder, 20 Oct evening). Model stake 7.70u. POSTED on Twitter at 3.85u: Twitter stakes are the model stake halved, so the Twitter max is 5u (founder, 20 Oct: "make it out of 5u like that's the max for twitter"). The book records both.

The test: after tonight's draw, re-pull Form King and re-price on the final inputs (barriers, gear, any late jockey changes), and compare the price and stake the model would actually give with the pre-draw ones above, to see which inputs were missing or moved the number. Settle at TAB $8 against SP and BSP after the race.

## Sent Wed 21 Oct for Fri 23 and Sat 24 (Market Open, TAB, $25 a unit)
- Cranbourne Fri 23: 93 orders on 40 runners, all scheduled. No first starters.
- Ballarat Fri 23: 48 orders on 23 runners, all scheduled. Resonant (R4) left out on the founder's call: two first starters in the race
  (Charmingly, Bogey Free). R2 kept with first starter Affair D'or in it (founder's call). R1 and R5 have first starters and no orders.
- Flemington Sat 24 (final fields Wed 11:50am; Form King now has the MV Gold Cup as R7 and the Cox Plate as R8): 86 orders on 41
  runners (Ice Kool's 0.02u step rounds to $0 and is dropped). R2 sent with first starter Regal Harry in it (founder's call: "I have a
  feeling Regal Harry will get scratched"). Aethelwulf and Cosmic Crusader left out of the file: already bet by the founder.
  The other R7/R8 orders (King Pedro, Pinhole, Point Of Law, So You Are; Aeliana, Blind Raise, Ceolwulf, Sir Delius, Warwoven) fired
  straight away because TAB's markets for the two feature races were already up; none was placed (no bet records), and BetMatic
  reports them as already triggered, so nothing is left live. Founder, 21 Oct: R7 and R8 are Aethelwulf and Cosmic Crusader only.
- TAB balance read $0.29 at every send: it must be funded before Friday's opens or TAB refuses what fires.
- CORRECTION (21 Oct 4pm): the Cranbourne R3 $0 records were NOT the TAB balance. Every one reads "Current odds is less
  than the notification odds": TAB opened them under our minimums (Karren $2.70 v $2.82, Escarpa $9 v $13.74, Bajaria $5 v
  $20.91). TAB was funded by 3:45pm ($1,250).
- Cranbourne and Flemington markets opened Wed 21 Oct afternoon. Cranbourne R1, R2 and R4 orders TRIGGERED (R1 2:56pm) but
  the bot never attempted them: no bet record at all (same fault as Geelong R1/R2, Mon 19 Oct). Every other race shows the
  bot's refusal on price. R2's Eye For An Eye (FK open $22, min $16.33) and Superstock (FK open $17.50, min $12.84) were value
  at the open and were missed by that fault; placed by hand after.
- Unit $50 from 21 Oct 4pm (founder). Ballarat's 48 orders cancelled and resent at $50 to fire at the open.

- CORRECTION (founder, Thu 22 Oct): the "never attempted" orders were the TAB account being EMPTY, not a bot fault. With no
  money in the account the bot does not attempt the bet at all, so no bet record is written. That fits the timeline: Mornington
  (Mon afternoon, after Murshidi's $126 took the balance to $0.29), Flemington and Cranbourne R1/R2/R4 (Wed, before TAB was
  funded about 3pm) left no records; Cranbourne R3 at 3:09pm and later races, after funding, show the bot's price refusals.
  Lesson: keep TAB funded to cover every order that can fire at an open.

### Taken, Wed 21 Oct (TAB, real money)
| Meeting | Race | Horse | Price | Stake | Units | Ours | How |
|---|---|---|---|---|---|---|---|
| Cranbourne Fri 23 | R6 | Castellar | $17 | $18 | 0.72u ($25 unit) | $12.41 | open order (min $14.80) |
| Cranbourne Fri 23 | R2 | Eye For An Eye | $23 | $95 | 1.90u | $13.22 | placed after the open, two steps ($73 + $22) |
| Cranbourne Fri 23 | R2 | Superstock | $15 | $98 | 1.96u | $10.39 | placed after the open, first step (second needed $16.05) |
| Flemington Sat 24 | R2 | Turbo Saint | $18 | $26 | 0.52u | $12.30 | after-open, value at FK open $17 |
| Flemington Sat 24 | R9 | Classic Gem | $9 | $44 | 0.88u | $7.33 | after-open, value at FK open $13.50 |
| Flemington Sat 24 | R9 | Shockletz | $10 | $40 | 0.80u | $8.10 | after-open, value at FK open $12.67 |
| Cranbourne Fri 23 | R6 | Castellar (top-up) | $11 | $17 | 0.34u | $12.41 | founder's call, below our price; Castellar now $35 at $14.09 average |
| **Total** | | | | **$338** | **7.12u** | | |

Flemington after-open, not filled (TAB under the minimum): Ice Kool ($2.30 v $2.73), Surfin' Bird ($2.90 v $3.30), and the
higher steps of the three above. Flemington R7/R8: Aethelwulf and Cosmic Crusader only (founder's own bets).


## Tweeted Thu 22 Oct (locked)
Twitter units are the model stake halved (max 5u). Prices are what BetMatic would have taken at Form King's opening price
(founder: "what betmatic would of got"), not always what we got; our real bets are in "Taken, Wed 21 Oct" above.

Murshidi winner card (Geelong R5, 5u at $11, SP $3.70, +50u), with today's Mornington runners listed without prices:
R2 Party Benefits, R3 Grinding Away, R7 Cresta Crystal, R8 Russian Benefits (paper; not placed, TAB was empty when they fired).
Settle on Twitter at the model's open-price stakes halved: Party Benefits 0.36u at $8.75, Grinding Away 1.44u at $21,
Cresta Crystal 1.35u at $17, Russian Benefits 2.50u at $14.

Fri/Sat card ("Placed early. Win bets.", rated price shown under each):

| Day | Race | Horse | Price | Rated | Twitter units |
|---|---|---|---|---|---|
| Fri | Cranbourne R2 | Eye For An Eye | $22 | $13.22 | 0.95u |
| Fri | Cranbourne R2 | Superstock | $17.50 | $10.39 | 1.24u |
| Fri | Cranbourne R6 | Castellar | $16.50 | $12.41 | 0.35u |
| Sat | Flemington R1 | Ice Kool | $2.80 | $2.27 | 2u |
| Sat | Flemington R2 | Turbo Saint | $18 | $12.30 | 0.26u |
| Sat | Flemington R6 | Surfin' Bird | $4.40 | $2.75 | 3.6u |
| Sat | Flemington R7 | Aethelwulf | $8.50 | $3.24 | 3.85u |
| Sat | Flemington R8 | Cosmic Crusader | $11 | $5.58 | 2u |
| Sat | Flemington R9 | Classic Gem | $13.50 | $7.33 | 1.3u |
| Sat | Flemington R9 | Shockletz | $10 | $8.10 | 0.4u |

## Copied tips (founder's call, separate from the model's results)

| Date | Race | Horse | Tipster (price, units) | Order | Placed | Result |
|---|---|---|---|---|---|---|
| 2026-10-21 | Eagle Farm R4 (4:18pm) | No. 5 Wootten Hyde (tweeted as "Wooden Hyde") | Anthony Don ($2.50, 6u) | $300 win, min $2.30, High Odds First across every running session | Triggered 10:21am, $0 accepted: TAB balance $0.29 | |

The order path works: BetMatic took a High Odds First bet with the bookmaker list left open (every bookmaker where we have a running session) and fired it at once. Nothing was matched because the only running session (TAB) had no money in it.


## Ballarat Fri 23 Oct: paper (orders fired, TAB empty)
BetMatic triggered all 48 $50 Market Open orders at 9:25:15am Thu 22 Oct when TAB opened the meeting. No bet records
on any of them, the signature of an empty account: the TAB balance read $0.44 at 10:03am. Founder: "I didn't place any
actual bets, so paper only". The cancel run was refused for every order ("already triggered"), so nothing is live.
Paper at Form King's opening price (every step whose band holds the open), 5 bets, 16.59u:

| Race | Horse | FK open | Ours | Stake (u) | Twitter (u, halved) | TAB 9:55am |
|---|---|---|---|---|---|---|
| R3 | Star Je Taime | $7.50 | $4.15 | 6.22 | 3.11 | $5.00 |
| R3 | Wavelets | $14 | $8.60 | 0.83 | 0.42 | $12.00 |
| R7 | Bel Lupa | $19 | $13.11 | 1.50 | 0.75 | $9.00 |
| R8 | Jenni You Think | $8.75 | $4.37 | 5.92 | 2.96 | $4.60 |
| R9 | Russian Duchess | $11 | $8.51 | 2.12 | 1.06 | $11.00 |

Not value at the open: the other 18 runners opened under their minimum (Anglais $4.00 sat in the gap between its
$3.97-$3.99 and $4.48 steps).

## Sent Thu 22 Oct for Sat 24: Yarra Valley and St Arnaud ($50 unit, Market Open, TAB)
Priced on the final fields (pulled 11:29am / 11:30am Thu). Founder: R1 and R2 left out at both meetings; St Arnaud R3
kept despite first starter Harder Than All ("bet that race"). Yarra Valley 45 orders on 23 runners (up to 83.21u),
St Arnaud 47 orders on 23 runners (up to 99.82u); all 92 registered "Notification has been scheduled". TAB balance was
$0.44 at 10:03am Thu: the orders fire only if the account is funded before the markets open.

## Mornington Thu 22 Oct settled (paper; TAB was empty when the orders fired)
Results pulled 7:23pm Thu. Paper at Form King's open, the model stakes:
| Race | Horse | Open | Stake | Result | SP / BSP | P/L (u) |
|---|---|---|---|---|---|---|
| R3 | Grinding Away | $21 | 2.88u | 4th | $4.60 / $5.70 | -2.88 |
| R7 | Cresta Crystal | $17 | 2.70u | WON | $4 / $5.10 | +34.13 |
| R8 | Russian Benefits | $14 | 5.00u | 5th | $3.90 / $4.60 | -5.00 |
R2 Party Benefits scratched: void. Cresta Crystal carries an estimated 21c deduction for Mykindakandy (scratched after the
open at about $4.60; Home Tomurra, Lagunanini and Crank were scratched before the market opened), so $17 pays $13.64:
2.70u x 12.64 = +34.13u. Meeting: 3 bets, 10.58u, +26.25u, ROI +248%. All three opens beat BSP (21 v 5.70, 17 v 5.10, 14 v 4.60).
Twitter (tweeted, half stakes): Cresta Crystal 1.35u +17.06u, Grinding Away -1.44u, Russian Benefits -2.50u, Party
Benefits void: +13.12u on 5.29u.

## Friday 23 Oct deductions (TAB, founder)
Cranbourne: R2 4c (Eye For An Eye taken $23 -> $22.12; Superstock taken $15 -> $14.44). R6 Castellar SCRATCHED: both real
bets refunded ($18 at $17 and $17 at $11, $35). Ballarat (paper): R3 4c (Star Je Taime $7.50 -> $7.24, Wavelets $14 ->
$13.48), R7 7c (Bel Lupa $19 -> $17.74), R8 5c (Jenni You Think $8.75 -> $8.36). R9 Russian Duchess SCRATCHED: void.
Twitter card (Fri) re-issued at the after-deduction prices with the two scratchings shown as SCR / REFUND.

## Paper lay book, from Wed 28 Oct 2026 (founder, 23 Oct: "Let do it starting next Wednesday")
The rule is fixed before the first race (research/form_gbm/README.md, 23 Oct; t_lay_halves.py). Paper only, four weeks, then judged.
- Each race morning, after scratchings, every runner on the final field with our price (the live shaded model) gets a trigger:
  lay it if Betfair SP is between $15 and $40 AND at least 1.6 x our price. The morning list names each horse with its trigger.
  BAND WIDENED $30 -> $40 on day one, before any race (founder, 28 Oct: "lets get more profit, $15 to $40"). Backtest 3 Jun-13 Oct,
  1u lays: $15-$30 562 lays +295u (+52%, 2.5% of liability, biggest loss 27u); $15-$40 841 lays +425u (+50%, 2.0% of liability,
  biggest loss 32u), no losing month either way; the $30-$40 slice alone is 4 winners, A/E 0.75 / 0.24 by half.
- Paper stake 1u lay at Betfair SP: a loser pays +0.92u (8% commission; NSW/ACT tracks 10%, +0.90u), a winner costs (BSP - 1)u.
- Settled from Form King's results (betfairStartingPrice). A horse whose BSP misses the band or the trigger is no bet.
- Backtest to beat: holdout $15-$30 band, 562 lays, 10 winners against 27 expected; +45% / +60% on the lay stake by half.
  First-starters, internationals and scratchings are excluded, as on the back side.

| Date | Meeting | Race | Horse | Ours | Trigger (BSP at least) | BSP | Result | P/L (u) |
|---|---|---|---|---|---|---|---|---|
| 2026-10-28 | Bendigo | R1 | Magnusaurus Rex | $10.63 | $17.00 | $12.08 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R1 | Resonant | $2.53 | $15.00 | $3.3 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R1 | Running Rich | $5.15 | $15.00 | $5.47 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R1 | Scoville | $4.00 | $15.00 | $2.9 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R1 | Vixen Vibes | $22.11 | $35.37 | $35.96 | lost (finished 4), lay won | +0.92 |
| 2026-10-28 | Bendigo | R2 | Centenary Florin | $2.85 | $15.00 | $5.12 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R2 | Hydro Rush | $6.98 | $15.00 | $5.58 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R2 | Nickibi | $9.50 | $15.20 | $16.5 | lost (finished 5), lay won | +0.92 |
| 2026-10-28 | Bendigo | R2 | Purgatorio | $4.09 | $15.00 | $3.7 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R2 | Sound Byte | $6.43 | $15.00 | $3.2 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R3 | Prestige Lucky | $6.28 | $15.00 | $6.2 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R3 | Purple Streak | $4.10 | $15.00 | $4.13 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R3 | Romantic Miss | $10.19 | $16.31 | $10.5 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R3 | Savoyard | $11.75 | $18.80 | $10 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R3 | Sea Poem | $11.01 | $17.62 | $18 | lost (finished 2), lay won | +0.92 |
| 2026-10-28 | Bendigo | R3 | Star Of Omaha | $23.56 | $37.69 | $6 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R3 | Yukaina | $5.44 | $15.00 | $9.35 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R4 | Amawasha | $20.35 | $32.56 | $28.14 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R4 | Celtic Park | $10.70 | $17.13 | $10.8 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R4 | Hollandia | $20.47 | $32.75 | $25.72 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R4 | Melek | $3.24 | $15.00 | $2.09 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R4 | No Rumours | $19.28 | $30.84 | $20 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R4 | Pee Bee Noir | $17.17 | $27.48 | $55 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R4 | Salsita | $18.02 | $28.83 | $23.62 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R4 | Yahoo Bar | $4.09 | $15.00 | $6.2 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R5 | Cushioned | $5.59 | $15.00 | $5.8 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R5 | Itsukushima | $23.26 | $37.22 | $9.2 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R5 | Jenni You Think | $4.30 | $15.00 | $4.3 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R5 | Kiwi Jenni | $16.56 | $26.49 | $9.02 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R5 | Mr Independent | $20.51 | $32.81 | $14.92 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R5 | Savannah Chill | $15.30 | $24.47 | | no result | 0 |
| 2026-10-28 | Bendigo | R5 | The Muffin Man | $4.75 | $15.00 | $7.8 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R6 | Fission | $24.28 | $38.84 | $70 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R6 | Ka Ying Cheer | $22.17 | $35.48 | | no result | 0 |
| 2026-10-28 | Bendigo | R6 | Lawborough | $3.20 | $15.00 | $3.16 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R6 | Weapon Clear | $16.86 | $26.98 | | no result | 0 |
| 2026-10-28 | Bendigo | R6 | Wingsandpropellers | $18.16 | $29.06 | $7.72 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R6 | Yes Yoshi | $3.15 | $15.00 | $2.73 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R6 | Yolo | $15.35 | $24.57 | $12 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R7 | Alero | $6.90 | $15.00 | $5 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R7 | Dirty Look | $2.40 | $15.00 | $1.9 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R7 | Flying Embers | $8.05 | $15.00 | $21.48 | lost (finished 8), lay won | +0.92 |
| 2026-10-28 | Bendigo | R7 | Jamesjohno | $22.90 | $36.63 | $16 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R7 | Legacy Bay | $9.75 | $15.60 | $17.5 | lost (finished 5), lay won | +0.92 |
| 2026-10-28 | Bendigo | R7 | Wolf Twenty One | $22.76 | $36.42 | $33.05 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R7 | Zourain | $22.73 | $36.37 | | no result | 0 |
| 2026-10-28 | Bendigo | R8 | Berkeley Square | $19.87 | $31.79 | $39.7 | lost (finished 2), lay won | +0.92 |
| 2026-10-28 | Bendigo | R8 | Grand Pierro | $16.76 | $26.81 | $58.29 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R8 | Kings Valley | $5.65 | $15.00 | $4.6 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R8 | Litzdeel | $5.70 | $15.00 | $10 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R8 | Machine Gun Gracie | $16.41 | $26.26 | $16.43 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R8 | See That Storm | $8.66 | $15.00 | $17 | lost (finished 11), lay won | +0.92 |
| 2026-10-28 | Bendigo | R8 | So You Are | $8.61 | $15.00 | $4.58 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R8 | Starford | $22.80 | $36.48 | $17.5 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R8 | Suntora | $15.14 | $24.22 | $14.37 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R8 | The Euphrates | $12.99 | $20.79 | $13 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R9 | Bel Mezyaan | $4.42 | $15.00 | $3.64 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R9 | Col Klink | $3.09 | $15.00 | $4.58 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R9 | Hiyaam Proud | $16.12 | $25.80 | $17 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R9 | Rosa Aotearoa | $10.10 | $16.17 | $4.33 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-28 | Bendigo | R9 | Silver Bullet | $12.46 | $19.93 | $30 | lost (finished 9), lay won | +0.92 |
| 2026-10-28 | Bendigo | R9 | Spirited Defence | $22.18 | $35.49 | $25 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R1 | Alltogethernow | $18.40 | $29.43 | $16.32 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R1 | Lord Timo | $16.13 | $25.80 | $19.5 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R1 | Ned Kelly | $2.67 | $15.00 | $2.32 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R1 | Paramount War | $3.19 | $15.00 | $3.27 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R1 | Rang A Round Up | $9.30 | $15.00 | $16.02 | lost (finished 5), lay won | +0.92 |
| 2026-10-29 | Warrnambool | R1 | Rollin'ontheriver | $22.67 | $36.27 | $22 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R2 | Both Sides Now | $4.63 | $15.00 | $5.46 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R2 | Crossoverkid | $6.33 | $15.00 | $5.96 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R2 | Heed The Omens | $10.71 | $17.13 | $9.6 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R2 | Hoodys Horse | $12.40 | $19.83 | $15 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R2 | Newcombe | $12.55 | $20.09 | $23 | lost (finished 4), lay won | +0.92 |
| 2026-10-29 | Warrnambool | R2 | Parkrun | $24.17 | $38.67 | $26 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R2 | Share The Stars | $7.53 | $15.00 | $4.23 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R2 | The Daily Planet | $9.35 | $15.00 | $9.78 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R3 | Grandpa Neil | $10.03 | $16.04 | $9.55 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R3 | Nick Knockdown | $9.38 | $15.01 | $13.17 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R3 | Tuscan Rose | $3.47 | $15.00 | $2.7 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R4 | Hughie's Spirit | $19.59 | $31.35 | $15.5 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R4 | Mamzelle Raine | $23.51 | $37.61 | $48.49 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R5 | Big Vee | $7.60 | $15.00 | $6.8 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R5 | Celestaria | $10.13 | $16.21 | $6.92 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R5 | Circus Circus | $12.45 | $19.91 | $24 | lost (finished 11), lay won | +0.92 |
| 2026-10-29 | Warrnambool | R5 | Leona | $2.93 | $15.00 | $2.9 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R5 | Piklemegranmother | $23.41 | $37.46 | $38 | lost (finished 4), lay won | +0.92 |
| 2026-10-29 | Warrnambool | R5 | Semper Augustus | $20.72 | $33.15 | $21 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R5 | Zercardy | $5.98 | $15.00 | $7.75 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R6 | Ballynacally | $4.33 | $15.00 | $7.8 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R6 | Bancoora | $15.23 | $24.37 | $12.8 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R6 | Icy Pole | $7.89 | $15.00 | $8.21 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R6 | King West | $4.43 | $15.00 | $3.66 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R6 | Pastoral King | $5.05 | $15.00 | $5.24 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R6 | Secret Crossing | $12.11 | $19.37 | $10.26 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R7 | Crickwood | $3.36 | $15.00 | $2.39 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R7 | Du Clisson | $3.21 | $15.00 | $2.82 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R7 | Francine | $10.43 | $16.68 | $28.63 | lost (finished 6), lay won | +0.92 |
| 2026-10-29 | Warrnambool | R7 | Leantothemoon | $15.06 | $24.10 | $14.25 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R7 | Meisho | $20.98 | $33.57 | $18.05 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R7 | Torlaah | $19.49 | $31.18 | | no result | 0 |
| 2026-10-29 | Warrnambool | R7 | Twister | $8.87 | $15.00 | $17.57 | lost (finished 5), lay won | +0.92 |
| 2026-10-29 | Warrnambool | R8 | Asal | $9.67 | $15.47 | $8.8 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R8 | Boggy Creek Boys | $20.39 | $32.63 | $49.75 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R8 | Cachink | $11.24 | $17.99 | $7.92 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R8 | Charming Deel | $4.18 | $15.00 | $3.71 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R8 | Dealer Sing | $19.17 | $30.68 | $15.5 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R8 | Designs Of Eight | $24.01 | $38.42 | $18.66 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R8 | Gunado | $14.14 | $22.63 | $12.9 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R8 | Invisible Magic | $5.96 | $15.00 | $10.12 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R8 | Sotomayor | $13.48 | $21.57 | $10.5 | no bet (BSP outside band/trigger) | 0 |
| 2026-10-29 | Warrnambool | R8 | Super Snitch | $18.16 | $29.05 | $29 | no bet (BSP outside band/trigger) | 0 |

Warrnambool Thu 29 Oct (9:30am final field): 49 runners can trigger. Bendigo Wed 28 Oct (9:30am final field, our price = live shaded model before the open blend): 62 runners can trigger; a lay only if BSP lands $15-$40 and at least the trigger.

## Sat 24 Oct: Yarra Valley and St Arnaud at the open (paper; no bets struck)
Yarra Valley's orders triggered Fri 10:24am with TAB at $0.19 (no records). St Arnaud's fired Sat 8:07-8:09am and BetMatic
ignored every one: "No active session" on TAB, TAB took $0 of $5,202 asked. Paper at Form King's opening price (fk_open),
every step whose band holds it:

| Meeting | Race | Horse | FK open | Ours | Stake | Twitter (halved) | Price at 8:30am Sat |
|---|---|---|---|---|---|---|---|
| Yarra Valley | R3 | Nightowl | $6.50 | $4.45 | 2.50u | 1.25u | $3.80 |
| Yarra Valley | R7 | Prestige Ole | $9.50 | $6.32 | 1.37u | 0.69u | $4.20 |
| St Arnaud | R5 | Steely Hustler | $9.50 | $6.86 | 1.36u | 0.68u | $8.50 |
| St Arnaud | R7 | Coastal Whispers | $21.17 | $7.88 | 3.24u | 1.62u | $11 |

Not filled: Spinhof (St Arnaud R5) opened $23, past its $17.81 ceiling; Smashing Ruby (Yarra Valley R6) $10 past its $8
ceiling. Tweeted Sat 24 Oct with Flemington as posted Thursday (locked): card_sat24.json.

Saturday 24 Oct (re-pulled 8:50am Sat, jockeys and gear in; re-priced on the final fields ~9am, v10). Flemington: Always
Enuff (R1), Lady Catalina (R4) and Moonlight Circus (R9) carry no price at all this morning after being priced Wednesday,
so they are treated as late scratchings (estimated deductions: R9 about 6c on Classic Gem and Shockletz). 13 value-at-open
runners, 5 top-ups logged (paper): Turbo Saint R2 1.23u at $13, Written Empire R3 1.30u at $8 (EDGE), Feroce R6 1.62u at
$15, Aethelwulf R7 3.78u at $5 and Cosmic Crusader R8 1.40u at $8 (R7/R8 are the founder's own bets, flagged, not
added). The Speed Machine R2 also qualified and is NOT logged: first-up block. St Arnaud 5 value-at-open, Yarra Valley 2:
all under take-at now, no top-ups.

Flemington Sat 24 Oct deductions (TAB, founder): R1 0c, R2 39c, R6 15c, R7 10c, R8 0c, R9 8c. Real bets after deductions:
Turbo Saint $18 -> $11.37, Classic Gem $9 -> $8.36, Shockletz $10 -> $9.28. The Twitter card re-issued at the
after-deduction prices; Yarra Valley and St Arnaud were never posted Friday (founder busy), so they are recorded at SP.

## Sale Sun 25 Oct: market already open when priced (paper)
Priced Sat 24 Oct 10:40am on the final field; TAB had opened the meeting before any orders were built. Had the pre-open
orders been in, these two fill at Form King's opening price (first starters in R1-R3 all opened $12 or longer, so no race
is voided):

| Race | Horse | FK open | Ours | Stake | Twitter (halved) | Price Sat 10:39am |
|---|---|---|---|---|---|---|
| R2 | Rough Enuff | $7 | $4.88 | 2.24u | 1.12u | $3.80 |
| R5 | Superstock | $9 | $6.64 | 1.46u | 0.73u | $12 |

Superstock ran at Cranbourne on Fri 23 (R2, our bet) and is backing up two days later.

## Wangaratta Mon 26 Oct: market opened Sat late morning (paper)
The 78 pre-open orders were sent live Sat 11:58am (founder: "send for now"), but TAB had already opened the meeting, so every
order triggered at once; none left a placement record (nothing taken). The founder had meant a dry run ("prices are already
out, so another dry run"): Wangaratta is paper. At Form King's opening price these fill (R3's Move It, a first starter,
opened $4.90, so R3 is void under the race rule; no R3 order filled anyway):

| Race | Horse | FK open | Ours | Stake | Twitter (halved) | Price Sat 12:10pm |
|---|---|---|---|---|---|---|
| R6 | Phantom's Chase | $18.50 | $10.36 | 2.26u | 1.13u | $16 |
| R7 | Positivo | $8.50 | $4.00 | 6.42u | 3.21u | $3.70 |
| R7 | Strummer | $19 | $12.15 | 2.46u | 1.23u | $23 |
| R8 | Vaderlee | $11 | $6.32 | 3.62u | 1.81u | $5.50 |
| R9 | Blue Moon Summit | $21 | $10.89 | 2.90u | 1.45u | $23 |
| R9 | Three Musketeers | $41 | $14.78 | 1.58u | 0.79u | $11 |

Tweeted Sat 24 Oct with Sale (card_sun25_mon26.json).
Sale Sun 25 deductions (TAB, founder): R2 11c (Rough Enuff $7 -> $6.34). R5 Superstock SCRATCHED: void. Card re-issued after deductions.

## Saturday 24 Oct settled (results pulled Sun 25 Oct)
Tweeted card (Twitter units, after deductions; Yarra Valley and St Arnaud at SP): 11 bets, 17.65u staked, 3 winners
(Surfin' Bird $3.89, Cosmic Crusader $11, Nightowl SP $2.20), +21.10u, ROI +120%.
Ice Kool 3rd -2.00 · Turbo Saint 6th -0.26 · Surfin' Bird WON +10.40 · Aethelwulf 6th -3.85 · Cosmic Crusader WON +20.00 ·
Classic Gem 14th -1.30 · Shockletz 2nd -0.40 · Nightowl WON (SP $2.20) +1.50 · Prestige Ole 5th -0.69 · Steely Hustler 6th -0.68 ·
Coastal Whispers 9th -1.62.
Real money (TAB, $50 unit): Turbo Saint $26 at $11.37 lost, Classic Gem $44 at $8.36 lost, Shockletz $40 at $9.28 2nd lost: -$110.
Aethelwulf ($8.50) and Cosmic Crusader ($11, Ladbrokes) were the founder's own bets: Cosmic Crusader WON the Cox Plate.
Paper at the open (model stakes): Flemington Ice Kool -4.07, Surfin' Bird 10.56u at $3.89 +30.52, Classic Gem -2.58;
Yarra Valley Nightowl 2.50u at $6.50 +13.75 (no deduction recorded), Prestige Ole -1.37; St Arnaud Steely Hustler -1.36,
Coastal Whispers -3.24: 7 bets, 25.68u, +31.65u, ROI +123%.
9am top-ups (paper): Turbo Saint -1.23, Written Empire -1.30, Feroce -1.62: -4.15u.
Paper lay sheet (preview, 1u lay at BSP): 5 lays, Turbo Saint +0.92, Caddington (BSP $15.76, WON) -14.76, Simply Excels +0.92,
Whiskey And Beer +0.92, Molesworth +0.92: -11.08u.
Friday 23 Cranbourne R2: Eye For An Eye 10th, Superstock 3rd (real bets $95 + $98, lost); Pariah Pearl 2nd (paper top-up -1.41u).
Ballarat Fri 23 races 3-9 still unresulted in Form King.
Ballarat Fri 23 Oct ABANDONED after R2 (founder, 25 Oct): every Ballarat bet from R3 on is void, paper and top-ups alike
(Star Je Taime, Wavelets, Bel Lupa, Jenni You Think; top-ups Wavelets, Circus Circus, Skjaldmo). Twitter Ballarat rows void.

## Swan Hill Tue 27 Oct (paper: the market opened Sunday afternoon before the orders were sent)
Priced Sun 25 Oct on the fields; founder took races 1, 3 and 4 off the sheet (42 orders on 19 runners, races 2, 5-8).
The first-starter rule would have voided those three races anyway at the open (Winna's Sister $4.80, Tremont $6.00,
Town Planner $4.60). Two fills at Form King's open:

| Race | Horse | FK open | Ours | Stake | Twitter (halved) | Deduction (est.) | Price after |
|---|---|---|---|---|---|---|---|
| R7 | Habitual | $6 | $3.25 | 11.78u | 5u (cap) | 16c (TAB actual) | $5.20 |
| R8 | Mr Butt's Boats | $21 | $8.23 | 3.60u | 1.80u | 12c (TAB actual) | $18.60 |

Nineteen others opened under their minimums; the market opened short on most of our book (Killiana $2.30 v ours
$2.67, Neziha $2.80 v $4.92, Switch Hit $3.80 v $6.76). Flash Inquiry (R1, $18 open, 3.08u) would have filled on
the full sheet but R1 was off.

Wangaratta Mon 26 deductions (TAB, founder, Sun 25 Oct): R6 15c (Phantom's Chase $18.50 -> $15.88), R7 none (Positivo
$8.50, Strummer $19), R8 none (Vaderlee $11), R9 6c (Blue Moon Summit $21 -> $19.80, Three Musketeers $41 -> $38.60).
Cards re-issued after deductions.

Wangaratta Mon 26 Oct (re-priced 9:35am Mon on the final field, 36 out): 15 value-at-open runners, 4 top-ups (7.13u: Kinky
Mistress 4.22u at $3.60, Princess Geisha 0.73u at $14, Somethingintheair 0.91u at $15, Brilliant Bull Ant 1.27u at $16), the
rest under take-at now. Of the six paper opens, Strummer is the only one still over our price ($23 v ours $13.44, already at
full stake); the market has come for the other five (Positivo $8.50 to $4.40, Vaderlee $11 to $4.20, Blue Moon Summit $21 to
$7.50, Three Musketeers $41 to $13, Phantom's Chase $18.50 to $12).

## Sunday 25 Oct Sale settled (results pulled Mon 26 Oct)
Rough Enuff (R2) WON: SP $3.50, BSP $4.42, against $6.34 after the 11c deduction ($7 open). Superstock (R5) scratched: void.
Tweeted card (Twitter units, after deductions): 1 bet, 1.12u at $6.34, +5.98u, ROI +534%.
Paper at the open (model stakes, 11c deduction): Rough Enuff 2.24u at $6.34, +11.96u; Superstock void. No real money (the
market was open before any orders were built). Open book (GD stake 1.82u): +9.72u.

## Bendigo Wed 28 Oct (orders sent Mon 26 Oct 12:04pm; nothing placed by 3:38pm, BetMatic bot not answering)
61 orders on 30 runners (R1 off, founder), 109u, sent live to fire at the TAB open. Form King had race 8 priced by 3:05pm
Mon and every race by 5:29pm; BetMatic status showed 0 placed and its odds feed returned nothing ("the bot must be running
with its sessions online"). Mickio (R4) and Turned Down (R7) scratched; Only Opera and Princess Toro in.
Value at the open (paper_open, Form King open), the Twitter card (card_wed28.json, model stake halved):

| Race | Horse | FK open | Ours | Stake | Twitter (halved) |
|---|---|---|---|---|---|
| R3 | Purple Streak | $8 | $4.36 | 3.14u | 1.57u |
| R4 | Yahoo Bar | $7 | $4.30 | 2.83u | 1.42u |
| R7 | Imperial Award | $11 | $8.45 | 2.25u | 1.13u |
| R8 | Litzdeel | $8.50 | $5.73 | 1.73u | 0.87u |
| R8 | See That Storm | $16 | $8.40 | 1.39u | 0.70u |

The pre-open order sheet at the same opens fills 21.08u: Purple Streak 5.32u, Yahoo Bar 3.90u, Jenni You Think 4.80u,
Lawborough 3.36u, Litzdeel 1.48u, See That Storm 2.22u (Imperial Award's orders start at $12.58, so none fill at $11).
Tweeted Twitter card (founder, 27 Oct, the open fills halved): R3 Purple Streak $8 2.66u (rated $4.36), R4 Yahoo Bar $7 1.95u
($4.87), R5 Jenni You Think $7 2.40u ($4.61), R6 Lawborough $4.40 1.68u ($3.22), R8 Litzdeel $8.50 0.74u ($5.73), R8 See That
Storm $16 1.11u ($8.40): 10.54u. This card, not card_wed28.json, is the Twitter record for Bendigo.
TAB deductions (founder, Wed 28 Oct): R3 3c, R4 6c, R5 10c, R6 5c, R8 none. Card prices after deductions: Purple Streak
$7.79, Yahoo Bar $6.64, Jenni You Think $6.40, Lawborough $4.23, Litzdeel $8.50, See That Storm $16.

## Monday 26 Oct Wangaratta settled (results pulled Mon 26 Oct 6:20pm)
Positivo (R7) WON: SP $3.70, BSP $3.77, tipped $8.50. Vaderlee 2nd, Strummer 3rd, Blue Moon Summit 3rd, Phantom's Chase 4th,
Three Musketeers 6th.
Tweeted card (Twitter units, after deductions): 6 bets, 9.62u, +17.67u (Positivo 3.21u x 7.50 = +24.08), ROI +184%. At BSP
the same stakes: +2.48u.

## October tips settled at Betfair SP (founder, 26 Oct: "show how we are profitable at BSP even without prices tipped early")
Every tip from 5 to 26 Oct with a Betfair SP (clv_oct_to24.json, plus Sale and Wangaratta), 1u each: 88 bets, 23 winners.
At the tipped price +118.19u (+134%); at BSP +49.91u (+57%), +40.72u (+46%) after 8% commission on winnings. Kingswood ($25
tipped, BSP $28.12) is +27.12u of the BSP figure; without him +22.79u (+26%). Yarra Valley Sat 24 (Nightowl) has no BSP in
Form King and is not counted.
Swan Hill Tue 27 Oct (re-priced 9:50am Tue on the final field: 30 out): 11 value-at-open runners, 3 paper top-ups (6.25u: Magna Sententia 3.09u at $3.50, His Finest Hour 2.08u at $7, Baganov 1.08u at $10), the rest under take-at now. Habitual (our open bet at $6) is $1.85; Mr Butt's Boats $9 (opened $21).
Swan Hill Tue 27 Twitter (founder, Mon 26 Oct evening: "This is just for Twitter"): tweeted at BSP with our rated prices,
Habitual 5u (rated $3.25) and Mr Butt's Boats 1.80u (rated $8.23); settled on Twitter at Betfair SP. The book's paper fills
stay at the open ($6 and $21, R8 deduction est. 17c on the Mon 9:05pm scratchings).

Wangaratta Mon 26 Oct top-ups settled (paper, results pulled Wed 28 Oct 7:13am): 4 bets, 7.13u, +3.09u. Princess Geisha WON
at $14 (0.73u, +9.49u; SP $9.50, BSP $11.72); Kinky Mistress 2nd, Somethingintheair 3rd, Brilliant Bull Ant 6th.

Warrnambool Thu 29 Oct orders: none placed (R5/R6 skipped for balance at 3:49pm Tue; R1/R2/R7/R8 fired at the open but the bot
had lost its connection, per BetMatic support). Cancel run Wed 28 Oct 7:13am: all 49 notifications already triggered, nothing
left live. At Form King's open the orders would have filled 24.16u (Ned Kelly, Both Sides Now, Hoodys Horse, Ballynacally,
Icy Pole, Francine, Gunado, Super Snitch); cards sent to the founder Tue evening at current prices and at the open (Twitter units).

## Tuesday 27 Oct Swan Hill settled (results pulled Wed 28 Oct 8:07am)
Habitual (R7) WON: SP $2.60, BSP $2.96, taken $5.20 after the 16c deduction ($6 open). Mr Butt's Boats (R8) 8th (SP $6.50, BSP $8.68).
Paper at the open (model stakes, after deductions): 2 bets, 15.38u, +45.88u (Habitual 11.78u x 4.20 = +49.48u).
Twitter card at BSP: 2 bets, 6.80u, +8.00u (Habitual 5u x 1.96 = +9.80u), before Betfair commission.
Paper top-ups (9:50am reprice): 3 bets, 6.25u, -6.25u (Magna Sententia 3rd, His Finest Hour 7th, Baganov 10th).

Bendigo Wed 28 Oct (re-priced 9:30am Wed on the final field, 25 out): 11 value-at-open runners, 2 paper top-ups (5.37u: Centenary Florin 5.11u at $4.40, Litzdeel 0.26u at $8.50), the rest under take-at or already at full stake. R1 Resonant ours $2.53 after Hot Samba, $2.90 best at 9:20am, take-at $2.94: no bet.

## Flemington Sat 31 Oct, Derby Day (paper: the BetMatic bot was off when the market opened)
Priced Wed 28 Oct on the final field at Good 4 (founder: lean drier for the carnival). TAB opened the market from about
12:15pm Wed; R6 and R7 were open before the send and came off the sheet. The live send (50 orders, 24 runners, R1-R5, R8,
R9, 52.27u, $1,962 at $37.50) was refused: "session is not running (bot_running false)". Founder, 28 Oct: "Bots off fuck me.
Paper test." The sheet is settled on paper at Form King's opening prices once Form King has them.
Founder's tip checks on TAB prices (after-open rule needs edge 1.3): R7 True Rebel $7 (ours $5.07; open rule from $6.61, after-open
rule $7.33), R8 Sass Appeal $12 (ours $6.47; clears both, 1.6u full, 0.80u Twitter). Recorded as Twitter tips only if posted.
Tweeted Twitter card, Flemington Sat 31 Oct (posted Wed 28 Oct by the founder, one tweet each): R5 War Machine $17 TABtouch
0.59u (rated $8.59), R6 Natural Fling $7 TABtouch 0.75u ($4.71), R7 True Rebel $7 TAB 0.64u ($5.07), R8 Sass Appeal $12 TAB
0.80u ($6.47), R9 Bridal Waltz $5 all books 1.46u ($3.29): 5 tips, 4.24u. This, not the order sheet, is the Twitter record.
Flemington paper at the open, every race open by 2:41pm Wed (R2 2:19pm, R4 2:41pm): 7 fills, 14.97u. Icelady $3.50 3.54u,
Hankee Alpha $6.50 2.22u (R4), Persian Spirit $9.50 1.27u, War Machine $16 1.24u, True Rebel $8 1.84u, Sass Appeal $11 1.70u,
Bridal Waltz $5 3.16u. Nothing in R1, R2 or R6. Plain card (no Mercer, Twitter units) sent to the founder.

## Pakenham Fri 30 Oct (paper: the BetMatic bot was off at the open)
Priced Wed 28 Oct on Good 4; R2-R4 off (first starters, founder). TAB opened Wed 3:20-4:09pm. At Form King's open the sheet
fills 6 bets, 11.47u: R1 Via Theresa $26 0.77u, R1 Viking Kid $4.60 4.68u, R5 In A Tizzy $4.40 3.22u, R7 Garnacho $11.50
1.05u, R7 Glenfinnan $18.50 0.73u, R8 Empressive Enuff $12 1.02u. By Thu 9:30am five of the six had firmed (Viking Kid $2.40,
Via Theresa $9, Glenfinnan $8, Garnacho $6.50, In A Tizzy $3.70); Empressive Enuff $10. Kilmore: no prices in Form King yet.

## Wednesday 28 Oct Bendigo and Thursday 29 Oct Warrnambool settled (results pulled Fri 30 Oct 8:55am)
Bendigo (paper, nothing placed): Lawborough (R6) WON, SP $3.20 / BSP $3.16, taken $4.23 after the 5c deduction. Purple Streak 3rd,
Yahoo Bar 2nd, Jenni You Think 2nd, Litzdeel 3rd, See That Storm 11th.
- Tweeted card (Twitter units, after deductions): 6 bets, 1 won, 10.54u, -3.43u, ROI -33%.
- Paper at the open (model stakes, after deductions): 6 bets, 1 won, 21.08u, -6.87u, ROI -33%.
- Top-ups (9:30am reprice): 2 bets, 5.37u, -5.37u (Centenary Florin 4th, Litzdeel 3rd).
Warrnambool (paper, nothing placed): Ned Kelly (R1) WON, SP/BSP $2.32, opened $3.50. Both Sides Now 12th, Hoodys Horse 6th,
Ballynacally 3rd, Icy Pole 8th, Francine 6th, Gunado 3rd, Super Snitch 10th. No TAB deductions recorded yet (settled at the open).
- Open card (Twitter units): 8 bets, 1 won, 12.08u, -8.86u, ROI -73%.
- Paper at the open (model stakes): 8 bets, 1 won, 24.16u, -17.72u, ROI -73%.
Lay book (1u at BSP, $15-$40 and the trigger): Bendigo 8 lays, 0 winners, +7.36u; Warrnambool 6 lays, 0 winners, +5.52u.
Lay book to date: 14 lays, 0 winners, +12.88u.
Week Mon 26 - Thu 29 Oct, paper at the open (model stakes; Wangaratta = the halved card doubled): 4 meetings, 22 bets,
4 won, 79.86u, +56.63u, ROI +71% (Wangaratta +35.34, Swan Hill +45.88, Bendigo -6.87, Warrnambool -17.72).
Twitter cards: 39.04u, +13.38u, ROI +34% (Swan Hill at BSP). Top-ups: 9 bets, 18.75u, -8.53u. Real money: none this week (bot).

Kilmore and Pakenham Fri 30 Oct, 9:30am (re-priced 8:35am Fri on the final field). Kilmore: 4 value-at-open runners, no top-ups
(Wavelets, Manchego, Adieu Grasse and Cable De Vega all under take-at now). Pakenham: R1 lost SIX runners overnight (Cowboykickedfive,
Marco Polo, Tempered Edge, Whitebait, Ambition In Bloom, Seven Sons), so Viking Kid and Via Theresa carry a big R1 deduction; one top-up,
Shidan (R8) 1.09u at $8 (opened $19, over the order's $15.84 max, so BetMatic took nothing). Voltrix (R4, $6 now, ours $3.88) is value
but R4 is off (first starters, founder) and is not topped up. topup.py fixed the same morning: it counted an order as filled
whenever the open cleared min_odds, ignoring max_odds (Shidan and Viking Kid's under-$4 tier were both mis-counted).

## Missed at the open, Fri 30 Oct (paper; founder: "Nah all paper")
The BetMatic bot reported bot_running false at 2:41pm, 3:08pm and 3:27pm Fri, so nothing was sent. Fills at Form King's
open on the sheets as priced (first-starter races off), prices at 3:20pm Fri. Twitter units are half.
Mornington Sun 1 Nov (Soft 7; every race open from 9:42am Fri): R5 Miss Cotoletta $5.50 2.81u (ours $3.60), R7 Eye For An Eye
$15 1.33u ($8.04), R7 Fam Gorman $15 1.46u ($7.43), R9 Kokako $5 2.65u ($3.77), R9 Master Of The Air $15 1.28u ($8.32): 9.53u.
Flemington Tue 3 Nov (Good 4; R2-R6 open 1:31-2:39pm Fri): R2 Yauson $4.80 4.55u (ours $2.86), R3 Star Of Macedon $6 2.43u
($4.04), R4 Gin Twist $17 0.80u ($10.52), R5 Grand Pierro $13 1.65u ($6.63), R5 Autumn Mystery $17 1.05u ($9.95), R5 Vegas Jack
$17 0.71u ($11.71): 11.19u. Nothing in R6.
Traralgon Sat 31 Oct (all races open 2:36-2:51pm Fri): R5 It's Gnarly $6 2.10u (ours $4.56), R5 Ze Bee Nine $7.75 1.81u ($5.15),
R6 Lulu Darling $10 1.31u ($6.79), R6 Trinity's D'oro $11 1.21u ($7.25): 6.43u.
Mortlake R6 (open 7:13am Fri): no fills. Total 15 bets, 27.15u (13.58u Twitter).
Still to send once the bot shows running: Healesville, Mortlake (R1, R4, R5, R7), Wycheproof (Sat); Ballarat (Mon);
Flemington R7-R10, Echuca, Mildura, Wangaratta (Tue). Mansfield (Tue) not priced (14% of runners without speed ratings).

## Sat 31 Oct morning: unit back to $50 for the next sends (founder, 31 Oct: "Make it $50 units as well please")
Ballarat (Mon 2 Nov) and Echuca, Mildura, Wangaratta (Tue 3 Nov) go at $50 a unit (unit=50 on the fk-betmatic send), once the bot
shows running ("TAB will be funded and bot on"). Dry run Sat 7:26am: "bot_running false". At 7:30am Sat these were still unopened:
Healesville, Mortlake (bar R6), Wycheproof (Sat), Ballarat (Mon), Echuca, Mildura, Wangaratta (Tue). Flemington Sat (all open from
Wed) and Traralgon (Fri 2:36pm) are paper: Flemington 7 fills 14.97u (Star Of Macedon scratched), Traralgon 4 fills 6.43u.
Saturday open card (no Mercer, Twitter units) sent to the founder 7:40am Sat.

## Sent live Sat 31 Oct 10:47am ($50 a unit, TAB, Market Open; founder: "re do it and let's go")
The bot dropped in and out: dry runs passed at 10:25am, live sends refused at 10:35 and 10:42 ("bot_running false"), the check at
10:46 showed the TAB session running ($1,500.17) and all four sends went through. BetMatic also flags the bot as outdated
(latest 1.2.70-beta04).
- Ballarat Mon 2 Nov (Soft 7): R6, R8 only, 17 orders, $727 if all fire. TAB had R6 and R8 up already (notifications "sent", not
  "scheduled"); status 10:51am: nothing placed (prices under the minimums). R4, R5, R7 opened 10:08am Sat, before the send.
- Echuca Tue 3 Nov (Soft 7): 38 orders, $1,888, scheduled.
- Mildura Tue 3 Nov (Good 4): 54 orders, $3,655, scheduled.
- Wangaratta Tue 3 Nov (Soft 6): 40 orders, $1,803, scheduled.
- Ballarat Mon 2 Nov R4 Best Terms: PLACED 11:17am Sat 31 Oct, $331 (6.62u at $50) at $2.60 TAB (after-open rule needed $2.50;
  ours $1.82 on Soft 7). Real money. The other open-time fills missed at Ballarat (paper): Wintery R6 $7 2.16u, Catwalk Icon R7
  $4.60 2.90u (passed after the open: Catwalk Icon $5 cleared the rule by 2c, Wintery in to $3.70).
- Status 11:15am: BetMatic showed 0 bot machines and 0 sessions running while the founder's app said on; at 11:16am both
  registered and the bet went. The connection drops in and out (bot flagged outdated, latest 1.2.70-beta04).

## Don copies, Sat 31 Oct (real money, $50 a unit; founder: "Mate just bet them at best odds all of them")
| Race (jump) | Horse | Bet | Stake | Price taken | Don's price |
|---|---|---|---|---|---|
| Doomben R5 (3:32pm) | Kick Up Rocky | Win 5u | $250 | $3.20 (BetMatic bookie 63, High Odds First) | $3.30 SB / Lads |
| Newcastle R5 (3:45pm) | Bundy Belle | Win 4u | $200 | $3.20 TAB | $3.80 TAB |
| Doomben R6 (4:12pm) | Vintage Vibes | Win 2u | $100 | $4.80 TAB | $6 Lads / Betr |
| Doomben R6 (4:12pm) | Vintage Vibes | Place 2u | $100 | $1.80 TAB | $2.10 |
First send at 20c under his price filled only Kick Up Rocky (Bundy Belle $3.20 and Vintage Vibes $4.80 were under the floors);
re-sent at best odds on the founder's word. Place bets now go through betmatic_send.py as PLACE rows (Fixed Place).
Settled (BetMatic status, 5:50pm Sat): Kick Up Rocky WON +$550, Bundy Belle lost -$200, Vintage Vibes WON win +$380 and place
+$80. Don copies Sat 31 Oct: $650 staked, +$810.

## Saturday 31 Oct: Traralgon ABANDONED (founder, 31 Oct). R5 and R6 tips (It's Gnarly, Ze Bee Nine, Lulu Darling, Trinity's D'oro)
are void, paper and Twitter alike. Flemington tips to R8: no winner (Icelady 3rd, Sass Appeal 4th, True Rebel 5th); War Machine
scratched (void); R9 Bridal Waltz to settle.

## Friday 30 Oct and Saturday 31 Oct settled (results pulled Sat 6:27pm), paper at the open
Kilmore (7.14u): Manchego 2nd, Adieu Grasse 6th: -7.14u. Pakenham (11.47u): Viking Kid 2nd, Via Theresa 5th, In A Tizzy 3rd,
Garnacho 2nd, Glenfinnan 7th, Empressive Enuff 6th: -11.47u. Pakenham top-up Shidan 8th: -1.09u.
Flemington (14.97u at the open): War Machine scratched (void, 1.24u back); Icelady 3rd, Hankee Alpha 10th, Persian Spirit 8th,
True Rebel 5th, Sass Appeal 4th: -10.57u; Bridal Waltz (3.16u) not resulted yet. Traralgon abandoned (void).
Week Mon 26 - Sat 31 Oct, paper at the open (model stakes), Bridal Waltz open: 33 bets settled, 4 won, 109.04u, +27.45u, ROI +25%
(Wangaratta +35.34, Swan Hill +45.88, Bendigo -6.87, Warrnambool -17.72, Kilmore -7.14, Pakenham -11.47, Flemington -10.57).
Real money this week: Don copies +$810 on $650; Ballarat Mon R4 Best Terms $331 at $2.60 open.
