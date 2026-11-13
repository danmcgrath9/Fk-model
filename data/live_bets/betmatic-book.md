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
| 2026-11-02 Ballarat | R4 | Best Terms (real bet 6.62u at $2.60 already on) | $2.50 | $2.90 | $1.92 | 6.62u (real, $2.60) | 2.74u | | |

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
  CORRECTION (3 Nov, t_lay_months.py on the refreshed holdout, 870 lays +427u): July IS a losing month, 8 winners from 226
  lays, -11u ($15-$30: 6 of 161, -5.5u); the other four months +50u to +148u. 'No losing month' was wrong.
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
Flemington R9 Bridal Waltz lost (founder, 31 Oct): -3.16u at the open (tweeted 1.46u: -1.46u). Week Mon 26 - Sat 31 Oct, paper at
the open: 34 bets, 4 won, 112.20u, +24.29u, ROI +22%. Flemington Derby Day: 0 from 6 (War Machine scratched), -13.73u.

Ballarat Mon 2 Nov (re-priced 9:40am Mon on a fresh export of the final field, Soft 7; 29 more out since Sunday incl. Star Je
Taime R1, Jack Will R4, Layla R7; emergencies Hola Amigos and Le Notre (R7), Cool Savanna and Lika Wreckin' Ball (R8) in): 9
value-at-open runners, 1 paper top-up, Best Terms R4 2.74u at $2.90 (full stake 9.36u at $2.90, less the real 6.62u at $2.60;
topup.py counts the sheet's 6.30u at the $2.50 open, so it says 3.06u). $2.90 also clears the after-open rule ($2.64): a real
top-up only on the founder's word. Everything else under take-at now: Marco Polo $26 -> $6, Wintery $7 -> $2.80, Catwalk Icon
$4.60 -> $2.30. TAB deductions (founder, Mon morning): R5 2c, R6 3c, R7 25c; R4 left for BetMatic to report at settlement.

Mornington Sun 1 Nov (re-priced 9:32am Sun on the final field, Soft 7, 29 out incl. Galway Gal, Bel Lupa, Superstock, Presscode): 10
value-at-open runners, 2 paper top-ups (1.09u: Fam Gorman R7 0.48u at $18, Warrior Within R9 0.61u at $19), the rest under take-at
now. Open fills (paper, market open before the send): Miss Cotoletta $5.50 now $3.30, Eye For An Eye $15 now $5.75, Fam Gorman $15
now $18, Kokako $5 now $2.70, Master Of The Air $15 now $5. Deduction in R5 (Bel Lupa, Pocket Size, Simply Steffi, Heidi Dancer out)
and R9 (Presscode, Sub Gauge, Rapid Cheval out) to settle at TAB's figures.

## Flemington Tue 3 Nov re-priced on Soft 6 (founder, 1 Nov: "Flemington will be a S5 - S6"), paper, not sent
Full re-pull Sun 11:34am (the odds-only pull had left the Cup with 68 entries and no benchmarks), metro fix and half stakes,
R1 off (8 first starters). Filled at Form King's open: R2 Yauson $4.80 1.35u (ours $3.12), R3 Katoto $13 0.83u ($5.26), R3 Star
Of Macedon $6 0.94u ($4.19), R4 Gin Twist $17 0.30u ($10.90), R5 Autumn Mystery $17 0.46u ($8.81), R5 Vegas Jack $17 0.30u
($10.92), R7 Enfjaar $21 0.29u ($11.55), R7 Juja Kibo $13 0.42u ($8.29), R8 Mr Natural $17 0.47u ($8.72), R8 Ranarsson $4 1.62u
($2.73): 10 bets, 6.98u ($349 at $50). Orders: 2026-11-03-flemington-s6-metrofix-orders-all.csv.

## Mornington Sun 1 Nov R1: Star Je Taime was off the sheet (founder, 1 Nov)
R1 came off on Fri 30 Oct under the first-starter rule because Galway Gal (first starter, opened $8.25) was in it. Galway Gal
was scratched Sun morning, but the 9:30am re-price only reads the order sheet, so R1 never came back. At Form King's open
($5.50, ours $2.80 then) the three orders would have filled 4.66u. Paper either way: the bot was off when the market opened.

## Sent live Sun 1 Nov 12:10pm: Tuesday's first-starter races ($50 a unit, TAB, Market Open; founder: "Yeah thats fine")
The race rule was scrapped the same morning, so the races it had held back went in: Echuca R3-R5 (19 orders, 10 horses),
Mildura R3 (4 orders, 2 horses), Wangaratta R1 and R3 (14 orders, 5 horses), every order scheduled (-fs-ledger.csv). TAB
balance $0.65 at the dry run: nothing places unless the account is funded before the markets open. Ballarat R1-R3: all
opened Sat before the send, none clears the after-open rule now; Star Je Taime opened $3 there (paper fill 7.05u).

## Flemington Tue 3 Nov under the $12 metro cap, full stakes (founder, 1 Nov), paper, not sent
Supersedes the half-stake list above. Filled at Form King's open: R2 Yauson $4.80 2.71u, R3 Star Of Macedon $6 1.87u, R8 Ranarsson
$4 3.25u: 3 bets, 7.83u ($392 at $50). The seven at $13+ are gone (Katoto $13, Gin Twist, Autumn Mystery, Vegas Jack, Mr Natural
$17, Juja Kibo $13, Enfjaar $21). Orders: 2026-11-03-flemington-s6-cap12-orders-all.csv. Deductions no longer shown on pages.

## Sat 31 Oct under the 1 Nov rules (founder: "what we would of had yesterday"), paper, at Form King's open, no deductions
Metro $12 cap and full stakes, first-starter races on. Flemington (Good 4 sheet): Icelady $3.50 3.30u 3rd, Hankee Alpha $6.50
1.96u 10th, Persian Spirit $9.50 1.25u 8th, True Rebel $8 1.54u 5th, Sass Appeal $11 1.11u 4th, Bridal Waltz $5 2.72u 16th:
-11.88u. Mortlake: Becauseyou're Mine $8 1.50u WON +10.50u, Semper Fortis $10 1.38u 3rd: +9.12u. Wycheproof: An Poitin Still
$6.70 1.91u 2nd: -1.91u. Healesville: no fills. Traralgon abandoned (4 void). Day: 16.67u, -4.67u.

## Week Mon 26 Oct - Sun 1 Nov re-run under the 1 Nov rules (founder: "re run this week with new rules"), paper
Each meeting's pre-market order sheet (the -all file: first-starter races on, first starters never bet), Flemington rebuilt with
the metro $12 cap at full stakes, every horse capped at 10u (Habitual 11.78u -> 8.66u), filled at Form King's open, no
deductions. Wangaratta +35.33, Swan Hill +36.62, Bendigo -6.30, Warrnambool -17.72, Kilmore -7.14, Pakenham -15.64, Flemington
-11.88, Mortlake +9.12, Wycheproof -1.91, Healesville no fills, Traralgon void, Mornington R1 Star Je Taime -4.66 (R3-R9 to run).
Settled: 43 bets, 5 won, 123.93u, +15.82u (+12.8%). research/form_gbm/settle_week_20261101.py.

## Tuesday 3 Nov replaced (founder, Sun 1 Nov: "Yep move it to $15, then send Tuesday")
Cancelled every earlier Tuesday order (preopen and -fs ledgers, Echuca, Mildura, Wangaratta: all 200 OK) and sent the v2
sheets, re-priced Sun afternoon on declared riders with every 1 Nov rule (rider fix, shade off, first-starter races on,
EARLY cap $15), $50 a unit, Market Open, TAB: Echuca 66 orders on 33 horses, Mildura 53 on 24, Wangaratta 58 on 28, all
scheduled (-v2-all-ledger.csv). Girl With A Pearl (Wangaratta R3, 8.37u) scratched; Airclash (Mildura R2) bounce-blocked.
TAB balance $0.65 at the 3:45pm check.

## Ballarat Mon 2 Nov cards (founder, Sun 1 Nov evening)
Mercer card at the 3:25pm Sunday prices, Marco Polo (R4, rated $10.69, opened $26, $6.50 Sunday) shown at BSP (founder: "Do
Marco Polo BSP for Mercer"): settle him on Twitter at Betfair SP. The rest at the prices on the card: Best Terms $2.50, Into
You $14, Wintery $3.10, Catwalk Icon $5. Plain card at the opens ($2.50, $26, $26, $7, $4.60). Twitter units 3.15 / 0.49 /
0.36 / 1.67 / 1.45. card_mon02.json, card_mon02_plain.json.

## Sunday 1 Nov Mornington settled (results pulled Sun 7pm), paper at the open, TAB's actual deductions (founder, Sun 8pm)
Big Kapow (R3) WON: $7.50 open, 23c deduction, paid $6.01 (SP $3.80, BSP $3.87), 2.05u +10.26u. Kokako (R9) WON: $5 open,
11c deduction, paid $4.56 (SP $2.25, BSP $2.32), 2.63u +9.36u. Star Je Taime 2nd (SP $1.65), Miss Cotoletta 2nd, Fam Gorman
2nd at $15, Eye For An Eye 6th, Master Of The Air 4th. 7 bets, 2 won, 15.64u, +8.66u (+55%). Big Kapow was in a
first-starter race the pre-1 Nov rule had off the sheet; both winners beat BSP by a street. Top-ups (paper): Fam Gorman
0.48u at $18 2nd, Warrior Within 0.61u at $19 7th: -1.09u. Sunday's cards (Twitter units, opens): Miss Cotoletta 1.41u, Eye
For An Eye 0.67u, Fam Gorman 0.73u, Kokako 1.33u (+4.73u at $4.56), Master Of The Air 0.64u: 4.78u, +1.28u if posted as sent.
Week Mon 26 Oct - Sun 1 Nov under the 1 Nov rules, paper at the open: 50 bets, 7 won, 139.57u, +24.48u (+18%).
RULE (clarified 1 Nov evening): no deductions are ESTIMATED any more; TAB's actual deduction, when the founder reports it, is
applied to the winnings (1 + (price - 1) x (1 - d)), as it always was for real bets.
Real money this week: Don copies +$810 on $650; Best Terms $331 at $2.60 runs Monday.

## Tuesday 3 Nov at the open (paper: TAB unfunded, BetMatic placed nothing; founder, Mon 2 Nov midday)
Flemington (opened Fri, metro $12 cap, full stakes): R2 Yauson $4.80 2.71u, R3 Star Of Macedon $6 1.87u, R8 Ranarsson $4 3.25u.
Echuca (R1-R6 opened Mon 11:44-11:50am): R1 Frozen Tide $4.40 3.39u, R3 Frewdamoss $16 0.77u, R5 Celestial Option $13
0.96u, R6 Flying Jude $13 0.96u. Mildura, Wangaratta and Echuca R7 not open at 12:05pm Mon. Mercer card at the opens
(Twitter units, half): card_tue03.json.

## Lay book gap and fix (Mon 2 Nov, founder: "why aren't the lay bets just part of this artifact always down the bottom?")
No lay list was made for any meeting from Fri 30 Oct to Sun 1 Nov: the book above stops at Warrnambool Thu 29 Oct. That was
a miss, not a decision; the four-week paper trial is short those days. lay_sheet.py also still carried the old $30 band (the
rule went to $40 on 28 Oct) and now uses $40. From today the lay book is the last section of every meeting page
(meeting.sh runs lay_sheet.py --html after the market sheet). Ballarat Mon 2 Nov, on the 1:20pm re-price after the late
scratchings: 43 runners can trigger (2026-11-02-ballarat-s7n-lays.csv), settled at BSP with the day's results.

## Ballarat Mon 2 Nov settled (results pulled Mon 6:16pm, forced re-fetch), TAB's actual deductions (founder)
Deductions: R4 4c, R5 2c, R6 19c (includes Mystic Reign's late scratching), R7 42c.
- Bets at the open, PAPER (BetMatic placed none of them), at the price after deductions: Best Terms 6.30u $2.50 -> $2.44
  5th -6.30u; Marco Polo 0.97u $26 -> $25 WON +23.28u; Into You 0.72u $26 -> $25.50 7th -0.72u; Wintery 3.33u $7 -> $5.86
  WON +16.18u; Catwalk Icon 2.90u $4.60 -> $3.09 3rd -2.90u. Total 14.22u, +29.54u (+$1,108 at $37.50).
- Real money: Best Terms $331 at $2.60, placed after the open (R4 "now" test bet), 5th: -$331.
- Twitter card (half units, posted prices after deductions): Best Terms $2.44 -3.15u; Marco Polo BSP $6.48 (founder's figure;
  Form King had no BSP yet) +2.69u; Into You $13.74 -0.36u; Wintery $2.70 +2.84u; Catwalk Icon $3.32 -1.45u. +0.57u.
- Lay book (1u at BSP, $15-$40 and the trigger), 43 runners, BSPs in at 9:55pm: 3 lays, 0 winners, +2.76u (+$138 at $50):
  R3 Meritorious (lay at $21.70, BSP $24.82, 9th) +0.92u; R4 Urban Creed ($18.81, BSP $19.50, 3rd) +0.92u; R4 Pneuma
  ($24.81, BSP $29, 6th) +0.92u. Void, no result in Form King (late scratchings): Celestial Splendor R5, Skjaldmo R6,
  Azzacool and Hola Amigos R7, Till Queen R8. Marco Polo (lay at $17.53) won at BSP $6.48: not a lay.

## The unit is $50 (founder, Mon 2 Nov: "$50 a unit duck")
The 31 Oct change to $50 a unit reached the sends (Sun 1 Nov was sent at $50) but not the code: betmatic_orders.py's
UNIT_DOLLARS, betmatic_html.py and the fk-betmatic workflow's default unit still said $37.50, so every dollar figure quoted
on Mon 2 Nov was at $37.50. All three now default to $50. Kyneton Wed and Flemington Thu sheets rebuilt (orders unchanged,
dollar column now at $50: $6,191 and $3,804 if every order fired). Ballarat Mon open bets +29.54u = +$1,477 at $50.

## Kyneton Wed 4 Nov and Flemington Thu 5 Nov at the open (paper: markets opened Mon 2 Nov before any send; bot off, TAB unfunded)
Sheets as rebuilt Mon (big-overlay doubling, saddlecloth numbers), Form King's open, prices at Mon 7:40pm.
Kyneton: R1 Sabrina $11 1.19u; R2 Mongol Heer $9.50 2.63u (2.13x our $4.46, 31c short of the $9.81 doubling line);
R3 Emanating $15 1.40u; R6 Gregolimo $19.50 0.90u; R6 His Finest Hour $11 1.05u; R8 Foujita San $11 1.07u; R8 Placo $8
1.50u; R9 Blaze Away $26 0.71u. 8 bets, 10.45u ($522 at $50). None doubled.
Flemington Thu: R4 Sass Appeal $2.50 4.92u; R8 De Armas $4.60 2.68u; R9 Ice Kool $7.50 1.52u. 3 bets, 9.12u ($456). None doubled.

## Tuesday 3 Nov 9:30am re-price and top-ups (paper)
Final fields at 9:33am, all 1 Nov rules. Scratched since the sheets: Echuca R6 Flying Jude (on the card: refund).
- Flemington (s6t): top-up R6 Al Duca 2.35u at $9 (topup.py now keeps the metro $12 cap; before the fix it also offered
  Autumn Mystery $17, Vegas Jack $17, Enfjaar $26 and Juja Kibo $14, none of which the sheet's rule would bet).
- Echuca (s7t): top-ups R1 Mutsuhito 2.44u at $7.50, R5 Snow Party 0.88u at $21, R6 Ice Quake 4.99u at $4.40, R6 Here
  Comes Wozza 1.56u at $8.50. 9.87u.
- Mildura (gdt): none. Form King holds no opening price for Mildura, so the open fills cannot be checked.
- Wangaratta (s6t): none.

## Tuesday 3 Nov settled (results pulled Tue 6:30pm, forced re-fetch; Form King results and BSPs), paper at the open
No TAB deductions applied: the founder was asked for Flemington R2, R8 and Echuca R1 and said "Nah all good", so every
bet settles at the price taken. ONE DIFFERENCE FROM THE FOUNDER'S RESULTS ("Yauson, Ranarsson, Frozen Tide won rest lost"):
Form King has Celestial Option (Echuca R5, opened $13) WINNING at SP $4.20, BSP $4.92, Casamar second. Flagged to the
founder Tue evening and CONFIRMED by him ("it did too"): the $13 opener that plunged to $4.20 was missed off the card's
settle. Settled on Form King below; the bracketed figures are what the day read before the correction.
- Bets at the open, PAPER (BetMatic placed none: Echuca asked $2,780, Mildura $3,284, Wangaratta $3,166 and TAB took $0
  on each; Flemington was never sent, it opened Friday): Flemington (the $12-cap metro sheet, the one the Mon 2 Nov entry
  above records) Yauson 2.71u $4.80 WON +10.30u; Star Of Macedon 1.87u $6 3rd -1.87u; Ranarsson 3.25u $4 WON +9.75u.
  Echuca Frozen Tide 3.39u $4.40 WON +11.53u; Frewdamoss 0.77u $16 7th -0.77u; Celestial Option 0.96u $13 WON +11.52u;
  Flying Jude scratched, refund. Wangaratta Just Basil 2.33u $6 7th -2.33u; Startin'sumthin' 0.89u $21 8th -0.89u.
  Mildura: Form King holds no open, so no open fills. 8 bets, 4 won, 16.17u, +37.23u (+230%, +$1,862 at $50)
  [first reported as 3 won, +24.75u, +$1,238].
- Twitter card (half units at the posted prices; Frewdamoss and Celestial Option posted at BSP): Yauson $2.90 1.35u +2.56u;
  Star Of Macedon $3.90 0.94u -0.94u; Ranarsson $2.15 1.63u +1.87u; Frozen Tide $2.90 1.70u +3.23u; Frewdamoss BSP $16
  0.39u -0.39u; Celestial Option BSP $4.92 0.48u +1.88u; Just Basil $5 1.17u -1.17u; Startin'sumthin' $19 0.45u -0.45u;
  Flying Jude scratched, refund. 8.11u, +6.60u (+81%, +$330) [first reported as +4.24u].
- Real money: none (bot off, TAB $0.65).
- Lay book (1u at BSP, $15-$40 and the trigger; research/form_gbm/settle_lays.py, which reproduces Ballarat's +2.76u):
  Flemington 10 lays, 0 winners, +9.20u (Tanabata, Big Wigs, Gas Station Rose, Strike Package, Autumn Mystery, Magnaspin,
  Enfjaar, Mr Monaco, No Fuss, Cash); Echuca 3 lays, 0 winners, +2.76u (Altruist 2nd at BSP $22, Bronco Revolution,
  Laura's Gold); Mildura none in the band; Wangaratta 4 lays, 0 winners, +3.68u (Style Guide, Opus, American Russ,
  Tasman Park). 17 lays, 0 winners, +15.64u (+$782 at $50). Lay trial since Thu 29 Oct: Ballarat +2.76u, Tuesday +15.64u.
- Top-ups (tracked only, never bet): Al Duca 2.35u $9 7th -2.35u; Mutsuhito 2.44u $7.5 4th -2.44u; Snow Party 0.88u $21 4th -0.88u; Ice Quake 4.99u $4.4 7th -4.99u; Here Comes Wozza 1.56u $8.5 11th -1.56u. 12.22u, -12.22u.

## Units: backs $100, lays $200 (founder, 3 Nov 2026: "Do the lays at $200 and backs at $100")
Lay book at $200 a lay (holdout, $15-$40): +$4,900 a week, +$21,000 a month at the backtest's +49%, July -$2,200 on eight
winners, worst drawdown $15,200, biggest single hit $6,480; plan on +$11,000 to $13,000 a month. Backs at $100: +$7,800 a
week on the holdout with the new staking. Code and the send default moved to $100; Kyneton Wed and Flemington Thu sheets
re-dollared at $100 (orders unchanged): Kyneton $12,383, Flemington $7,611 if every order fired. Lay trial so far at $200:
34 lays, 0 winners, +31.28u = +$6,256.

## Founder, 3 Nov 2026 evening: "I'm comfortable we are on with Betfair, let's see how long until we get limited on TAB"
Betfair lays are the founder's to place by hand in the last two minutes (projected SP at or over the trigger, lay at SP
with the $40 max, $200 a lay); the morning list on each page is the instruction. From the first real lay the book carries
what actually matched, not the paper 1u, so a part-match settles as what went on. TAB: the backs run at $100 a unit until
TAB cuts them; every send's status line (asked / took / reduced) is logged per meeting so the first reduced fill is dated.
Nothing has been sent at $100 yet: the bot is off and TAB holds $0.65.

## Units again, 3 Nov evening (founder: "take it down 40% from what we are predicting. Do $50 a bet and $200 a lay")
Backs $50 a unit (code, send default, sheets re-dollared: Kyneton $6,191, Flemington Thu $3,804 if every order fired),
lays $200. The projection he asked for, every state at 40% under the Victorian backtest (backs +59% -> +35%, lays +49%
-> +29%; Victoria taken as a quarter of Australian racing, so all states = 4x Victoria): Victoria $128k backs + $140k
lays = $268k a year; all states about $1.07m a year, $89k a month ($511k backs, $561k lays). At the full backtest, all
states, about $1.8m. Every non-Victorian figure assumes the edge travels, which the August week did not show on the
back side (+13%, one standard error from zero) and has never been tested on the lay side.

## The book since 9 Oct, as it happened (founder, 3 Nov: "What's our book been since we've been live October 9")
Open book, model stakes at Form King's open, TAB's deductions where reported, paper plus the few real fills at their model
stake; abandoned meetings void (Ballarat Fri 23 Oct after R2, Traralgon Sat 31 Oct). From this file's own settled entries:
| Week | Bets | Won | Staked | P/L | ROI |
|---|---|---|---|---|---|
| Fri 9 - Sun 18 Oct (forward test) | 49 | 9 | 49.53u | +49.15u | +99% |
| Mon 19 - Sun 25 Oct | 22 | 10 | 61.46u | +135.57u | +221% |
| Mon 26 Oct - Sun 1 Nov | 41 | 6 | 127.84u | +32.95u | +26% |
| Mon 2 - Tue 3 Nov | 13 | 6 | 30.39u | +66.77u | +220% |
| **Total** | **125** | **31** | **269.22u** | **+284.44u** | **+106%** |
At $50 a unit that is +$14,222 on $13,461 staked. Real money the model's bets actually took: Geelong Murshidi +$1,260,
Cranbourne Fri 23 Oct -$193, Flemington Sat 24 Oct -$110, Ballarat Mon 2 Nov Best Terms -$331: +$626 on $760. Don copies
(founder's call, Sat 31 Oct) +$810 on $650. Lay book, paper from 28 Oct: 34 lays, 0 winners, +31.28u (+$6,256 at $200).

## The weekend's lays, back-filled (Fri 30 Oct to Sun 1 Nov; founder, 3 Nov: "Sunday and Saturday?")
No lay list was made on these days (the 2 Nov gap entry). Built now from the morning model files as they stood (Kilmore
and Pakenham gd, Flemington gd, Mortlake/Wycheproof/Healesville of, Mornington s7v2), the rule unchanged, settled at BSP from
the Form King results; the sheets are DAYPREFIX-TAG-lays.csv. A back-fill, labelled as one: the rule is mechanical and was
fixed on 23 Oct, so nothing was chosen after the results, but these days were not watched live.
- Fri 30 Oct: Kilmore 6 lays, 0 winners, +5.52u; Pakenham 10 lays, 0 winners, +9.20u.
- Sat 31 Oct: Flemington 7 lays, 0 winners, +6.44u (Sass Appeal, Idle Flyer, Youmzaa, Grand Larceny, Mbube, Naifah, Swift
  Force); Mortlake 6 lays, GARGANTUAN WON at BSP $24 (lay at $20.11+), -18.40u; Wycheproof 3 lays, MORE GIVE IT WON at
  BSP $18.50 (lay at $15+), -15.66u; Healesville no lay (Betfair SP on 13 of 29 runners only, R4-R6 void); Traralgon
  abandoned.
- Sun 1 Nov: Mornington 3 lays, 0 winners, +2.76u (Fam Gorman 2nd at $15.50, Master Of The Air, Warrior Within).
Weekend: 35 lays, 2 winners, -10.14u (-$2,028 at $200). Both winners were $15-$25 lays at bush meetings with thin pools.
TRIAL TO DATE (28 Oct to 3 Nov, 8 race days): 69 lays, 2 winners, +21.14u, +31% on the lay stake (+$4,228 at $200).

## Pages: lay and back book at the bottom, Game day race by race (founder, 3 Nov 2026)
From Kyneton Wed 4 Nov every page has the open bets at the top, a Game day section (per race: the lays with their lay-if-SP
price, the back candidates with their back-if-favourite range) and the lay and back books under it, Game day button in the
top bar. The back rule is in TIPPING_RULES.md (paper from Thu 5 Nov; the Kyneton page carries it a day early, also paper).
Had it run this week: Tue 3 Nov one back, Tempesti (Flemington R5, favourite at BSP $6.06, ours $15.54), 13th, -1u; Mon 2 Nov
none. Settle each day: settle_lays.py and settle_backs.py over the meeting's results.

## Kyneton Wed 4 Nov, 9:32am re-price (final field, Form King's rating Dead 5, not the Heavy 8 the Monday sheet was priced on)
34 scratched since the sheet, among them three of the eight open-book horses (Foujita San and Placo R8, Blaze Away R9:
refunds). Open book standing, Monday's sheet at Form King's open: Sabrina 1.19u $11, Mongol Heer 2.63u $9.50, Emanating
1.40u $15, Gregolimo 0.90u $19.50, His Finest Hour 1.05u $11: 5 bets, 7.17u, paper (bot off). Top-ups (paper, tracked only):
Tomanado R9 0.74u at $13 (ours $10.48, take $12.57); His Finest Hour already at full stake; the rest under take-at (Mongol
Heer $3.30, Emanating $5.50, Extreme Turbo $3.40 have been backed in). The 9:32 sheet on Dead 5 (d5w: 111 orders, 39
horses, 176.59u if every order fired) is kept as 2026-11-04-kyneton-d5w-orders*.csv for the record and is NOT the open
book; the run overwrote the pre-open sheet and it was restored from git, and pricemtg.sh now writes a re-price under its
own tag. Lay book 2026-11-04-kyneton-d5w-lays.csv and back book -backs.csv on the page, with Game day.
Kyneton 11:50am refresh (founder: "update artifact for me to follow today"): Johnny Tightlips R1 out (35 scratched now),
page rebuilt on the 11:50 prices (d5m), open book unchanged at 5 bets 7.17u with TAB's deductions (R1 31c, R2 16c, R3 13c,
R4 12c, R5 17c, R6 22c, R7 3c, R8 23c, R9 63c). CORRECTION to the 9:32 line: "His Finest Hour already at full stake" was
read off the overwritten sheet; against the real pre-open stake (1.05u) the top-up rule offers 0.71u at $8.50 (paper,
tracked only), on top of Tomanado 0.74u at $13 from 9:32. Mercer card update sent with deductions and the three
scratchings shown as SCR (no refund word, founder's call).

## Friday 6 Nov priced Wed 4 Nov 12:30pm (final fields; no market open on either), Saturday 7 Nov Flemington pending
Cranbourne Fri on the official Dead 5 (d5f): 73 orders on 30 horses, 88.51u if every order fired. Warrnambool Fri on the
official Dead 4 (d4f): 50 orders on 19 horses, 75.51u. CORRECTED 1:50pm: that first run priced 53 of the 75 runners, because the two-meeting scratchings export (Warrnambool + Flemington Sat) was split at the meeting headings and its prices sections sit at the end of the file, so Warrnambool's went with Flemington's; drop_scr then dropped every runner the short prices file did not list and every price came out too short. Re-split by section and re-priced: 73 orders on 30 horses, 96.25u. Rain (Open-Meteo through the fk-experiment runner, the sandbox cannot
reach it): Cranbourne 8.4mm Wed, 1.9 Thu, 0.4 Fri; Warrnambool 4.6 / 0.4 / 6.7; under the 15mm line, so the official
rating stands for both. Flemington Sat 7 Nov: Form King has no rating yet; forecast 7.2mm Wed, dry Thu and Fri, 17.2mm
ON Saturday (97%, max 13C), so the export is asked for SOFT 6 (founder to confirm); its export and the market-open check
failed on GitHub's API rate limit (fetch_history.sh pulls 430 release files through the API on every run and this
morning's runs used the hour's quota) and are re-run once it clears. Sheets are -betmatic-preopen.csv (copied from the
re-price tag files, since pricemtg.sh now writes under the tag). Pages published with the empty open-bets box, lay book,
back book and game day. BetMatic check 10:48am: every bot session off, no bot machine connected, TAB $0.65.
Flemington Sat 7 Nov (Stakes Day) priced Wed 1:50pm on SOFT 6 (our call: 17.2mm forecast on the day; Form King has no
rating yet), final fields, 7 out: 32 orders on 16 horses, 43.70u if every order fired (metro $12 cap). The export ran on the
new history cache (f1f631f) without touching the API limit.

## Kyneton Wed 4 Nov settled on the founder's results (Wed afternoon: "Gregolimo and Emanating won. Rest have lost"), TAB's deductions
- Bets at the open, PAPER (BetMatic placed none; bot off, TAB $0.65), price after TAB's deduction: Sabrina 1.19u $11 -> $7.90
  lost -1.19u; Mongol Heer 2.63u $9.50 -> $8.14 lost -2.63u; Emanating 1.40u $15 -> $13.18 WON +17.05u; Gregolimo 0.90u
  $19.50 -> $15.43 WON +12.99u; His Finest Hour 1.05u $11 -> $8.80 lost -1.05u. 5 bets, 2 won, 7.17u, +25.17u (+351%,
  +$1,258 at $50). Foujita San, Placo, Blaze Away scratched.
- Twitter card (half units, posted prices after deductions): Sabrina $4.79 -0.59u; Mongol Heer $4.36 -1.31u; Emanating
  $4.92 +2.74u; Gregolimo $9.58 +3.86u; His Finest Hour $8.80 -0.53u. 3.58u, +4.17u (+117%, +$209 at $50).
- Real money: none.
- Top-ups (tracked only): His Finest Hour 0.71u at $8.50 lost -0.71u; Tomanado R9 0.74u at $13 to run.
- Lay and back books settle at BSP once Form King has the results (7:15pm).

## Friday 6 and Saturday 7 Nov at the open (paper: bot off, TAB $0.65), read Wed 7:10pm
Flemington Sat opened Wed 12:33-2:56pm, before the 1:50pm "nothing open" check, which read odds stored at 12:01pm; Cranbourne
Fri opened Wed 3:41-4:04pm; Warrnambool Fri not open. Fills at Form King's open on the pre-open sheets:
Cranbourne R6 Speir $8 1.88u (ours $4.99), R8 Power And The Beat $10 2.22u (ours $5.15); Flemington Sat R3 Litzdeel $8.50 1.46u
(ours $5.15), R9 Salaria $11 0.63u (ours $7.21). 4 bets, 6.19u. None doubled (all under 2.2x). Prices at 7:07pm: Speir $4.80,
Power And The Beat $4.40, Litzdeel $8.50, Salaria $11. Cards: card_frisat07_mercer_now.json (Mercer, live prices, Twitter
units) and card_frisat07_plain_open.json (no Mercer, the open, full units, rated).
Kyneton Wed confirmed by Form King's results (pulled 7:19pm): Emanating WON (SP $4.60, BSP $5.50; we had $13.18 after the
deduction), Gregolimo WON (SP $12, BSP $15.78; we had $15.43), Sabrina 4th, Mongol Heer 6th, His Finest Hour 8th. The open
book and the card stand as settled above. Top-up Tomanado R9 6th: -0.74u (top-ups for the day -1.45u).
- Lay book (1u = $200 at BSP, d5m list): Exploit R2 (BSP $18.25, 8th), Platinum Rush R3 ($22, 3rd), Weather Delay R6 ($17.50,
  9th), Who I Think I Am R6 ($18, 6th): 4 lays, 0 winners, +3.68u (+$736). Trial to date (28 Oct to 4 Nov, 9 race days):
  73 lays, 2 winners, +24.82u, +34% on the lay stake (+$4,964 at $200).
- Back book (favourite $4-$7 we rate 1.6x+, paper): none landed.

## Top-ups stopped (founder, Wed 4 Nov evening: "I think we can stop doing top up")
No more 9:30am top-up checks or top-up lines from Thu 5 Nov. The 9:30 routine now re-prices, refreshes the lay book, back
book and game day, and reports the open bets still running.
Flemington Sat emergencies (founder, Wed evening: "why didn't you include emergencies Saturday"): the seven are out of the
sheet because none has a start yet (no main-field scratching), and pricing them in would lengthen every price in R4, R5
and R9. Priced as if each got in (s6e, kept for the record): Hankee Alpha R4 ours $5.91, opened $4.20 (under our price, now
$2.90); Superfabulistic R5 $22.80 (opened $26), Classic Gem R5 $28.88 ($21), Lawborough R9 $12.73 ($15, past the metro $12
cap), Brave Design R9 $15.19 ($13), Fission R9 $59.28 ($34), My Zephyr R9 $95.73 ($51). None would have been a bet at the
open. Any that gets a start is priced in at the Saturday 9:30 re-price, when mkprices lets it in for its scratching.

## Thu 5 Nov 9am: Flemington Thu and Cranbourne Fri re-priced (official ratings from RV Stewards, founder's screenshot)
Flemington Thu, Soft 5 official (we priced Soft 5 Mon): re-priced on the final field (s5t), 25 out (scratchings and the
emergencies with no start), none of ours. Open bets unchanged: Sass Appeal 4.92u $2.50 (now $1.70; ours $1.58 on the final
field), De Armas 2.68u $4.60 (now $3.20), Ice Kool 1.52u $7.50 (now $6.25). Mercer card at 8:30am prices: Sass Appeal and De
Armas at BSP (founder: they will drift), Ice Kool $6.25. Lay and back books and game day refreshed.
Cranbourne Fri, Soft 6 official (we priced Dead 5 Wed): re-priced (s6f). Ours: Speir $4.99 to $5.38, Power And The Beat
$5.15 to $4.96; both taken at the open ($8 and $10) and stay. 57 lay candidates (was 58). Warrnambool Fri not in the
screenshot; still on the Dead 4 Wed rating.
Flemington Thu 9:30am routine: 9 more out after 8:38am (R3 Just Folk, Merrigold; R6 Surfy Pete, Hiyaam Proud, Untapped,
Hedjet; R7 Southern Sway; R8 Chocolate Freckles; R9 Saluted), none of ours. Re-priced on that field (s5u): Sass Appeal
$1.57, De Armas $3.07, Ice Kool $3.26 (now $1.70, $3.10, $6.50). R3 moved most (Feroce $6.31 to $4.86). 65 lay candidates.

## Sat 7 and Sun 8 Nov priced Thu 5 Nov 12:40pm (the new 12:17pm routine: fields 10:30-11am, riders at 12)
Pulled Fri, Sat and Sun by date (force no): three new Victorian meetings. No market open on any of them.
- Geelong Sat, Dead (Form King; 9.1mm forecast to race day, under the 15mm line): 85 orders on 35 horses, 84.37u if every
  order fired (d5g). 4 riders still to come.
- Ararat Sun, Slow (Form King; 3.4mm): 89 orders on 36 horses, 92.01u (s6a). PROVISIONAL: 13 of 92 runners have no rider
  yet (Sunday's riders come Friday), so it is re-pulled (force yes) and re-priced Friday after 12 before anything is sent.
- Balnarring Sat (picnic), Heavy 8 (RV Stewards): 70 orders on 24 horses (h8b). PAPER ONLY: the model's history holds no
  Balnarring meeting and its picnic meetings (Hanging Rock, Towong, Great Western) all sit before the 3 Jun holdout, so
  nothing on picnic racing has been tested out of sample.
The first cut of all three sheets had no saddlecloth numbers (the entry-numbers file was not copied into data/live_bets);
fixed, and pricemtg.sh now copies it on every run. TAB $0.65, bot not connected.
Flemington Thu settled R1-R8 on Form King's results (pulled 6:25pm; R9 not in yet):
- Open book: Sass Appeal R4 4.92u $2.50 (14c ded) 2nd (BSP $1.79) -4.92u; De Armas R8 2.68u $4.60 3rd (BSP $3.86) -2.68u;
  Ice Kool R9 1.52u $7.50 (34c ded, pays $5.29) waits for R9. So far -7.60u.
- Twitter card: Sass Appeal BSP 2.46u 2nd -2.46u; De Armas BSP 1.34u 3rd -1.34u; Ice Kool $6.25 (34c ded, $4.47) 0.76u waits.
- Lay book ($200 at BSP, s5u list): Chakado R2 ($17, 12th), Didn't Miss Many R2 ($40, 6th), Different Gravy R5 ($28, 10th),
  Single Choice R5 ($40, 12th), Placo R5 ($34, 2nd), Unwavering R7 ($34, 10th), Your Colour R8 ($40, 8th): 7 lays, 0
  winners, +6.44u (+$1,288). R9 waits.
- Back book: none landed (no BSP favourite at $4-$7 that we rated 1.6x+).
- Feroce (R3, not a bet) 4th at SP $4.60.
Flemington Thu R9 in (pulled 6:40pm): Ice Kool 6th (SP $6, BSP $8.40), Rey Magnerio won. DAY SETTLED:
- Open book 3 bets 9.12u, 0 winners, -9.12u (-$456 at $50). Twitter card 4.56u out, 0 in, -4.56u (-100%).
- Lay book 7 lays, 0 winners, +6.44u (+$1,288 at $200); no R9 lay (none at BSP $15-$40 and 1.6x ours). Back book none.
- Paper day: +$832 ($1,288 lays less $456 open book). Lay trial (28 Oct to 5 Nov): 80 lays, 2 winners, +31.26u.

## Friday 6 Nov at the open (paper; bot off)
Warrnambool opened overnight (all 8 races at 9:20am Fri; scratched Vulcana R1, Unamerican, Duhlata, Sanika, Phoenician R7,
none of ours): R3 Big Vee 4.94u at $2.73 (ours $2.24), R4 Mamzelle Raine 1.08u at $13 (ours $8.02). Cranbourne (opened
Wed): R6 Speir 1.88u at $8, R8 Power And The Beat 2.22u at $10. Day 10.12u. Mercer card at 9:20am best prices (Big Vee
$2.50, Mamzelle Raine $7.50, Speir $5, Power And The Beat $4.60; half units); no-Mercer card at the open.
Fri 9:30am re-price on the final fields (Warrnambool d4g, Cranbourne s6g; Form King now Dead and Slow, same bands as
priced): ours now Big Vee $2.38, Mamzelle Raine $10.27 (was $8.02: the model has gone off it as the market came in, $13 to
$7.50), Speir $4.92, Power And The Beat $5.38. All four still running; no scratching among them. Lay candidates:
Warrnambool 52, Cranbourne 53. The day on one page: research/form_gbm/day_page.py (founder, 5 Nov: "Create one artifact
for all of today please").

## Fri 6 Nov 12:17pm run: Ararat re-pulled with riders, Hamilton Mon priced
- Ararat Sun re-pulled (force yes) once Sunday's riders were in: 3 of 90 runners still riderless (was 13 of 92). Re-priced
  (s6b): 83 orders on 33 horses. But Ararat's market OPENED Fri 10:41am, before the riders were in, so the open was met by
  Thursday's sheet of record (s6a), which stays the record. Paper fills at the open: R2 Model Gigi 4.79u $4.40 (ours $2.75,
  with riders $2.70), R3 Pray For Elegance 1.50u $9 ($6.02, $5.82), R5 Selita's Fury 1.73u $7.50 ($5.35, $7.15). 8.02u.
- Hamilton Mon, Slow (Form King; 1.2mm to race day): 75 orders on 30 horses, 80.78u if every order fired (s6h); 2 riders
  to come; no market yet.
- Geelong Sat still not open. TAB $0.65, bot not connected (last connect 5:11am Thu): nothing sent.
Warrnambool Fri settled (Form King results, 7:25pm):
- Open book: Big Vee R3 4.94u $2.73 WON (SP $2.30, BSP $2.88) +8.55u; Mamzelle Raine R4 1.08u $13 7th (BSP $15.09) -1.08u.
  +7.47u (+$374 at $50). No deduction reported (no scratching in R3 or R4).
- Twitter card: Big Vee $2.50 2.47u won +3.71u; Mamzelle Raine $7.50 0.54u lost: 3.01u out, 6.18u in, +3.17u (+105%).
- Lay book ($200, d4g): 7 lays, 1 winner, No Rumours R7 (BSP $17.18) -16.18u; Francine, Ballynacally, Dandruff, Carnival
  Riches (2nd), The Daily Planet, Parkrun lost +0.92u each: -10.66u (-$2,132). Lay trial: 87 lays, 3 winners, +20.60u.
- Back book: none qualified.
Cranbourne Fri (founder, 9:45pm): Speir R6 1.88u $8 lost -1.88u; Power And The Beat R8 SCRATCHED late, refunded (2.22u void;
marked SCR in the prices file). Card: Speir 0.94u lost, Power And The Beat 1.11u refunded.
FRIDAY OPEN BOOK: 3 bets settled, 1 winner (Big Vee), +5.59u (+$280). Card: 3.95u out, 6.18u in, +2.23u (+56%).
Cranbourne lays wait for Form King's results.
Cranbourne Fri lays R1-R5 (Form King results, 9:55pm; R6-R8 not posted yet): Cowboykickedfive R1 ($24, 7th), Trentino R4
($16.46, 3rd), Mykindakandy R5 ($28, 5th), Brutal World R5 ($31.78, 3rd), Claymore Mine R5 ($32, 4th): 5 lays, 0 winners,
+4.60u (+$920). R6-R8 lays settle when the results post.
Cranbourne Fri fully settled (Form King results Sat 7:05am): Speir 7th (SP $8.50, BSP $13.50). Lays R6-R8: Room For Bingo
($30, 6th), Weapon Clear ($34.46, 4th), Kastun Star ($17.50, 5th), Couldthisbetheone ($30, 9th), Bit Of Shoosh ($40, 6th).
Cranbourne lays 10, 0 winners, +9.20u (+$1,840); R7 winner She's Pretty Rich (BSP $37.56) was not on the lay list.
FRIDAY FINAL (paper): open +5.59u (+$280); lays 17, 1 winner, -1.46u (-$292); backs none; day -$12. Card +2.23u (+56%).
Lay trial (28 Oct to 6 Nov): 97 lays, 3 winners, +29.80u (+$5,960 at $200).

## Saturday 7 Nov at the open (paper; bot off)
Flemington (opened Wed): R3 Litzdeel 1.46u $8.50 (ours $5.15), R9 Salaria 0.63u $11 ($7.21). Geelong opened Sat 7:58am:
R7 Fridge Monster 2.78u $22.67 (ours $7.72; 2.9x ours, so the big-overlay double fired), R7 Shaalute 0.88u $13 ($9.59).
Balnarring (paper meeting) no market at 8:35am. Day 5.75u. Cards: Mercer at 8:35am prices (Litzdeel $7, Salaria $11,
Fridge Monster $11, Shaalute $8; half units); no-Mercer at the open.
Sat 9:30am re-price on the final fields (Flemington s6t Soft 6, our call; Geelong d5h Dead; Balnarring h8c Heavy 8, paper):
20 scratchings at Flemington, 30 at Geelong, 11 at Balnarring, none of ours. Ours now: Litzdeel $4.91, Salaria $7.92,
Fridge Monster $6.93, Shaalute $9.83. Lay candidates: Flemington 72, Geelong 54. Balnarring's market still not up.

## Sat 7 Nov 12:17pm run: Mornington Tue priced, Hamilton Mon opened
- Hamilton Mon opened Sat 10:14-10:43am on Friday's sheet: paper fills R2 Al's Diemen 0.81u $17 (ours $10.37), R7 Sweet City
  Dancer 0.69u $17.50 ($11.98). 1.50u.
- Mornington Tue, Dead (Form King; no rain to race day): 78 orders on 31 horses (d5m). Its market OPENED Sat 11:02-11:14am,
  before this run pulled the meeting (fields out about 10:30, riders at 12), so the whole meeting is MISSED and its sheet
  of record is empty. Would have filled: R4 Marilyn's Edge $9.50 2.14u (ours $5.30), R5 Nightowl $8.50 1.46u ($6.16), R5
  Tassadar $34 0.67u ($14.94), R8 Express Guard $19 0.97u ($10.67), R8 It's Gnarly $19 1.08u ($9.74): 6.32u
  (2026-11-10-mornington-missed.csv). TIMING: TAB opened Mornington about 30 minutes after its fields came out, an hour
  before riders, so a 12:17pm pull cannot catch that kind of open. Put to the founder.
- TAB $0.65, bot not connected.

## Saturday 7 Nov settled (Form King results, 11:55pm; paper, bot off)
- Open book: Litzdeel R3 1.46u $8.50 5th (SP $8.50, BSP $8.84) -1.46u; Salaria R9 0.63u $11 8th (BSP $14.47) -0.63u; Fridge
  Monster R7 2.78u $22.67 11th (SP $8.50, BSP $8.25) -2.78u; Shaalute R7 0.88u $13 WON (SP $10, BSP $11.70) +10.56u.
  4 bets, 1 winner, +5.69u (+$284.50 at $50). No deduction reported.
- Twitter card (half units, Mercer prices): Litzdeel $7 0.73u, Salaria $11 0.32u, Fridge Monster $11 1.39u lost; Shaalute $8
  0.44u won +3.08u: 2.88u out, 3.52u in, +0.64u (+22%).
- Lay book ($200): Flemington (s6t) 11 lays, 1 winner, Lawborough R9 (BSP $19.06) -18.06u: -8.86u (-$1,772). Geelong (d5h)
  8 lays, 1 winner, Crank R6 (BSP $22) -21.00u: -14.56u (-$2,912); Somebody Told Me R8 void (scratched late, not in the
  results). Balnarring no lays (no Betfair prices). Day lays 19, 2 winners, -23.42u (-$4,684).
- Back book ($500): Geelong R7 Miss Castelvecchio (BSP fav $4.65) 13th -1u (-$500).
SATURDAY FINAL (paper): open +$284.50; lays -$4,684; back -$500; day -$4,899.50. Card +0.64u (+22%).
Lay trial (28 Oct to 7 Nov): 116 lays, 5 winners, +6.38u (+$1,276 at $200).

## Sun 8 Nov 9:30am re-price (paper; bot off)
- Ararat: Form King now Dead (priced Slow Thu/Fri, so the band changed: re-exported on Dead), 14 scratchings, none of ours.
  Re-priced s6c. Ours now: Model Gigi R2 $2.92 (open $4.40, now $5.50), Pray For Elegance R3 $5.73 ($9, now $6), Selita's
  Fury R5 $6.14 ($7.50, now $6.50). All three running, 8.02u. Deductions to come: R2, R3 and R5 each had a scratching.
- Hamilton Mon (founder: "Hamilton as well"): still Slow, no scratchings yet (Monday morning). Page refreshed at Sun 9:45am
  prices (s6i, same model prices as s6h). Al's Diemen R2 0.81u $17 (ours $10.37, now $9), Sweet City Dancer R7 0.69u $17.50
  ($11.98, now $14). Both running.
- Mornington Tue cards (founder, Sun 8 Nov: "Mornington card, Mercer and not Mercer"): the open was missed, so both cards
  are at Sun 1:10pm TAB prices against the d5m sheet. Qualifying now: R5 Tassadar $34 0.67u (ours $14.94), R8 It's Gnarly
  $15 0.87u ($9.74; the second order needs $16.66+). The other three missed horses have firmed under their minimum (Marilyn's
  Edge $6.50 vs $6.93, Nightowl $5.50 vs $8.12, Express Guard $11 vs $14.46). Exacting Standard R3 scratched.
- Mornington Tue cards REPLACED (founder: "No I wanted what we would of had at the open, a Mercer and non Mercer card"): both
  cards at the Sat 11:02am open, the five would-be fills of 2026-11-10-mornington-missed.csv. Mercer half units: Marilyn's
  Edge $9.50 1.07u, Nightowl $8.50 0.73u, Tassadar $34 0.34u, Express Guard $19 0.49u, It's Gnarly $19 0.54u (3.17u).
  No-Mercer full units with rated: 2.14u, 1.46u, 0.67u, 0.97u, 1.08u (6.32u). Settle Mornington on these.

## Sunday 8 Nov Ararat, our three on the founder's results (Sun afternoon: "Win, scratched, loss")
- Open book (paper, no deduction reported yet): Model Gigi R2 4.79u $4.40 WON +16.29u; Pray For Elegance R3 1.50u SCRATCHED
  late, refunded; Selita's Fury R5 1.73u $7.50 lost -1.73u. 6.52u settled, +14.56u (+$728 at $50).
- Twitter card (Mercer, 9:45am prices, half units): Model Gigi $5.50 2.40u won +10.80u; Pray For Elegance 0.75u refunded;
  Selita's Fury $6.50 0.87u lost -0.87u. PLUS the founder's own late tip, Daniel Boone (R2) 2u, lost -2.00u (ours $14.36:
  not a model bet; ran in Model Gigi's race). Card 5.27u out, 13.20u back, +7.93u (+150%); the model's three alone +9.93u.
- Lays and backs settle on Form King's results after R8.

## Twitter record, week Mon 2 - Sun 8 Nov (founder, Sun 8 Nov: "What's our total for Twitter now" / "Make a card and tweet")
From the tweeted cards as settled above (half units, posted prices; BSP-posted tips not counted in "beat BSP"; Daniel Boone
the founder's own tip included): 31 tips, 11 winners, 35.47u, +17.58u (+50%); posted price beat BSP 12 of 24.
Mon +0.57 (7.12u), Tue +6.60 (8.11u), Wed +4.17 (3.58u), Thu -4.56 (4.56u), Fri +2.23 (3.95u), Sat +0.64 (2.88u), Sun +7.93 (5.27u).
Card: branding/mercer-tipping/summary_week_02_08.json. RUNNING TOTAL from the posted week cards, Sat 17 Oct - Sun 8 Nov:
17-24 Oct 45 tips 14 won 62.5u +141.9u; Sun 25 Oct 1 tip 1 won 1.12u +5.98u; 26 Oct-1 Nov 39 tips 5 won 56.8u +1.7u; 2-8 Nov
31 tips 11 won 35.47u +17.58u: 116 tips, 31 winners, 155.9u staked, +167.2u (+107%). Thu 15 and Fri 16 Oct are not in it
(full-stake public record, before the half-unit rule of 20 Oct).
- Ararat back book so far (Form King results R1-R4, 4:20pm): Daniel Boone R2 was the BSP favourite at $4.45, ours $14.36,
  a back (the founder's late Twitter tip was the same horse), 3rd: -1u (-$500). No lays qualified R1-R4. R5-R8 to settle.
WEEK Mon 2 - Sun 8 Nov (paper; Sunday's R5-R8 lays and backs to come): open book 30 bets, 11 won, 66.85u, +108.66u (+163%,
+$5,433); lays 67, 3 won, +3.64u (+$728); BSP favourite backs 2, 0 won, -$1,000; total +$5,161. Twitter +17.58u (+50%).
Real money: Best Terms -$331 (Mon).

## $8-$12 lay band added (founder, Sun 8 Nov: "Yes add it in"), paper from Mon 9 Nov
Hamilton Mon (s6i) and Mornington Tue (d5m) lay books rebuilt with both bands and republished. Sunday's Ararat would have
had 2 lays in the band to R6, both losers (+1.84u): not counted, the band starts Monday.

## Sunday 8 Nov Ararat settled (Form King results and BSPs, 7:10pm)
- Open book: Model Gigi R2 4.79u $4.40 WON +16.29u; Pray For Elegance R3 scratched; Selita's Fury R5 1.73u $7.50 8th -1.73u:
  +14.56u (+$728). No deduction reported.
- Lays ($15-$40 at 1.6x, the rule of the day): 6 lays, 0 winners, +5.52u (+$1,104): Masked Marauder R4, Selita's Fury R5
  (also our open bet), Trigger Warning R5, Thedoctoroflove R6, Unseen Ruler R6 (2nd), Tikemyson R6. Nothing in R7-R8.
- Back: Daniel Boone R2 (BSP fav $4.45, ours $14.36) 3rd -1u (-$500).
SUNDAY FINAL (paper): +$1,332. Twitter card +7.93u.
WEEK Mon 2 - Sun 8 Nov FINAL (paper; one real bet, Best Terms -$331): open book 30 bets, 11 won, +108.66u on 66.85u (+163%,
+$5,433); lays 73, 3 won, +9.16u (+$1,832); BSP favourite backs 2, 0 won (-$1,000); total +$6,265. Twitter +17.58u (+50%).
Lay trial (28 Oct to 8 Nov): 122 lays, 5 winners, +11.90u (+$2,380 at $200).

## Since live, 9 Oct - 8 Nov, every strategy on the same footing (founder, 8 Nov: "Why can't you just look at results from 9 October")
Each meeting's own live model file and Form King's results/BSPs (research/form_gbm/t_since_live.py, 48 meetings; Yarra Valley
24 Oct has no results export). Open book as it happened (+326.33u = +$16,317 at $50). Lays $15-$40 at 1.5x: 306 lays, 12 won
(BSP said 13.2), +48.38u (+$9,676 at $200, +$2,419 at $50). Lays $8-$12 at 1.6x: 49 lays, 4 won (5.0), +6.31u (+$1,262 /
+$316). BSP favourite backs: 23, 7 won (5.0), +7.48u (+$3,739 at $500, +$374 at $50). Total +$30,994 at $200 lays and $500
backs; +$19,426 at Friday's $50 lays and $50 backs.

## Mon 9 Nov 9:30am re-price (paper; bot off)
Hamilton still Slow (Form King), 10 scratchings, none of ours; re-priced s6j on the final field. Ours now: Al's Diemen R2
$10.26 (open $17, now $9), Sweet City Dancer R7 $12.17 ($17.50, now $14). Both running, 1.50u. Lay book on the new rules
($8-$12 at 1.6x, $15-$40 at 1.5x). Betfair manifest written (the runner is not live until Friday).

## Monday 9 Nov Hamilton settled (Form King results, Tue 9:50am; paper, bot off)
- Open book: Al's Diemen R2 0.81u $17, 7th (SP $13, BSP $19.56) -0.81u; Sweet City Dancer R7 0.69u $17.50, 6th (SP $16,
  BSP $24) -0.69u. -1.50u (-$75).
- Twitter (Mercer card at current prices): Al's Diemen 0.41u $9 lost, Sweet City Dancer 0.35u $14 lost: -0.76u.
- Lay book (s6j, $200 a lay): 13 lays, 2 winners, -49.29u (-$9,858; -$2,465 at Friday's $50). $8-$12: 2 lays, 0 won, +1.84u.
  $15-$40: 11 lays, 2 won (R1 Invisible Caravan BSP $37.41, R6 French Navy BSP $24), -51.13u. Void 5 (late scratchings).
- Back book: no BSP favourite inside its range. 0 backs.

## Twitter units doubled from Thu 12 Nov (founder, Tue 10 Nov: "We are doubling Twitter units", "From Thursday onwards")
Posted units become the full model stake, the same as the open bets (half since 20 Oct). Wednesday's Ballarat card stays
at half (Goodness 1.85u, Ladhar 1.66u, Tempt The Gods 0.51u); Thursday's Seymour card is the first at full units.

## Track bias: tested and left out (founder, Tue 10 Nov: "Yeah good - don't put it in")
Track-bias inputs for every track (research/form_gbm/t_trackbias_ab.py) did not improve the model on 3 Jun - 9 Nov
(open-bet profit +1,165.6u v +1,237.8u for the current inputs). The model stays as it is, and the Sandown Lakeside G3 on
Sat 14 Nov is priced by the model with no hand shade for the leader bias.

## Tuesday 10 Nov Mornington settled (Form King results, Tue 7:40pm; the open was missed, so no open bets count)
- Open book: NOT COUNTED. TAB opened Mornington Sat 11:02am, before we priced it, so the meeting was missed and its sheet
  of record is empty (Sat 7 Nov entry). For the record only, the five would-be fills (2026-11-10-mornington-missed.csv,
  TAB's deductions R4 15c, R5 16c): Marilyn's Edge R4 2.14u $9.50 WON (paid $8.23 after 15c; SP $4.20, BSP $5.70);
  Nightowl 8th, Tassadar 12th, Express Guard 12th, It's Gnarly 9th. Would have been +11.28u on 6.32u.
- Twitter (Mercer card, current prices with deductions, half units): Marilyn's Edge 1.07u $6.50 -> $5.67 won +5.00u;
  Nightowl 0.73u, Tassadar 0.34u, Express Guard 0.49u, It's Gnarly 0.54u lost. 3.17u, +2.90u.
- Lay book (d5n, $200 a lay): 7 lays, 1 winner, -4.98u (-$996; -$249 at Friday's $50). $8-$12: R1 Molesworth BSP $11.50
  WON, -10.50u (its window $11.31-$12; the founder confirmed $11.50, Form King's figure: the $12.50 said at midday was wrong,
  and so was "no lay"). $15-$40: 6 lays, 0 won, +5.52u (Fantastic Beast 2nd at $30.02).
- Back book: no BSP favourite inside its range. 0 backs.
- Rule tracker (research/form_gbm/track_rules.py, 47 meetings): the ten paper rules +261.74u since 9 Oct; Mornington alone
  -12.72u (Molesworth hit both the $8-$12 lay rules; the $12-$15 drift lay -11.66u).

## Wednesday 11 Nov Ballarat settled (Form King results, Thu 9:50am; paper, bot off)
- Open book: Goodness R1 3.69u $3.90, TAB's 33c deduction -> $2.94, WON (SP $2.05, BSP $2.24) +7.17u; Ladhar R4 3.32u
  $4.60, 4th (SP $5.50, BSP $7) -3.32u; Tempt The Gods R7 1.01u $13, 9th (SP $9.50; R7's deduction not reported) -1.01u.
  +2.84u (+$142).
- Twitter (Mercer card, current prices with deductions, half units): Goodness 1.85u $2.80 -> $2.21 won +2.23u; Ladhar
  1.66u, Tempt The Gods 0.51u lost. 4.02u, +0.06u.
- Lay book (s6x, $200 a lay): races 1-5, 5 lays, 0 winners, +4.60u (+$920; +$230 at Friday's $50). Races 6-8 NOT SETTLED:
  Form King has no Betfair SP for them (written as 0.0, still missing after a re-pull at 9:45am Thu). settle_lays.py and
  settle_backs.py now treat a missing BSP as void, not as "outside the band", which is how a 0.0 would have read.
- Back book: no BSP favourite inside its range in races 1-5; races 6-8 not settled (no BSP).
- Rule tracker (research/form_gbm/track_rules.py, 48 meetings): +269.02u since 9 Oct; Ballarat races 1-5 +7.28u (10 bets,
  all lost by the horse, one $4-$7 firm back lost); since 10 Nov 31 bets -5.44u.

## Friday 13 Nov Geelong: opened 8:05-8:08am Fri, the sheet never sent (BetMatic down Wed; only checks since)
- At Form King's open the sheet would have filled two horses: Baccano R4 2.61u at $4.90 (ours $3.81) and Smarticon R9
  0.63u at $19 (ours $12.92), 3.24u. Everything else opened under its minimum.
- Missed open: the same two bets sent as 2026-11-13-geelong-late.csv, any price, best bookie price now (when=best),
  inside 2 hours of the open. Nothing on the Geelong 9am list.
- 9:26am send (fk-betmatic when=best, run 43319913632) REFUSED: no bot machine connected, no session running; a check at
  9:27am read the same (every session bot_running false, last states from 31 Oct to 2 Nov). Left with the founder to place
  by hand inside the window: Baccano R4 #1 $130, Smarticon R9 #4 $32.
- Friday Mercer card (founder, 9:45am): Melek R4 10.43u at $2.60, the open's 5.43u plus 5u for the 9am fill (9am list
  $2.70 or better); Geelong Baccano 2.61u $5 and Smarticon 0.63u $21 at the 8:32am best prices; Helizangel SCR.
- Friday no-Mercer card: Melek R4 10.43u at $2.80, the blend of 5.43u at $2.90 (open) and 5u at $2.70 (9am):
  5.43 x 2.90 + 5 x 2.70 = 29.25 returned on 10.43u, $2.804.

## Thursday 12 Nov Seymour settled (Form King results, Fri 10:05am)
- Open book (no-Mercer card, the open, full units): Tale Of Genji R3 2.54u $5.50 WON (SP $5.50, BSP $6.20) +11.43u;
  Zverev R1 0.96u $13.50 2nd, Princess Of Sol R1 0.88u $13.50 4th, Soju R7 0.88u $26 4th, Ulfberht R8 1.38u $13 13th
  -4.10u. +7.33u on 6.64u (+$367 at $50), ROI +110%. No TAB deductions reported.
- Mercer card (current prices, full units): Tale Of Genji 2.54u $3.80 won +7.11u, the rest -4.10u: +3.01u on 6.64u.
- Lay book (s6l, $200 a lay): 7 lays, 2 winners (Commands Success R7 BSP $36.57 -35.57u, Deliberate Ploy R8 BSP $10.04
  -9.04u), -40.01u (-$8,002 at $200); void 1 (Kiss My Rock R6). Lays live at $50 from Fri 13 Nov.
- Back book: no BSP favourite in range. 9am list: none (started Fri 13 Nov); no 9am-tracker rows at Seymour.
- Rule tracker (49 meetings): Lay $25-$40 drifted 2x +125.40u since 9 Oct; current lay $15-$40 rule -22.68u since 9 Oct,
  -20.85u since 10 Nov (17 lays, 1 winner).

## Sunday 15 Nov Donald and Moe re-priced with riders (Fri 1:20pm, tag r11131319; Donald 5 and Moe 3 riders still to come)
- Moe opened Fri 10:12-10:18am (R8 Thu 12:17pm), before the re-price, so its sheet of record stays the Wednesday sheet
  (restored after --replace emptied it). At the open it would have filled: Fridge Monster R4 4.24u $14 (ours $5.35), Yes
  Yoshi R5 6.35u $2.60 ($1.91), Stole Him R9 0.73u $18.50 ($11.35): 11.32u. Not placed: BetMatic's bot has been off since
  2 Nov, and by the re-price the two-hour missed-open window had closed.
- Donald: R6 opened Thu 2:30pm with no fill; its Wednesday rows stay on the sheet, the other seven races take the new
  prices (37 horses, up to 113.68u). Send refused: bot not connected.

## Fri 13 Nov evening: $37.50 a unit; Dunkeld sent on the founder's word; every send waits for the bot
- Units $37.50 (founder: "Can you do units at 37.50"): the send default, the order builder and the pricer; the Dunkeld,
  Donald, Wangaratta and Kyneton sheets re-dollared.
- Dunkeld Sat 14 Nov is PAPER ONLY by the pricer's rule (8 races at the venue, 0 since the 3 Jun holdout); founder: "Yep
  send". Re-priced with riders at 10:34pm (tag r11132234; 3 runners still without a rider): 37 horses, 142.43u
  ($5,344) if every order fired. R7 opened Thu 3:55pm (its seven missed opens were all under their minimum).
- The $50 sends of Donald (1:23pm), Wangaratta and Kyneton were refused: no bot machine connected. 10:29pm and 10:39pm
  checks: still none. A watcher in the session checks every 10 minutes and sends Dunkeld, Donald, Wangaratta and Kyneton at
  $37.50 (Market Open) the moment a machine connects. Opened races (Dunkeld R7, Donald R6) stay on the sheets and do not fire.

## Friday 13 Nov Geelong and Pakenham settled (Form King results, Sat 4:05am; the 3am results job had not run, so both meetings re-pulled by date)
- No-Mercer card (the open, full units): Mongolian Hero Pakenham R2 5.04u $3.05 WON (SP $1.30, BSP $1.57) +10.33u;
  Baccano Geelong R4 2.61u $4.90 4th, Smarticon Geelong R9 0.63u $19 7th, Melek Pakenham R4 10.43u at the blended $2.80
  7th -13.67u; Helizangel R1 scratched. -3.34u on 18.71u (-$167 at $50), ROI -18%. No TAB deductions reported.
- Mercer card (current prices): Mongolian Hero 5.04u $2.20 won +6.05u, Baccano $5, Smarticon $21, Melek 10.43u $2.60 lost
  -13.67u: -7.62u (-$381 at $50).
- 9am list: Melek R4 to win $1,000 a bookie at $2.70 (stake $588), 7th: -$588 a bookie.
- Ours/1.6 lay rule (tracked, no lays placed): 6 lays, 1 winner (Zapatch Pakenham R1, BSP $26, ours $45.38) -20.40u
  (-$1,020 at $50); since 9 Oct 48 lays, 1 winner, +18.24u; from 13 Nov -20.40u.
- Back book ($500 a unit): Jarbardar Pakenham R5 BSP $4.69 9th -1.00u (-$500); Geelong none.
- 9am tracker (27 meetings): blend 9am 6 bets, 3 won, +8.7u. None of Friday's bets went through BetMatic (no bot machine).

## Sat 14 Nov 5am: back to $50 a unit
- Founder: "$50 units". The send default, the order builder and the pricer are $50 again; the Dunkeld, Donald, Wangaratta
  and Kyneton sheets re-dollared: Dunkeld 142.43u $7,123, Donald 135.80u $6,790, Wangaratta 106.79u $5,341, Kyneton
  128.75u $6,441 if every order fired. The overnight check-ins (every 30 minutes) send all four at $50, Market Open, when a
  bot machine connects; checks to 4:49am found none.

## Sat 14 Nov 7am: Dunkeld at $25 a unit, nowhere else
- Founder: "$25 units for just dunkeld, no where else". The Dunkeld sheet re-dollared: 142.43u $3,563 if every order
  fired; it is sent with unit 25. Donald, Wangaratta, Kyneton and every other meeting stay $50 (the send default, the
  order builder and the pricer are unchanged at $50). Checks to 6:57am: no bot machine connected, nothing sent.

## Sat 14 Nov Dunkeld in BetMatic ($25 a unit; Donald, Wangaratta and Kyneton removed by the founder)
- Sent 8:08am (run 43508014313, when=open): 99 orders, $3,563 if all fired. R7 and R8 were already open, so their orders
  went straight to TAB at 8:11-8:15am and every one was under its minimum (e.g. Rippa Buddy R8 $8.50 against $17.64; Stay
  Humble R7 $4.40 against $4.94; Foujita San scratched). R1-R6 opened about 8:25am; Boridi R1 scratched (5 orders failed).
- BetMatic holds 2 bets for the day: Cracked It R2 $126 at TAB $3.30 (min $2.61; status read), and very likely its second
  order $29 (min $3.26). Everything else opened under its minimum; nothing is still waiting.
- The page's "bets at the open" box counts Form King's opening price, not TAB's: it showed Rippa Buddy at $18 (BetRight
  and UpYaGo only); TAB never offered that.
- The 11:15 pricing routine is on a send hold (founder: "$25 units for just dunkeld, no where else").
