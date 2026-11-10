# The night of 10-11 Nov 2026: every check, closer to BSP, betting strategies

Founder, Tue 10 Nov evening: "Do every check of our model ANYTHING you can think of, research to get our model closer to
bsp and any betting strategies. You have all night". Everything here is DB-free and credit-free: the 9 Nov dataset
(5,178 Victorian races from 1 Jul 2025), the committed live price files, and the frozen live v10 models.

How results are judged (nl.py): two walk-forward folds, so a change has to hold on two separate sets of unseen races
(A: trained before 3 Jun 2026, scored 3 Jun - 9 Nov; B: trained before 1 Jan 2026, scored 1 Jan - 2 Jun, never used as
a test set before), three seeds, and the same model on three seed sets for the noise floor. Betting rules are judged on
four separate periods (and six on the 16-month cross-check); a rule counts only if it points the same way in all.

## What the night found, in order of money
Nothing live was changed. Every item marked CALL is the founder's decision.
1. THE OPENS WE MISS (Part 4). 21% of races in the last four weeks opened on TAB before our order sheet existed (67 of
   317; Tuesday meetings 23 of 45), before counting the wait for "send" and the days the bot was off. TAB opens Tuesday
   meetings on Saturday morning and Saturday metro on Wednesday from 11:50am; the 12:17pm run is too late for both.
   Roughly 20-25u a month from scheduling alone. CALL: earlier pricing runs (4.3).
2. THE 3x CEILING (3.1, 3.6, 3.10, 3.14). Lifting max_odds to 6x our price adds a quarter to a third to the backtest
   profit on both prices and in every period; in races whose opening market stayed intact it is +25% from about three
   extra bets a month. Above 6x there is nothing. CALL: one constant in betmatic_orders.py.
3. THE BETFAIR LAY RULES DO NOT SURVIVE UNTOUCHED MONTHS (3.12, 3.13). Seven of the ten tracked rules fail on Jul 2025 -
   2 Jun 2026, both current lay rules among them; the lay edge exists only in the months the rules were chosen on. CALL
   before Fri 13 Nov: keep the lays on paper.
4. THE LIVE PRICE RAN 10% FURTHER FROM BSP THAN THE BACKTEST, AND WHY (1.2, 1.10). Clean races match the backtest. The
   gap was riders not declared when the file was priced (fixed 1 Nov, gap closed since) and late scratchings. In money
   the same four weeks made +28% on stakes live against +47% on the backtest's inputs: plan live at about 60% of any
   backtest figure.
5. THE HISTORY THE LIVE PRICER READS IS FROZEN AT 14 OCT (1.3, 1.8). It costs 3% of the distance to BSP by weeks 3-4 and
   grows daily. CALL: run pipeline/refresh_history.sh each morning (the live models do not change).
6. A PRICE MADE BEFORE RIDERS ARE DECLARED (4.4, 2.5). Blanking riders on the live model costs 29% of the distance to
   BSP and a third of the profit; a model trained without riders costs 12%. Earlier runs (item 1) should use one.
7. THE DRIFT HALF-STAKE (3.4) holds on four weeks it never saw (+117u against +80u on 286 bets). CALL: put --drift back
   for the drift third, or retire it.
8. THE BOUNCE BLOCK (3.9) stops bets that made +22% to +24% at the open over 16 months, but nothing since June. CALL.
9. TRAINING IS AT ITS CEILING (Part 2). 49 retrains, 20 network seeds, 3 CatBoost seeds, mixed recipes: the best is half
   a percent on the trees alone and nothing inside the full blend (the live recipe 0.0891 / 0.0942; everything doubled
   0.0892 / 0.0941). The second stage is worth 6-7% and is at its ceiling too (2.10). The blend and its weights are
   right. No leaks. The only lever left on the price is more history (each doubling 4-6%).
10. LEFT ALONE, CHECKED: the 1.20 edge, the $1.60-$15 range, the three steps, the 10u cap, the flat 16c deduction, the
    blend with the open, the first-up and second-up blocks, the stake's calibration (3.2, 3.6, 3.9, 3.11, 1.6, 1.9).

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

## Part 4. Operations: the opens we miss (scripts/open_times.py, open_times_report.py, sheet_vs_open.py)
The open is where the money is (3.x), and a race that opens before our orders are in is gone. Two things are separate:
the bot being off (known), and the sheet not existing yet when TAB opens (measured here for the first time).

### 4.1 When TAB opens, by race day (67 meetings with timed opening markets, 1 Sep - 10 Nov)
| race day | the market opens | examples |
|---|---|---|
| Monday | SATURDAY 9:15-10:45am | Echuca 9:13, Wangaratta 9:50, Ballarat 9:58, Hamilton 10:14 |
| Tuesday | SATURDAY 9:45am-12:00 | Kyneton 9:46, Swan Hill 9:56, Mildura 10:17, Moe 10:22, Mornington 11:02, Kilmore 11:55 |
| Wednesday | Monday: metro from 11:20-12:45, provincial 2:45-4:30pm | Geelong 11:20, Sandown 11:44, Caulfield 12:42; Bendigo 2:44pm, Kyneton 4:28pm |
| Thursday | Tuesday 3:40-4:10pm | Warrnambool 3:42 / 3:50 / 4:00, Seymour 3:58, Mornington 4:07 |
| Friday | Wednesday 3:00-3:45pm (one at 11:14am); extra meetings on the day 8:40-9:25am | Cranbourne 3:37 / 2:56 / 3:41 |
| Saturday metro | WEDNESDAY from 11:51am to 12:33pm, then race by race until about 3pm | Caulfield 11:51 / 11:53, Flemington 11:55 / 12:00 / 12:01 / 12:33 |
| Saturday country | Friday 10:20-11:30am, or Saturday 8:00am | Bendigo, Yarra Valley 10:20; Wodonga 11:26; Avoca, St Arnaud, Geelong 8:00 |
| Sunday | Thursday 2:00-3:40pm or Friday 9:40-10:45am | Seymour, Sale 2:01; Horsham 3:38; Mornington Fri 9:42; Ararat Fri 10:41 |
58% of meetings opened before 12:17pm on the day they opened; none after 5pm.

### 4.2 Was the sheet there? (41 live meetings, 14 Oct - 10 Nov)
First commit of each meeting's order sheet against each race's opening time: 67 of 317 races (21%) OPENED BEFORE THE
SHEET EXISTED, in 11 of 41 meetings, 7 of them missed whole. By race day: Tuesday 23 of 45 races, Monday 9 of 33,
Wednesday 9 of 35, Thursday 8 of 33, Sunday 9 of 32, Saturday 9 of 97, Friday 0 of 42.
- Tuesday meetings: Kyneton 20 Oct, Swan Hill 27 Oct and Mornington 10 Nov all opened Saturday 9:46-11:14am; their
  sheets were committed Saturday 12:40pm or on Sunday.
- Saturday metro: Flemington 7 Nov opened Wednesday 12:33pm onward; the sheet was committed at 1:51pm, after 7 of the 9
  races had opened. Flemington 31 Oct: 2 of 9. The 12:17pm run takes 30-90 minutes to produce a sheet, and then waits for
  "send".
- Sunday Mornington 1 Nov opened Friday 9:42am; the sheet came Friday 11:41am.
This is before counting the wait for the founder's "send" and the days the bot was off. At the backtest's 0.7 bets a race
and about +0.5u a bet, 67 races is roughly 20-25u a month ($1,000-$1,250 at $50) from scheduling alone.

### 4.3 What would fix it (founder's calls)
1. A SATURDAY 9:00am pricing run, repeated at 10:00 and 11:00 until Tuesday's fields are in (Monday's come out Friday and
   are already caught). Tuesday meetings open 30-60 minutes after their fields: pricing has to start when the fields land,
   not at 12:17.
2. A WEDNESDAY 11:00am run for the Saturday metro meeting and a MONDAY 11:00am run for the Wednesday metro meeting: both
   start opening before noon. A FRIDAY 9:00am check for Sunday meetings not priced on Thursday.
3. Price before riders are declared when the open will not wait: the median-rider fill (1 Nov) costs far less than the
   open. Re-price when riders land if the race has not opened.
4. The "send" gate: for a meeting that opens within the hour, a standing approval to place the sheet as priced (dry run
   first), with the list sent to the founder at the same time. Without it the early run only produces a sheet in time.
5. Keep TAB funded and the bot running through Saturday morning and Wednesday midday: those are the two windows where
   most of the week's races open.

### 4.4 The price before riders are declared (replay_noriders.py)
The catch in an earlier pricing run: 15 Oct - 9 Nov, frozen live models, the same races with NO rider on any runner
(name blank, every rider input at the median rider, as the 1 Nov rider fix does): stage 2 KL to BSP 0.1189 against
0.0924 with riders in, winner log loss 1.936 against 1.898; three quarters of runners move by more than 10%. Still well
ahead of the open (0.154), but a fifth of the way back to it. The live model leans on the rider a great deal, and a
median rider is not what it was trained to see. queue2's no_rider_model arm trains the same trees with no rider input at
all, which is the price an early run should use for runners with no rider yet (result in Part 2).
In money: the live edge rule at the open on those four weeks, 306 bets +319.4u (+47%, 73% beat BSP) priced with riders;
312 bets +211.1u (+37%, 67% beat BSP) priced with NO riders on the live model. A price made before riders keeps about
two thirds of the profit; a missed open keeps none. So: price as soon as the fields land, re-price when riders do.

### 1.10 The same four weeks in money: live files against the backtest's inputs (replay_bets.out.txt)
The live edge rule at Form King's open, 15 Oct - 9 Nov, first starters out, 16c deduction, the same races:
committed live files 293 bets, 51 won, +180.9u (+28%); replay on the rebuilt inputs, history to 14 Oct, 298 bets, 60
won, +313.1u (+47%); the same on fresh history +309.1u (+47%). Both halves alike (15-28 Oct +116u against +184u;
29 Oct - 9 Nov +64u against +129u).
- THE BACKTEST KNOWS THE FINAL FIELD AND THE RIDERS; A PRICE MADE FOR THE OPEN KNOWS NEITHER. On these weeks that is
  the difference between +47% and +28% on stakes. Plan live at about 60% of any backtest profit figure in this file
  (the 14 Oct study said 60-80% from volume alone; this is the same answer from the price side).
- Fresh history is worth 2-3% of the distance to BSP but nothing measurable in four weeks of bets (+309u against +313u).
  It is a correctness fix, not a profit lever.
- What this does to the ceiling result (3.1): a race that loses runners after the open makes every survivor's opening
  price look long against a price computed on the final field, so some of the backtest's "3x-6x" opens would have been
  2x-3x against a price made before the scratchings. The clean test is races whose opening book is intact (110-135%):
  there the 6x ceiling still adds +378u on 42 extra bets, all four periods (3.6), and the committed live files, priced
  before the late scratchings, show the same thing on a small sample (17 runners, +24.5u). The direction is safe; expect
  less than the headline +27% to +35%.

## Part 2. Closer to BSP: 49 retrains of the stage-1 trees and the blend's members (queue1.py to queue5.py, report.py -> queues_report.out.txt)
Noise floor, the live settings on three seed sets: fold A KL 0.0929 +/- 0.0003, log loss 1.9058 +/- 0.0004, profit
+1,246u +/- 20u; fold B 0.0969 +/- 0.0001, 1.8354 +/- 0.0014, +1,360u +/- 47u. (Today's form-line and track-bias results,
-0.0004 and -0.0007 on fold A alone, sit inside it.) Fold B is new: trees trained only on Jul-Dec 2025 made +1,414u on
Jan-May 2026 at the open under the live rules, races never used as a test before.

### 2.1 What beat the live recipe in BOTH folds
| change | fold A: KL / log loss | fold B: KL / log loss | note |
|---|---|---|---|
| 8 seeds averaged (tests use 3, live 5) | -0.0012 / -0.0011 | -0.0011 / -0.0001 | free at training time |
| learning rate 0.03 with 8,000 rounds (live 0.06 / 4,000) | -0.0011 / +0.0004 | -0.0009 / -0.0025 | October's tuning tried 0.03 without the extra rounds and called it worse |
| + margin over the best other runner, 12 headline ratings | -0.0007 / -0.0001 | -0.0004 / -0.0006 | every rating reaches the trees as "minus the best in the race", 0 for the top horse; this adds the top horse's margin over the second. The full 111-input version, the z-scores and the rivals-close counts add nothing |
Each is about 1% of the distance to BSP at three seeds. queue4.py checks them together at the live seed count (2.6):
about half of each survives, and the margin input does not.

### 2.2 What did not
- The blanked copy stays: without it KL +0.0011 / +0.0000 and log loss worse in both folds. On 40% of runners instead
  of 80%: no different.
- min_data_in_leaf 50 / 200 / 400, lambda_l2 1 / 50, feature_fraction 0.1 / 0.35, bagging 0.6, num_leaves 31, weighting
  races by how complete the BSP book is: all inside the noise. num_leaves 7, 2,000 rounds and extra_trees off: worse.
- PRUNING IS WORSE: the 400 inputs with the most gain +0.0033 / +0.0034, the top 200 +0.0061 / +0.0093. The long tail
  of small inputs earns its place.
- New inputs: sire and dam sire on today's going class and distance band, jockey at the track, trainer in the distance
  band (rolling, earlier races only): KL -0.0005 / -0.0000, inside the noise.

### 2.3 What the model stands on (each family removed, KL change fold A / fold B)
Trial form and section splits +0.0037 / +0.0041; our rolling trainer / jockey / stable records +0.0030 / +0.0023 (and
-197u / -188u of profit, the biggest money effect of any family); speed and sectional figures +0.0011 / +0.0027; Form
King's form records +0.0013 / +0.0007. Removed with no measurable loss on its own: gear detail, past price moves, bias,
speedmap, sire, head-to-head, past market, track-surface-going, the neural rating, Form King's jockey and trainer
percentages (log loss worse on fold A), the field-relative copies (KL a little worse, winner log loss a little BETTER
in both folds: they help us follow the market more than they help find winners).

### 2.4 The learning curve: history is still the biggest lever
Fold A's holdout (3 Jun - 9 Nov), trees trained on less history ending 2 Jun:
| trained from | training races | KL to BSP | winner log loss |
|---|---|---|---|
| 1 Mar 2026 | 1,041 | 0.1028 | 1.9157 |
| 1 Jan 2026 | 1,652 | 0.0992 | 1.9116 |
| 1 Oct 2025 | 2,682 | 0.0950 | 1.9053 |
| 1 Jul 2025 (all) | 3,636 | 0.0932 | 1.9053 |
Each doubling of the history has been worth about 0.004-0.006 of KL, 4-6% of the distance to BSP, and the last 36%
still bought 0.0018. Nothing else tested tonight is worth more than 0.0012. Form King's own history starts 1 Jul 2025,
so more Victorian history only comes with time (the model gains about 1% every two months by being retrained); the
national archive is the only way to buy a doubling, and other states' races will not transfer in full.

### 2.5 A model for the price before riders are declared (no_rider_model)
The same trees trained with no rider input at all (47 inputs out): KL 0.1046 / 0.1078 against 0.0932 / 0.0970, about
12% further from BSP; at the open under the live rules +829u against +1,238u (fold A) and +1,249u against +1,414u
(fold B). Blanking the riders on the LIVE model instead costs 29% (4.4). So the early price should come from a model
trained without riders, kept beside the live one, and be replaced by the live price when the riders land.

### 2.6 The three small gains together, at the live seed count (queue4.py)
Queues 1 and 2 ran on three seeds; live averages five. The same arms on five:
| softmax trees | fold A: KL / log loss / profit | fold B: KL / log loss / profit |
|---|---|---|
| live settings, 5 seeds | 0.0924 / 1.9044 / +1,186u | 0.0963 / 1.8344 / +1,530u |
| learning rate 0.03, 8,000 rounds, 5 seeds | 0.0919 / 1.9051 / +1,253u | 0.0959 / 1.8330 / +1,470u |
| the same + the 12 headline margins | 0.0921 / 1.9066 / +1,230u | 0.0960 / 1.8335 / +1,461u |
| live settings, 10 seeds | 0.0919 / 1.9042 / +1,252u | 0.0959 / 1.8345 / +1,476u |
- Going from three seeds to five already took half of what the extra seeds had to give (0.0932 to 0.0924 on fold A).
- Slower learning and ten seeds are each worth 0.0004-0.0005 on top, about half a percent of the distance to BSP, in
  both folds. Winner log loss and profit do not move outside the noise (+/-20u to +/-47u).
- THE MARGIN INPUT ADDS NOTHING once the trees are slow and on five seeds (0.0921 v 0.0919, log loss worse in both
  folds). It is not worth a new input family. Dropped.
- So the stage-1 trees are at their ceiling for this recipe and this history. The honest size of everything the night
  found on the training side is half a percent. More history (2.4) is worth ten times that.

### 2.7 The blend's members and weights, walk-forward (queue3.py)
The live stage 1 is trees 0.5 (softmax 0.7 + regression 0.3), network 0.3, CatBoost 0.2, weights fitted in September
on out-of-fold prices. Each member trained inside each fold, exactly as live trains it:
| price | fold A: KL / log loss / profit | fold B: KL / log loss / profit |
|---|---|---|
| softmax trees alone | 0.0932 / 1.9053 / +1,238u | 0.0970 / 1.8348 / +1,414u |
| regression trees alone | 0.0963 / 1.9133 / +1,289u | 0.1014 / 1.8409 / +1,285u |
| network alone (3 seeds) | 0.0987 / 1.9120 / +1,047u | 0.1053 / 1.8448 / +1,287u |
| CatBoost alone | 0.0959 / 1.9142 / +1,214u | 0.1032 / 1.8429 / +1,449u |
| trees: 0.7 softmax + 0.3 regression | 0.0924 / 1.9059 / +1,307u | 0.0965 / 1.8348 / +1,433u |
| no-network blend: trees 0.7 + CatBoost 0.3 | 0.0913 / 1.9063 / +1,215u | 0.0963 / 1.8350 / +1,460u |
| LIVE blend: trees 0.5, network 0.3, CatBoost 0.2 | 0.0893 / 1.9038 / +1,157u | 0.0945 / 1.8334 / +1,523u |
- THE BLEND IS THE BIGGEST SINGLE THING IN STAGE 1: 4.2% closer to BSP than the best member on fold A, 2.6% on fold B,
  and better on winner log loss in both. No retrain of the trees comes near it.
- THE LIVE WEIGHTS ARE RIGHT. The best weights found on fold B (0.6 / 0.3 / 0.1) score 0.0896 on fold A against the
  live weights' 0.0893; the best on fold A (0.4 / 0.3 / 0.3) score 0.0947 on fold B against 0.0945. The regression
  share of the trees is flat from 0 to 0.5. Leave all of it.
- THE NETWORK IS THE WEAKEST MEMBER ALONE AND THE MOST USEFUL IN THE BLEND (the no-network blend is 2.2% and 1.9%
  further from BSP). It is useful because it is different: the 3-seed network sits a median 15-16% from the trees
  runner by runner.
- It is also the noisiest: two network seeds are a median 13.6% apart on the same runner (90th percentile 36%). Live
  re-trains five seeds every time a day is priced. On the frozen history that gives the same five networks every
  time; once the history is refreshed each morning (1.3) the network third will move from one day to the next on
  noise alone (at Seymour it moved 7.5% on the refresh, 1.8). queue5.py measures what more seeds buy (2.9).
- Profit does not follow KL here (the live blend makes the least on fold A and the most on fold B): 1,700 bets a fold
  is too few to rank prices that are 2-4% apart by money. KL to BSP on 1,500+ races is the measure that can.

### 2.8 Mixing recipes against adding seeds (recipe_mix.py)
Every arm of queues 1-2 that kept all 809 inputs is a different set of trees. Averaged, from the saved prices:
| softmax trees | fold A: KL / log loss | fold B: KL / log loss |
|---|---|---|
| live settings, 3 seeds | 0.0932 / 1.9053 | 0.0970 / 1.8348 |
| live settings, 9 seeds | 0.0921 / 1.9049 | 0.0960 / 1.8345 |
| live settings, 10 seeds | 0.0919 / 1.9042 | 0.0959 / 1.8345 |
| 3 recipes x 3 seeds (live, slow, 31 leaves) | 0.0918 / 1.9050 | 0.0961 / 1.8331 |
| all 14 full-input recipes x 3 seeds (42 models) | 0.0917 / 1.9050 | 0.0957 / 1.8329 |
| slow 5 seeds + live 10 seeds | 0.0917 / 1.9045 | 0.0957 / 1.8336 |
- A different recipe is no more different than a different seed: two 3-seed sets of the live settings sit a median
  5.4% apart runner by runner; live against slow 4.4%, against 31 leaves 5.9%, against a feature share of 0.1 5.6%.
  So 42 models of 14 recipes land where 10 seeds of one recipe do. The trees stop improving at about 0.0917 / 0.0957.
- INSIDE THE FULL BLEND THE GAIN SHRINKS TO 0.2%: live blend with the 3-seed trees 0.0893 / 0.0945; with 10 seeds
  0.0891 / 0.0943; with the slow trees 0.0891 / 0.0944; with all 42 models 0.0891 / 0.0943. The network and CatBoost
  already average away most of what extra trees would.
- Verdict on the training side: nothing to change. With the network on 5 seeds, as live has it, even the 0.2% goes
  (2.9).

### 2.9 Seeds for the network and CatBoost, and everything together (queue5.py, seed_stability.py)
20 network seeds and 3 CatBoost seeds per fold. Live averages 5 network seeds and uses 1 CatBoost model.
| network seeds | network alone: fold A / fold B KL | the live blend: fold A / fold B KL |
|---|---|---|
| 1 | 0.1054 / 0.1107 | 0.0900 / 0.0948 |
| 3 | 0.1000 / 0.1055 | 0.0895 / 0.0943 |
| 5 (live) | 0.0992 / 0.1044 | 0.0894 / 0.0942 |
| 10 | 0.0985 / 0.1036 | 0.0894 / 0.0942 |
| 20 | 0.0981 / 0.1033 | 0.0893 / 0.0941 |
- The network alone gains 7% from 1 seed to 20; inside the blend 5 seeds already have it (0.0894 against 0.0893).
  CatBoost alone gains 3.5% from 1 seed to 3 (0.0965 to 0.0932 on fold A, 0.1043 to 0.1004 on fold B); inside the
  blend 0.0001 to 0.0002.
- EVERYTHING TOGETHER CHANGES NOTHING. The live recipe (trees 5 seeds, network 5, CatBoost 1): 0.0891 / 1.9031 on fold
  A, 0.0942 / 1.8332 on fold B. Trees 10 seeds, network 20, CatBoost 3: 0.0892 / 1.9029 and 0.0941 / 1.8326. Slow trees
  with the same: 0.0892 / 1.9032 and 0.0941 / 1.8321. THE LIVE STAGE-1 RECIPE IS AT ITS CEILING ON THIS HISTORY: every
  gain found on a single member is already averaged away by the other two.
- How much of the bet list is the network's seed: the blended price on two different draws of 5 network seeds is a
  median 1.8% apart runner by runner (90th percentile 4.9%); 93% of the bets are in both lists, with stakes within 2%.
  The 7% that are in one list only are the small ones at the margin (1.6u a bet against 2.0-2.2u) and they are the weak
  ones: +19% and +9% on stakes against +36% and +41% for the bets in both lists. Two 3-seed sets of the TREES do the
  same (93% shared; the one-list bets +5% and -14%). With 10 network seeds 95-96% are shared.
- What that means for live: once the history is refreshed each morning (1.3) the network is re-trained on slightly
  different races and about one bet in fourteen will come or go between the first price and a re-price for no reason
  but the seed. They are the marginal bets and worth little either way; a taken bet is never dropped, so no rule is
  needed. Ten network seeds at pricing time would halve it for about a minute more per meeting. Optional.

### 2.10 The second stage on two folds (s2_check.py)
Stage 2 v6 rebuilt on the 9 Nov dataset from the cross-fitted three-model stage-1 price, trained inside each fold as
live trains it (400 rounds, 7 leaves, learning rate 0.03, 3 seeds), scored on the fold's unseen races:
| price | fold A: KL / log loss | fold B: KL / log loss |
|---|---|---|
| stage 1 alone | 0.0873 / 1.8993 | 0.0848 / 1.8164 |
| + stage 2, live settings | 0.0813 / 1.8913 | 0.0798 / 1.8083 |
| the same on two other seed sets | 0.0813, 0.0812 | 0.0798, 0.0797 |
- STAGE 2 IS WORTH 6-7% OF THE DISTANCE TO BSP (6.9% and 5.9%) and improves winner log loss in both folds. It is the
  largest single step in the price after the blend.
- IT IS AT ITS CEILING. 10 seeds, 200 rounds, learning rate 0.015 or 0.06, 3 leaves, min leaf 100 or 400, feature
  share 0.4 or 1.0, lambda 1 or 50: every one within 0.0001 of the live settings in both folds, which is the seed
  noise. More rounds and bigger trees are worse (800 rounds +0.0004 / +0.0005; 1,600 +0.0010 / +0.0017; 15 leaves
  +0.0003 / +0.0004; 31 leaves +0.0007 / +0.0009).
- What it stands on (each block removed, KL change A / B): the market-gap encodings (how BSP rated this horse,
  trainer, jockey, sire, trainer-at-track against our price in earlier races) +0.0016 / +0.0016; the horse's earlier
  gaps +0.0003 / +0.0002; travel +0.0003 / +0.0002; collateral form +0.0002 / +0.0005; jockey switch +0.0002 /
  +0.0002; stablemates +0.0002 / +0.0001. The first version's inputs alone: +0.0009 / +0.0013, so versions 2 to 6
  together added 1.1-1.6%.
- The sections and trials blocks now add nothing in stage 2 (-0.0001 / +0.0001 and +0.0001 / -0.0002): both went into
  the stage-1 inputs in October and the trees already use them. Harmless; not worth a retrain to remove.
- The market-gap encodings are exactly what the frozen history starves (1.3): a horse that has run since 14 Oct is
  priced on the gap from the run before. The refresh is the one thing that helps this stage.

### 3.11 The chance the stake is sized on is honest (blend_calib_bets.out.txt)
The sheet's 3,484 walk-forward bets (6x ceiling) by open / our price, winners against the blended chance the Kelly stake
uses: 1.2-1.4x 173 won v 173.3 expected; 1.4-1.7x 232 v 228.9; 1.7-2.2x 154 v 150.6; 2.2-3x 58 v 62.2; 3-4x 17 v 15.4;
4-6x 9 v 7.3; all 643 v 637.7 (our price alone expected 688.6, BSP 617.0). The blend is calibrated on its own bets at
every overlay, the big ones included, so the stake needs no haircut there.

### 3.12 THE BETFAIR SP RULES ON MONTHS THAT NEVER CHOSE THEM (bsp_rules_oos.py)
The ten tracked rules were picked on 10 Nov from June-July, August-8 Oct and the live weeks. Jul 2025 - 2 Jun 2026 was
never looked at: four untouched periods, 2,900 races. Rules that read only the open and BSP are exact there; rules that
read our price use the walk-forward trees (2026) and the cross-fitted blend (2025), stage 1, a little blunter than live.
1u at BSP, 8% commission, first starters out. Bets, winners (BSP expected), units:

| rule | the four untouched periods | by period | 3 Jun - 8 Oct (chosen on) | 9 Oct - 9 Nov | verdict |
|---|---|---|---|---|---|
| Lay $8-$12, BSP >= 1.6x ours (CURRENT) | 502, 51 (50.6), -34.1u | -8.6, -34.0, -3.2, +11.8 | 149, 6 (15.0), +75.8u | -0.3u | FAILS |
| Lay $15-$40, BSP >= 1.5x ours (CURRENT) | 2,765, 126 (117.4), -457.2u | -255.6, +87.3, -211.1, -77.8 | 908, 21 (37.9), +335.4u | -68.2u | FAILS |
| Lay $25-$40, drifted 2x from open | 1,218, 39 (39.0), -89.9u | -180.6, -21.6, -20.1, +132.4 | 471, 11 (15.1), +119.8u | +144.4u | FAILS |
| Lay $8-$12, firmed 1.5x from open | 595, 66 (62.4), -85.2u | -24.8, -111.8, +56.0, -4.6 | +28.8u | +27.4u | FAILS |
| Lay $12-$15, drifted 1.25x from open | 1,294, 96 (97.2), -80.7u | -183.4, +37.1, +56.5, +9.0 | +33.5u | -4.6u | FAILS |
| Back $4-$7, firmed 1.5x from open | 968, 177 (186.8), -132.8u | -90.1, -36.1, +10.9, -17.4 | +23.7u | +39.6u | FAILS |
| Back BSP fav $4-$7, ours >= 1.6x BSP (CURRENT) | 189, 41 (40.9), -13.9u | -18.1, +10.3, +1.5, -7.6 | +25.6u | +0.4u | FAILS |
| Lay $25-$40, BSP <= ours/1.6 | 271, 6 (8.9), +77.1u | +19.7, +64.4, -11.4, +4.4 | +48.3u | +18.4u | holds 3 of 4 |
| Back $3-$5, firmed 1.5x from open | 774, 228 (199.1), +58.5u | -3.6, +11.7, +28.8, +21.6 | +16.5u | +3.2u | holds 3 of 4 |
| Back $4-$7, ours >= 1.6x BSP (any runner) | 851, 188 (164.8), +47.4u | -0.2, +9.6, +3.3, +34.7 | +10.0u | -0.0u | holds 3 of 4 |

- THE LAY EDGE EXISTS ONLY IN THE PERIOD THE RULES WERE CHOSEN ON. The $15-$40 lay: 21 winners against 37.9 expected
  from June to 8 Oct; 126 against 117.4 in the eleven months before; 17 against 14.0 in the live weeks. The $8-$12 lay:
  6 against 15.0, then 51 against 50.6. Outside June-October these runners win exactly as often as BSP says, and a lay
  at BSP then loses the commission.
- The tracker's best rule (lay $25-$40 drifted 2x from the open, +122u live on 167 lays, 1 winner against 5.3) is dead
  even on 1,218 untouched lays: 39 winners against 39.0. The live month was the lucky tail of a fair bet.
- What survives is small and on the BACK side: firmers at $3-$5 (228 won against 199.1 by BSP, +58u, and positive in
  the chosen and live periods too: six periods, five positive, +78u on 1,171 bets), and $4-$7 runners the market has far
  shorter than we do (188 against 164.8, +47u). The first reads only prices; the second agrees with the live scorecard
  (where BSP is 1.5x+ shorter than us the horse wins more than even BSP says). The same firmers at $4-$7 fail, so even
  these are weak: z about 2.4 and 2.1 before allowing for ten rules.
- This is the same conclusion as 1.1 from the other side: BSP is efficient against everything we hold. The model's
  value is at the open.
FOUNDER'S CALL before Friday 13 Nov: the paper lay book and the live $50 lays rest on rules that do not survive eleven
untouched months. Keep them on paper (the tracker costs nothing), and do not put real money behind the two current lay
rules on this evidence.

### 3.13 Does BSP under-react to its own move? (bsp_move.py, no model, 50,700 runners, three eras)
Winners against BSP's expected winners by how far the price moved from the open: drifted 2x+ 0.95 (0.94 / 0.96 / 0.96
by era, 15,038 runners, most of them $40+, so the lay is all liability); drifted 1.5-2x 1.02; drifted a little 1.03;
steady 0.97; firmed a little 0.98; firmed 1.25-1.5x 0.98; firmed 1.5-2x 1.00; firmed 2x+ 1.05 (1.00 / 1.17 / 1.00).
BSP has the move priced. Inside the big firmers only $3-$5 stands out, in all three eras (A/E 1.10 / 1.21 / 1.10,
1,322 runners, +7.5% backed at BSP after commission), and its neighbours do not ($1-$3 0.99, $5-$7 0.91, $7-$10 0.87):
an island in a grid of twelve cells, already in the tracker, not a book. There is no BSP-side edge in the prices alone.

### 3.14 The ceiling in races whose opening market stayed intact (ceiling_clean_book.out.txt)
Opening book 110-135% (nothing much scratched after the open, so the price on the final field is the price we could
have had), every live block on, deduction by race: walk-forward 3x +1,614u, 6x +2,018u (+25%; +708 v +529, +322 v +267,
+754 v +681, +234 v +138); blend 3x +2,063u, 6x +2,584u (+25%, five of six periods). The extra bets are FEW: 32 and 35
(about three a month), 6 and 8 winners where BSP's chances said 3.7 and 4.1, median open $26, BSP 0.4x the open. The
gain does not need those winners to have been lucky: a horse that opens at 2.5x where the market ends up is a bet at
BSP's own strike rate. So the honest size of the change is about three more bets a month in clean races plus the
scratching-affected ones (which pay less after deductions), for roughly a quarter more profit.

### 3.15 The ceiling on a third price (ceiling_third_price.py)
Queue 3 produced a price neither ceiling test had: the walk-forward THREE-MODEL blend, every member trained inside the
fold, live weights, the closest thing here to the live stage 1. Plain live rules at the open (first starters in, no
blocks, flat 16c), 1 Jan - 9 Nov:
| ceiling | 1 Jan - 17 Mar | 18 Mar - 2 Jun | 3 Jun - 8 Oct | 9 Oct - 9 Nov | all four |
|---|---|---|---|---|---|
| 3x | +891u | +632u | +854u | +303u | +2,680u on 3,418 bets (+38%) |
| 4x | +951u | +722u | +1,115u | +315u | +3,103u (+42%) |
| 6x | +1,024u | +737u | +1,275u | +390u | +3,427u on 3,621 bets (+46%) |
| none | +1,024u | +732u | +1,249u | +389u | +3,394u (+45%) |
6x against 3x: 203 more bets, 30 more winners, +747u (+28%), better in all four periods; nothing above 6x. Three prices
(walk-forward trees, the cross-fitted blend, the walk-forward blend), fourteen periods between them, the same answer.

### 3.16 The ceiling, band by band (ceiling_bands.py; founder, 11 Nov: "show me the stats on the price increase")
Walk-forward three-model blend, 1 Jan - 9 Nov 2026, plain live rules at the open with no ceiling, every bet sorted by
how far the open was above our price:
| open / our price | bets | a month | won | BSP expected | median open | median BSP | staked | profit | on stakes | periods in profit |
|---|---|---|---|---|---|---|---|---|---|---|
| under 1.4x | 572 | 56 | 132 | 132.6 | $6.00 | $5.10 | 1,444u | +178u | +12% | 4 of 4 |
| 1.4x-1.7x | 1,377 | 134 | 243 | 228.7 | $9.80 | $7.40 | 2,606u | +768u | +29% | 4 of 4 |
| 1.7x-2.2x | 1,028 | 100 | 171 | 161.4 | $13 | $8.30 | 2,162u | +1,144u | +53% | 4 of 4 |
| 2.2x-3x | 441 | 43 | 59 | 67.3 | $17 | $8.00 | 909u | +590u | +65% | 4 of 4 |
| 3x-4x | 128 | 12 | 20 | 17.3 | $26 | $9.20 | 241u | +423u | +175% | 4 of 4 |
| 4x-6x | 75 | 7 | 10 | 8.6 | $34 | $11 | 142u | +324u | +228% | 4 of 4 |
| 6x and over | 15 | 1 | 0 | 1.7 | $61 | $12.40 | 33u | -33u | -100% | 0 of 4 |
The 203 bets between 3x and 6x: 30 winners where BSP's chances said 25.9, +747u on 383u staked, 94% of them opened
above BSP and BSP lands at 0.39 of the open. Without the three biggest winners +588u; the longest losing run is 18
bets; the biggest single win +56u. The winners opened $8 to $51 (median $19). These counts are with first starters in
and no blocks; with the live blocks on it is about 12 a month (3.10).

### 3.17 Anything else at Betfair SP? A full sweep on the live-style price (bsp_scan.py, bsp_scan2.py)
The price: stage 2 trained inside each fold and blended with the open as live does (2026), the cross-fitted blend with
the same open blend (Jul-Dec 2025). Six periods, 1u at BSP, 8% commission, first starters out.
- WHEN WE DISAGREE WITH BSP, BSP IS RIGHT, at every size of disagreement. Where the market has a runner at half our
  price or less (1,523 runners): we expected 91 winners, BSP 218, and 218 won. Where we have it at half the market's
  price (1,679): we expected 210, BSP 88, and 80 won. Winners against BSP's expected sit between 0.91 and 1.03 in all
  nine bands and no band pays a back or a lay in more than four of the six periods.
- THE TWO CURRENT LAY RULES ON THIS SHARPER PRICE: lay $8-$12 where BSP is 1.6x ours, 596 lays, 53 won against 59.8;
  by period +10u, -33u, -35u, -9u, +52u (the months it was chosen on), +41u. Lay $15-$40 where BSP is 1.5x ours, 3,648
  lays, 143 won against 153.2, -22u; by period -147u, +8u, -43u, -25u, +256u (chosen on), -71u. Same answer as 3.12:
  the edge is the June-October sample.
- THE GRID (six BSP bands by six bands of BSP / our price, backs and lays, 72 cells): two pay in five of six periods,
  about what luck gives. Lay $20-$40 where BSP is 0.6x ours or less (510 lays, 11 won against 19.4, +207u, 1.55% of the
  liability; already tracked as the $25-$40 rule) and lay $8-$12 in the same band (565, 48 against 58.7, +53u). The cell
  between them ($12-$20, same band) runs the other way (A/E 1.26), so this is not a pattern.
- NO MODEL: winners against BSP by price band are 0.95 to 1.05 from $1 to $40. Only $100+ is off (22 won against 30,
  the lay pays in all six periods), which is a hundred units of liability to win one: not a book.
- OUR TOP PICK at BSP: 4,910 bets, 1,572 won against 1,543, -1.8% after commission. Top pick that is not the BSP
  favourite: A/E 1.10, +4.9%, but two periods of six.
- WHAT SURVIVES, all small: (1) back $3-$5 runners that firmed 1.5x+ from the open, 1,171 bets (72 a month), 338 won
  against 300.2 (z 2.5), +6.7% a bet, five of six periods (-4, +12, +29, +22, +16, +3), no model needed and our price
  adds nothing to it; (2) the $20-$40 lay above; (3) back $20-$40 runners that firmed 1.25x+ from the open AND that we
  rate 10%+ shorter than BSP, 139 bets (9 a month), 12 won against 5.0, +164u, five of six periods, found by splitting
  a wider cell after the fact ($8-$20 on the same rule: 30 won against 28.8, -15u), so it is a paper rule at most.
  Together, if all three held, about +25u a month at 1u a bet against a median +207u a month at the open.

### 3.18 Liquidity at BSP (bsp_scale.py, open_bets_at_bsp.py; founder, 11 Nov: "Yeah but more liquidity at bsp")
More liquidity multiplies an edge; it does not make one.
- THE OPEN BOOK'S OWN BETS STRUCK AT BSP INSTEAD: 3,621 bets, +41% flat at the open, -4.7% at BSP (1 of 4 periods
  pays). The 3x-6x bets: +165% at the open, -4.0% at BSP. Every band loses at BSP. The edge is the opening price, not
  the horse.
- THE THREE BSP SURVIVORS SCALED TO THE OPEN BOOK'S MEDIAN MONTH ($10,350):
  back $3-$5 firmed 1.5x+: $2,157 a bet, 72 a month; A/E 1.13 but 2 SD either side is 1.03 to 1.23 and it pays only
  above 1.06, so the edge could be -3.4% a bet; at that stake 38% of months lose, one in five worse than -$16,200.
  lay $20-$40 where BSP is 0.6x ours or less: $813 a lay, about $20,300 liability each, 31 a month; 11 winners against
  19.4, but 2 SD reaches A/E 1.01 against a break-even of 0.92; 22% of months lose, the worst 5% under -$21,000.
  back $20-$40 firmed and rated shorter: $1,030 a bet, 9 a month; 48% of months lose; found after the fact (3.17).
  The open book at $50 a unit loses in about 2% of months (3.7).
- We hold no Betfair volumes, so the BSP pools for a Victorian country race are not measured here. A large SP back
  order shortens the BSP it is settled at and a large SP lay lengthens it, so the stakes above would also eat into
  their own edge. Betfair's own data (the planned API key) is the way to measure it.
