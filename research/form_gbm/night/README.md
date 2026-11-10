# The night of 10-11 Nov 2026: every check, closer to BSP, betting strategies

Founder, Tue 10 Nov evening: "Do every check of our model ANYTHING you can think of, research to get our model closer to
bsp and any betting strategies. You have all night". Everything here is DB-free and credit-free: the 9 Nov dataset
(5,178 Victorian races from 1 Jul 2025), the committed live price files, and the frozen live v10 models.

How results are judged (nl.py): two walk-forward folds, so a change has to hold on two separate sets of unseen races
(A: trained before 3 Jun 2026, scored 3 Jun - 9 Nov; B: trained before 1 Jan 2026, scored 1 Jan - 2 Jun, never used as
a test set before), three seeds, and the same model on three seed sets for the noise floor. Betting rules are judged on
four separate periods (and six on the 16-month cross-check); a rule counts only if it points the same way in all.

## Part 1. Checks of the live model

### 1.1 No leaks (leak_scan.py)
Each of the 809 inputs tested for win information beyond BSP (score test of a conditional logit with BSP as the null,
5,136 races). Largest |z| 2.70; about 3.2 is expected by chance with 809 inputs. Nothing over 3.2, nothing that holds in
both halves. No input knows the result, and BSP has already absorbed everything in the form data.

### 1.2 The live price against the backtest: where the gap came from (replay_stale.py, score_replay.py, diag_inputs.py)
The committed live files, 15 Oct - 9 Nov (275 races where every runner that ran is in the file): our price KL to BSP
0.1016, blended with the open 0.0958, the open 0.1565; winner log loss 1.938 / 1.926 / 1.966, BSP 1.806. The backtest of
the same models on the same races, on the rebuilt inputs: 0.0922. So live ran about 10% further from BSP than the
backtest says. Same trees, same history, live file against the rebuilt inputs, by what changed after pricing:

| races | n | live KL | rebuilt-input KL | log loss live / rebuilt |
|---|---|---|---|---|
| a runner was scratched after the file was made | 51 | 0.1158 | 0.0898 | 1.907 / 1.834 |
| a rider was missing or changed | 71 | 0.1318 | 0.1036 | 2.073 / 2.021 |
| clean: same field, same riders | 153 | 0.0941 | 0.0949 | 1.891 / 1.890 |

- CLEAN RACES MATCH. Form King is not revising its figures after the race in a way that flatters the backtest; the
  pre-race inputs and the rebuilt ones price the same when the field and the riders are the same.
- RIDERS: 172 of the 205 runners whose jockey differed had NO rider in the final live file. October's files were priced
  with 3 to 22 runners a meeting undeclared (Cranbourne 16 Oct 22 of 82, Flemington 31 Oct 22 of 138). From the 1 Nov
  rider fix it is 1 or 2 a meeting, and the gap is closed: 1-9 Nov, live 0.1004 against rebuilt 0.1002.
- LATE SCRATCHINGS (after the 9:30 re-price): 19% of races. Re-spreading the price over the runners left is not enough;
  a re-price on the final field is 12-28% closer to BSP on those races. This cannot help a bet struck at the open, but it
  matters to anything decided at the jump (the Betfair books): see 3.5.

### 1.3 The history the live pricer reads is frozen at 14 Oct (replay_stale.py)
price_day3 and apply_stage2f read ds/model_ds.npz and p_oof_blend9.npy from the model work folder. Those are the files
v10 went live with on 15 Oct; nothing refreshes them. So a live price today is built on trainer / jockey / sire records
that stop at 14 Oct, and the second stage's "what did the market think of this horse last time" comes from the run
BEFORE the horse's last one for any horse that has run since (94 of Seymour's 100 runners had a run or a trial in that
window). Every backtest computes these from every earlier race. Replay with the frozen models (no-network blend):

| stage 2, 15 Oct - 9 Nov | KL to BSP | log loss |
|---|---|---|
| history to 14 Oct (what live does) | 0.0924 | 1.8981 |
| history to the day before each race | 0.0908 | 1.8934 |

Paired by race: +0.0016 (SE 0.0005, t 3.1). By age of the history: weeks 1-2 no difference (t 0.6); weeks 3-4 the fresh
history is 3.0% closer (0.0968 -> 0.0939, t 3.1). It is getting worse every day. The fix costs nothing: copy the nightly
retrain's history files (models branch, challenger/) into the pricing folder each morning; the live MODELS do not change.
pipeline/refresh_history.sh does it, keeps the old files, and checks the columns line up.

### 1.4 Live scorecard (live_scorecard.py)
By week the live price holds its place: our price 0.109 / 0.090 / 0.101 / 0.103, the open 0.155 / 0.164 / 0.160 / 0.146.
Calibration by price band is fine on 2,834 runners (A/E 0.84 to 1.17, no trend). Where we are 1.5x+ SHORTER than BSP
(791 runners) we expected 62 winners, BSP 31, and 24 won: BSP is right, and those horses do even worse than BSP says.
Where we are 1.5x+ LONGER (441) BSP expected 61 and 68 won. Runners the live blended price rated value at the open: 354,
59 won, flat +54% at Form King's open, 71% beat BSP, median open/BSP 1.34 (the backtest: 73%, 1.33). The open edge is
live and the size the backtest says.

### 1.5 Names line up (name_match.out.txt)
Seymour's pre-race export against the history: every trainer, sire, dam sire and stable town matches; one jockey of 95
is new to us; 91 of 100 raced runners are in the history under the same horse id. No silent blanks.

### 1.6 The blend with the open (blend_live.py)
Best weights on the live weeks 0.76 ours / 0.28 open against the live 0.82 / 0.22: KL 0.0949 against 0.0953, and worse
when fitted on one half and scored on the other (0.0960). Leave it.

### 1.7 The race-morning re-price against the first price (first_vs_last.py)
13 meetings with both files committed 6+ hours apart (median 68 hours), 67 races: first price KL to BSP 0.1037, the
re-price 0.0930 (paired +0.0108 a race, SE 0.0042), winner log loss 1.800 -> 1.763. A third of runners move 10%+.
The 9:30 re-price (final field, riders in) is worth about 10% of the distance to BSP; anything decided after the open
should use it, and does.

## Part 3. Betting strategies (strat1.py, strat2.py, strat3.py, strat_ceiling.py, drift_live.py)
Two prices, so a rule has to hold on both: the stage-1 trees walk-forward (1 Jan - 9 Nov 2026, 3,194 races, four
periods), and the 10 Nov challenger's out-of-fold three-model blend (1 Jul 2025 - 9 Nov 2026, 5,178 races, six periods;
cross-fitted, so a second opinion). Live BetMatic rules at Form King's open, 16c deduction.

### 3.1 THE 3x CEILING COSTS A QUARTER TO A THIRD OF THE PROFIT
The order sheet stops at 3x our price (max_odds, added 14 Oct after three losing fills in the first forward test, when
the files were still priced before final fields). With the full live sheet (first starters out, 1.15 under $4, the 2 Nov
doubling from 2.2x):

| ceiling | walk-forward trees, 11 months | worst drawdown | three-model blend, 16 months | worst drawdown |
|---|---|---|---|---|
| 3x (live) | +3,139u on 3,316 bets (+41%) | 68u | +4,517u on 5,346 bets (+37%) | 103u |
| 4x | +3,770u | 81u | +5,423u | 93u |
| 6x | +4,283u on 3,484 bets (+52%) | 74u | +6,479u on 5,613 bets (+50%) | 93u |
| none | +4,232u | 76u | +6,737u | 103u |

6x beats 3x in ALL FOUR walk-forward periods (+1,367 v +1,133, +784 v +571, +1,621 v +1,107, +512 v +328) and ALL SIX
cross-fit periods. The bets it adds (not first starters, open 3x-6x ours): 168 in 11 months, about 15 a month, median
open $26, 26 winners where BSP's chances said 21.8; BSP lands at a third of the open. Above 6x: 17 bets, none won
(walk-forward) and 3 of 6 periods (blend): stop at 6x. On the committed LIVE files, 15 Oct - 9 Nov: 17 such runners, 2 won
(Lim's Ida $26, Spinhof $23), flat +24.5u. The whole book has the same shape: return on stakes by open / our price is
+7% at 1.2-1.4x, +25% at 1.4-1.7x, +50% at 1.7-2.2x, +75% at 2.2-3x, +180% at 3-6x; the live files show it too
(+6%, +13%, +81%, +64%, +219%). Caveats: Form King's open is an average and a $26 open may not take a full stake; these
are the bets that get an account noticed; the two prices are stage 1, not the live stage-2 price.
FOUNDER'S CALL: lift max_odds from 3x to 6x our price (one constant in betmatic_orders.py).

### 3.2 The edge: leave it at 1.20
Walk-forward: total profit is flat from 1.10 to 1.30 (+2,611u to +2,739u; live 1.20 +2,652u), ROI rises with the edge.
Three-model blend: 1.20 is the profit maximum (+3,893u; 1.25 +3,786u, 1.30 +3,544u). The live sheet's 1.15 under $4
is +88u better than a flat 1.20 walk-forward. No change. Price range $1.60-$15, three steps and the 10u cap: all at or
within noise of the best in their grids.

### 3.3 Segments of the live rule's bets (walk-forward, four periods, against random draws from the same period)
Of 78 segments luck would flag about 1.3. Flagged WEAK in all four: open 1.2-1.4x our price (621 bets, +7%).
STRONG in all four: horses aged 5+ (+49%), a drop in class of 25%+ by prize money (+41%), "beat its price last start"
(349 bets, +63%; the same type was the only runner type to survive the BSP test earlier the same day). Near misses:
jockey's only ride at the meeting (+75%, top quarter in three periods), metro (+17% against +40% elsewhere, weak in
three). No rule proposed from these: the stake already follows the overlay, and the ceiling is the structural finding.

### 3.4 The firm/drift forecast on races it never saw (drift_live.py)
Model trained on races to 9 Oct; the committed live prices 15 Oct - 9 Nov; 286 value bets at the open:

| forecast third | bets | won | flat at the open | BSP/open | firmed |
|---|---|---|---|---|---|
| to drift | 117 | 18 | +3% | 0.74 | 72% |
| middle | 97 | 19 | +59% | 0.79 | 69% |
| to firm | 72 | 12 | +26% | 0.64 | 83% |

The drift third is the weak one out of sample, as in the backtest; the firm third firms most but does not out-earn the
middle at flat stakes. x2 firm / x0.5 drift on the live stakes: +116.9u against +80.0u on the same turnover. The
forecast itself is weak out of sample (correlation with the actual move 0.08, 0.27 in its backtest). Reading: the half
stake on the forecast-to-drift third is supported; the doubling of the firm third is not proven on four weeks.
FOUNDER'S CALL (open since 3 Nov): put --drift back for the drift third, or retire it.

### 3.5 The lay rules and late scratchings (lay_late.py)
Live files, 15 Oct - 9 Nov, lay $15-$40 at 1.5x ours: races WITH a late scratching 46 lays, 3 won (BSP expected 2.0),
-42.9u; races without 211 lays, 6 won (8.9 expected), +73.3u. Re-pricing those races on the final field does not rescue
them (45 lays, 4 won, -67.5u), so it is not our stale price. Four winners against two expected is not a finding on its
own (about one chance in eight). Worth a column in the rule tracker before the Betfair book goes live, not a rule yet.

### 1.8 What the refresh does to a meeting already priced (seymour_fresh_history.out.txt)
Seymour Thu 12 Nov re-priced in a copy of the model folder after refresh_history.sh (the live folder untouched): our
price moves a median 5.3%, 24 of 94 runners by more than 10% (Mahmudah $7.08 -> $5.80, Cushioned $4.96 -> $5.68,
Zverev $8.93 -> $10.24, Who'llstoplorraine $47.52 -> $28.28). Trees and CatBoost move 2%; the network third, which is
re-trained on the history every time a day is priced, moves 7.5%; the second stage (the market's memory of each horse)
does the rest. FOUNDER'S CALL: run refresh_history.sh on the live folder each morning before pricing (one line in the
9:30 and 12:17 routines), from the next meeting priced; bets and tips already out stay as they are.

### 3.6 The opening book, scratchings and the deduction (open_book_check.py, open_book_months.py, deduction_model.py)
In 22% of races the opening prices of the runners that RAN add up to under 100% (median 1.20, 5th percentile 0.75):
every month since Jul 2025 (13-32%), live-pulled races included. That is not a broken record. It is scratchings after
the market opened: the opens were real, the horses that came out took their share of the book with them, and TAB's
deduction follows the shortfall. TAB's actual deductions (50 races from the founder's reports with every open):
opening book under 0.9: 28.7c average; 0.9-1.0: 18.6c; 1.0-1.1: 11.6c; 1.1-1.2: 5.9c; 1.2+: 3.4c.
Fit: DEDUCTION = 0.62 x max(0, 1.24 - opening book), correlation with the actual 0.87 (mean 12.4c fitted, 13.1c actual).
- The backtest's bets lean into those races (2.3 bets a race where the book is under 0.9, 0.55 where it is 1.3+), so a
  flat 16c could have been far too little. It is not: settled with the fitted deduction race by race the live sheet
  makes +3,110u against +3,139u at the flat 16c (walk-forward), +4,285u against +4,517u (blend). The stake-weighted
  deduction on our winners is 16-17c. THE FLAT 16c WAS RIGHT.
- The 6x ceiling under the fitted deduction: +4,136u against +3,110u (walk-forward, all four periods), +5,904u against
  +4,285u (blend, all six). At 1.5x the fitted deduction: +3,070u against +2,254u. Two thirds of the extra bets sit in
  races that lost a fifth of their market, and they still pay after the deduction those races carry. In races with an
  ordinary opening book only (110-135%): 42 extra bets, 7 won, +378u, all four periods.
- Use the fit for settling paper bets when TAB's figure has not been reported: it is closer than the 0.95 / price
  schedule (which ran 2.5x too high at Caulfield 14 Oct) and needs only the prices we already store.

### 3.7 What a month looks like (risk_months.py)
The live sheet's walk-forward bets re-drawn by whole race days into 10,000 thirty-day months, $50 a unit:
at the backtest's volume the median month is +297u ($14.8k), one month in twenty is under +101u, 0.5% lose; at 70% of
the volume (what live has fired) +207u ($10.3k), one in twenty under +41u, 1.8% lose, the worst run inside a month is
typically 50u ($2.5k). With the 6x ceiling at 70% volume: +281u ($14.0k).

### 3.8 More cuts, with the deduction fitted by race (strat4.py)
- Our bets in the same race: the only bet +46% on stakes (1,247 bets); one of two +33%; one of three +50%; ONE OF FOUR
  OR MORE +12% (265 bets, flat -1%; +52%, -4%, +7%, -15% by period). When the sheet wants four horses in a race there is
  little in it, but 265 bets in 11 months and one good period: noted, no rule.
- Race number on the card: nothing (races 1-2 +37%, 3-4 +49%, 5-6 +31%, 7-8 +45%).
- By how much of the market was scratched after the open (the opening book): under 90% +25% on stakes and fading
  (+72%, +18%, +12%, -3%); 90-100% +58%; 110-125% +51%; 125%+ +56%. The heavily scratched races are the weak ones once
  the deduction is charged properly, and nothing known at the open says which races they will be.

### 1.9 Blend weights by race type (blend_segments.py)
Walk-forward trees with the open, 3,146 races, weights fitted per group on one half-year and scored on the other: one
pair for every race KL 0.0866; by first starters in the race 0.0862; metro / not 0.0864; field size 0.0864; distance
0.0867; a 2yo in the race 0.0865. The fitted weights do lean to the open where we are weakest (2+ first starters
0.66 / 0.48, metro 0.62 / 0.52, as the metro fix already does), but the whole-market gain is under half a percent.
Leave the blend as it is.

### 3.9 Audit of the order sheet's blocks (strat5.py, strat5_blend.out.txt)
Every bet the edge rule would strike with the blocks off (first starters still out), deduction fitted by race; the
bets each block STOPS, at the open: walk-forward trees (11 months, four periods) / cross-fitted blend (16 months, six).

| block | walk-forward: bets, profit, ROI, periods | blend: bets, profit, ROI, periods | flat at BSP | verdict |
|---|---|---|---|---|
| resuming 60+ days, 200m+ short of last start | 247, -161u, -27%, lost in 4 of 4 | 370, -22u, -3%, lost in 3 of 6 | -66% / -43% | KEEP |
| resuming off a bottom-half trial | 68, -12u, -9% | 77, -37u, -25%, lost in 5 of 6 | -31% / -44% | keep |
| second-up after a good first-up, open over $15 | 44, -32u, -61% | 69, -11u, -14%, lost in 4 of 6 | -50% / -44% | KEEP the $15 cap ($8-$15: +49% / +61%, the 1 Nov change was right) |
| BOUNCE: last start a new peak by 3+ | 307, +177u, +22% (+55%, +43%, +2%, -7%) | 457, +299u, +24%, won in 4 of 6 | -32% / -19% | QUESTIONABLE |
| metro, open $12+ (plain rule, without the metro lean) | 274, +100u, +33%, won in 2 of 4 | 424, +128u, +26%, won in 5 of 6 | -4% / -19% | inconclusive |

The bounce block was built on BSP returns (-40% at BSP in October's test, still -19% to -32% here) and the bets it stops
do lose at BSP; but we strike them at the open, where they made +22% to +24% on 16 months, about +180u to +300u given
up. All of the walk-forward gain is in January to May; from June the stopped bets broke even, which is what the 20 Oct
audit saw (0% at the open on the June holdout). FOUNDER'S CALL: keep it (nothing lost since June) or drop it (16 months
say the bets pay at the open). The first-up-short-of-trip block and the $15 second-up cap both hold on the longer sample.

### 3.10 The sheet as it is against the two changes (strat6.py)
Every live rule this backtest can apply (first starters out, both first-up blocks, the bounce block, the second-up $15
cap, the metro $12 cap, 1.15 under $4, three steps, the 2.2x doubling), deduction fitted by race:

| sheet | walk-forward trees, 11 months | every period? | three-model blend, 16 months | every period? | worst drawdown |
|---|---|---|---|---|---|
| A today: 3x ceiling, bounce block | +2,936u on 2,442 bets (+49%) | | +3,818u on 4,034 bets (+40%) | | 65u / 104u |
| B ceiling 6x | +3,724u (+27%) | 4 of 4 better | +5,166u (+35%) | 6 of 6 better | 84u / 85u |
| C ceiling 6x, no bounce block | +4,024u (+37%) | 3 of 4 better than B | +5,664u (+48%) | 5 of 6 better than B | 89u / 98u |

About 12 more bets a month for B, 36 for C.
