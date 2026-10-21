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
| | | | | | | | | |

Placed so far (Mon 19 Oct, for Wednesday): Geelong R5 Murshidi (#7), $126 (5.04u) at $11, our price $3.81, both order steps filled at TAB's open 11:45am Monday. Tweeted by the founder the same morning as 5u at $11 (locked). Card posted Monday afternoon records it at $6.50 (5u), founder's call; the real-money line stays $126 at $11. Runs: no deduction in R5 (founder, Wed 21 Oct).
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
| 2026-10-21 Geelong | R2 | Superliv | $15.00 | $18.00 | $12.14 | 0.00u | 1.00u | | |
| 2026-10-21 Geelong | R6 | Stay Humble | $5.50 | $5.50 | $3.96 | 0.00u | 3.11u | | |
| 2026-10-21 Geelong | R7 | Litzdeel (Geelong Cup: internationals in the field, flagged) | $6.00 | $6.00 | $4.88 | 0.00u | 1.71u | | |
| 2026-10-21 Geelong | R8 | Keep Your Cool | $7.50 | $7.00 | $5.81 | 0.00u | 1.27u | | |

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

## Copied tips (founder's call, separate from the model's results)

| Date | Race | Horse | Tipster (price, units) | Order | Placed | Result |
|---|---|---|---|---|---|---|
| 2026-10-21 | Eagle Farm R4 (4:18pm) | No. 5 Wootten Hyde (tweeted as "Wooden Hyde") | Anthony Don ($2.50, 6u) | $300 win, min $2.30, High Odds First across every running session | Triggered 10:21am, $0 accepted: TAB balance $0.29 | |

The order path works: BetMatic took a High Odds First bet with the bookmaker list left open (every bookmaker where we have a running session) and fired it at once. Nothing was matched because the only running session (TAB) had no money in it.

