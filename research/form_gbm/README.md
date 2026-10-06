# Form King-only price: boosted trees fitted to BSP (28 Sep 2026)

No input from today's market. Past-run prices are in (the horse's own BSP history).
Data: `scripts/export_dataset.py` (workflow `fk export`, kept on the `datasets` branch):
3,632 VIC races, 35,660 runners, 293 Form King columns plus each runner's last 10 runs.
Split by date: fitted on the older 2,539 races, scored once on the newer 1,093 (27 May to 27 Sep).

Model: LightGBM with a softmax-within-race objective against the BSP chances (soft labels),
589 inputs (the 293 plus past-run summaries, each also measured against today's field:
rating shape, speed and sectionals, beaten margins, past prices, spacing, distance, going,
track). Trained on the races twice, once as stored and once with the speed and sectional
figures blanked on 80% of runners, because live-pulled runners are often missing them.

| unseen races | opening market KL | new model KL | deployed form price KL |
|---|---|---|---|
| all 1,093 | 0.1371 | 0.1107 | 0.1789 |
| 78 pulled before the jump | 0.1817 | 0.1586 | |
| 1,015 back-filled | 0.1336 | 0.1070 | |

Log loss against winners, all 1,093: new 1.9705, market 1.9771, deployed 2.0168.

Leakage checks: past-run prices recomputed from date-filtered runs match (94%) and correlate
no more with today's BSP; entry ratings differ run to run (race-day figures, not pull-day);
career wins gain an extra win at the same rate for winners and losers. The model trained
without the gap copy lost to the market on the 78 live races only because 81% of those
runners lacked their speed figures; blanking the same figures on back-filled races reproduced
most of the drop.

Run: `python run4.py` (needs `ds/model_ds.npz` from the datasets branch, lightgbm, numpy).

## Second pass (same day): 0.1107 -> 0.1020

Decisions made on the newest fifth of the training races; the unseen races scored once at the end.

| step | validation KL |
|---|---|
| first model | 0.1136 |
| + class change, weight-adjusted ratings, first-up history, consistency, campaign runs, past implied chances, race context | 0.1081 |
| extra_trees, 20% of inputs per tree | 0.1060 |
| + head-to-head form among today's runners (past race ids), jockey change | 0.1036 |
| average of five seeds | about 0.103 |

Tried and dropped: race context alone (no KL gain), a winners/BSP target mix, adding first-three
finishing order to the objective (worse on both scores), temperature scaling (already calibrated),
blending with the linear price.

Final (`final.py`, five models averaged), unseen races:

| races | market KL | final KL | market log loss | final log loss |
|---|---|---|---|---|
| all 1,093 | 0.1371 | 0.1020 | 1.9771 | 1.9627 |
| 78 pulled before the jump | 0.1817 | 0.1574 | 1.8826 | 1.8568 |
| 1,015 back-filled | 0.1336 | 0.0977 | 1.9843 | 1.9709 |

Value bets worth 20c+ at the opening price: back-filled +41.9% over 2,257 bets, but -11.6% over
137 bets on the live-pulled races, where every model tested loses at the stored opening price.
The live and back-filled opening prices may not be the same quantity; the paper book decides.

## Second stage: the market's past view of each horse (28 Sep 2026)

`stage2.py` adjusts the 3-way price by how BSP rated each horse, trainer, jockey and sire against our own
price in EARLIER races: the horse's last-run gap, its 120-day decayed average gap, trainer, jockey, sire
and trainer-at-track averages (shrunk), fed to a 7-leaf race-softmax LightGBM with the 3-way price as
init score. Trained on all 3,632 out-of-fold races (`stage2_train.py`, models in `models/`); applied to a
day by `apply_stage2.py`.

| test (KL to BSP, lower is closer) | before | after |
|---|---|---|
| out-of-fold, races from 6 May (fit on earlier races) | 0.0940 | 0.0883 |
| leak-free: stage 1 trained on the older 70%, gaps only from unseen races | 0.1026 | 0.0978 |

Tried with no gain: race-level temperature, recency-weighted training (worse), past open-to-BSP drift
encodings, jockey x trainer / horse x track / horse x distance / trainer first-up encodings, extra form
features in the second stage. CatBoost QuerySoftMax as a fourth member: 0.0975 to 0.0969 on the lab
split, not deployed.

## The longer push (29 Sep 2026): holdout KL 0.0883 to 0.0848

All scores are KL to BSP on races from 6 May (opening market 0.1365).

| step | holdout KL |
|---|---|
| trees only, out of fold (what the first second stage was trained on) | 0.0940 |
| + network out of fold (65/35) | 0.0918 |
| + CatBoost QuerySoftMax out of fold (trees 0.5, net 0.3, CatBoost 0.2) | 0.0909 |
| + second stage: BSP-gap encodings (horse, trainer, jockey, sire, trainer at track) | 0.0851 |
| + stablemates, jockey gap vs the horse's last jockey, horse gap trend | **0.0848** |

Found on the way: the first second stage was fitted on tree-only out-of-fold prices while it was applied to the
three-way blend; it is now fitted on the blend it is applied to (`p_oof_blend3`, `stage2b_*`).
Where the remaining distance is: 89% of the KL sits on the eventual BSP favourite; races with 3+ first starters
(0.145) and 2yo races (0.126) are the hardest per race.

No gain (lab split unless noted): BSP/SP blended labels (0.1015 vs 0.1009), past-market features from the
last 10 runs (0.1042), bigger trees (0.1025), field-aware set network (0.1077 vs 0.1072), attention network
(0.1099), second-stage trainer/sire first-starter and dam-sire gaps, a third stage on second-stage gaps (0.0874 vs
0.0875 walk-forward), second-stage hyperparameters (all 0.0854 to 0.0855).

Day pricing: `price_day2.py` (four models) then `apply_stage2b.py`.

## Springboard: late speed beyond the tempo (29 Sep 2026, founder's idea)

Raw last-600 vs class barely registered in the trees (ranks 250 to 650 of 743) because a slow tempo inflates
the late split. Adjusted for the race's early tempo (mean run-to-600 vs class of every runner we hold from
that race): last600 = -3.94 - 0.35 x tempo, and the residual is late speed beyond the tempo.
Springboard = last race run in the top fifth of that residual (>= 4.21L) while rated at or below class.
Next start, out of fold: wins vs our price 1.08, vs BSP 1.07 (4,136 runners). As a second-stage input it
moves KL only 0.0848 to 0.0847, but as a filter on value bets (1 unit, opening price):

| plan | bets | open | BSP | holdout open |
|---|---|---|---|---|
| value 20c+ | 7,111 | +38.7% | -1.6% | +47.4% |
| value 20c+ and springboard | 914 | +63.4% | +16.7% | +86.6% |
| value 20c+, not springboard | 6,197 | +35.1% | -4.3% | +42.4% |

Lesson: judge an idea as a bet filter as well as by whole-market KL; a signal on one runner in eight cannot
move KL and can still be the best bet type.

## Where BSP is wrong (29 Sep 2026)

Single inputs: 3,115 fifths of every input tested for winners vs BSP-expected on older and newer races; 12 were
off by 8%+ the same way on both, against 18 expected by chance (simulated winners drawn from BSP). BSP prices every
single input. Edges are combinations with a racing reason.

Handicapping-book angles (Brohamer, Beyer, Quinn, Scott, Mordin, Ragozin, Cramer, Betfair AU) as filters on value
20c+ bets. Picked on races before 6 May only (BSP ROI > +5%, 60+ bets): beaten by the pace, class drop by prize,
already run to par, bounce after a new top, third-up, declining deep in prep, market liked it before a bad run, weight
relief, back in trip after being handy, proven wet, class drop by rating, late 600 beyond tempo. Judged once on the
untouched newer races:

| value 20c+ and... | newer races bets | BSP | open |
|---|---|---|---|
| any picked angle (9.9 bets a meeting) | 1,768 | +15.3% (+/-11%) | +66.0% |
| no picked angle | 942 | -24.0% | +12.9% |

The angles sort the value bets: value without a racing reason is mostly the market being right. Several are the
authors' "fade" angles, profitable as value bets: the market over-reacts to the story (bounce, decline, bad last run)
and a form model does not.

## Stage 2 v3: section splits (30 Sep 2026)

Form King's section splits (lengths vs class, leader and field for each 200m and the 800-400) now come through the
export in `S` / `sec_fields`, kept apart from `P` so stage 1 sees exactly what it was trained on. `stage2.sections()`
turns the last race runs into 13 inputs: middle (800-400) vs class and vs leader, last 200 vs field, start-800 and
last 600 vs class, middle minus the whole-run figure, a real-move-then-faded flag, three-run means, race-relative
versions and a has-data flag. Holdout KL to BSP (races from 6 May): 0.0848 -> **0.0835** (t_sec_s2.py).
As a standalone betting angle the fast middle was slightly over-bet next start (A/E 0.94 at BSP, t_sec.py);
it helps as a model input, not as a bet on its own. Live: stage2c_train.py (400 rounds x 3 seeds) and apply_stage2c.py.

## Stage 2 v4: trial form (30 Sep 2026)

Found by scoring the first two meetings the models never trained on. Tatura 29 Sep: KL 0.179 against the
opening market's 0.153, most of it Race 1, where The Shyster (first starter, won its last three trials) was
$19.80 with us and $2.60 at BSP. Re-pricing Tatura from the history-format export gave the same numbers, so
it is the model, not the live pipeline. `stage2.trials()` adds 13 trial-form inputs. Holdout KL 0.0835 ->
**0.0824** (t_trial_s2.py). Out of sample: Tatura 0.179 -> 0.163 (open 0.153), Kilmore 28 Sep 0.090 -> 0.068
(open 0.169). The Shyster only moves to $14.45: stage 2 adjusts stage 1's price, and stage 1 has no trial
inputs, so the full fix is trial form in the stage-1 models at the next retrain. Live: stage2d_train.py,
apply_stage2d.py. score_meet.py scores any priced meeting against its results; subset_meet.py cuts a resulted
meeting out of the history export so it can be re-priced through the day pipeline.

## Model v5: stage 1 retrained with trial form and section splits (30 Sep 2026)

F9 = the 743 F7 inputs + stage2.trials (13) + stage2.sections (13). Every stage-1 model re-fitted on it,
same 5 date blocks, same settings (oof_f9.py, oof2_f9.py nn|cb, blend_f9.py 0.5/0.3/0.2), then stage 2 on
the new blend (stage2e_*). Out-of-fold KL to BSP, all races: trees 0.0963 -> 0.0929, net -> 0.0980,
CatBoost -> 0.0968, blend 0.0934 -> **0.0897**. Holdout (races from 6 May) with stage 2: live v4 0.0824 ->
**0.0802** (the trial inputs add nothing in stage 2 once stage 1 has them). Out of sample through the day
pipeline: Tatura 29 Sep 0.163 -> 0.156 (open 0.153), Kilmore 28 Sep 0.068 -> 0.069 (open 0.169); The Shyster
$19.80 -> $10.97 (BSP $2.60), so trial form is still under-weighted for first starters.
Day pricing: price_day3.py (asserts the day's input names equal F9_names.txt) then apply_stage2e.py with
p_oof_blend9.npy. Final models all9_sm*, all9_rg*, cb_all9.cbm are too large for main: kept on the `models`
branch, gzipped.

## Deductions (1 Oct 2026)

Paper bets struck at the opening price settle at the price after bookmaker deductions for runners scratched after
the open. The user's bookmaker applies the deduction to the WHOLE price: $10 with a 50c deduction pays $5 (4u profit
per unit), i.e. effective price = open x (1 - deduction), not 1 + (open - 1) x (1 - deduction). Each race's deduction
comes from scripts/scratch_report.py (sum of 1/price of runners scratched after a price was quoted, under 2.5c ignored,
capped at 75c; emergencies that never gained a start do not count). BSP settlement needs no deduction.

## Rule: no EDGE in a race with a backed first-starter (1 Oct 2026)

After Pastoral King (Warrnambool R4, first starter, $5 to $3.30, won by 8L; model $8.19) and The Shyster (Tatura R1).
Value 20c+ bets on other horses, by race type (p_oof_blend9, all races): no first-starter +53% at open / -1% at BSP
(5,468 bets); only first-starters over $6 +59% / +6% (924); a first-starter at $6 or shorter at the open +12% / -28%
(577 bets; newer races -23% at BSP). Backed first-starters win 24.4% against 18.6% the model gives them (market
21.9%). The pages (market_tpl.html) drop the EDGE tag in such a race and say why; paper bets carry fs_backed_race.
(Open-price ROI here has no deductions taken off; BSP is unaffected.)

## Pro punters' ideas tested (4 Oct 2026)

Vince Accardi (Race Speed Profiles), Dan O'Sullivan (WFA ratings, wet tracks), Kingsley Bartholomew (The King Zone:
barriers, track bias). As stage-2 inputs (t_research.py, holdout KL, live 0.0806): all three sections above the field
0.0806, best this prep 0.0805, wet-track indicator 0.0806, best zone at the 800 0.0805, all four 0.0808: no gain.
As filters on value 20c+ bets at BSP (t_research_filter.py, t_kingsley.py; all value bets -14.1%, newer -13.0%):

| filter | bets | BSP all | BSP newer |
|---|---|---|---|
| all three sections above the field last run (angle added) | 713 | -0.5% | +1.2% |
| blinkers first time (angle added) | 476 | +9.1% | +26.9% |
| wet today, 1L+ worse on wet (no EDGE) | 887 | -27.9% | -32.3% |
| wide draw (outer quarter, 10+ field), usually back (no EDGE) | 358 | -47.8% | -41.4% |
| wide draw at 1600m+ (no EDGE) | 383 | -22.3% | -28.9% |
| wide draw in a sprint (watch, not used) | 383 | +9.5% | +23.4% |
| last run 3L+ below best this prep (watch) | 440 | +3.9% | +7.1% |
| best zone at the 800 | | no use | no use |

Cut-offs were chosen on all races, so these are looked-at results, not clean out-of-sample: the newer-races column
agreeing in direction is the check. Re-judge on live paper bets.

## First-starter races vs the rest (4 Oct 2026, t_fs_split.py)

Holdout races from 6 May, stage-2 v4 out-of-sample prices (pp from t_b9_s2), races with an opening price on every runner.
KL to BSP, lower is closer:

| races | n | model | opening market |
|---|---|---|---|
| all | 1,355 | 0.0806 | 0.1368 |
| no first-starter | 1,005 | 0.0722 | 0.1287 |
| first-starter, none $6 or shorter | 208 | 0.0865 | 0.1500 |
| first-starter at $6 or shorter | 142 | 0.1312 | 0.1746 |
| live-pulled, no first-starter | 55 | 0.1105 | 0.1611 |

The model is closer to BSP than the open in every group; races with a backed first-starter are where it is weakest.
Value 20c+ bets on non-first-starters at BSP: no first-starter -14.4% (2,153 bets), first-starter none $6 or shorter
+38.1% (351), backed first-starter -39.1% (205); live-pulled no first-starter -46.4% (94). Back-filled opening-price ROI
(+57%) is not a price that was available: live-pulled is +21% on 94 bets before deductions.

Value bets ON a first-starter (holdout, same prices): -34.9% at BSP over 266 bets (-15.1% even at the back-filled open),
live-pulled -84% on 23. Rule from 4 Oct 2026: no bet of any kind on a first-starter, and no bets in a race with a
first-starter at $6 or shorter. The race pages (market_tpl.html) and paper bets (paper_open.py, FS_JSON from fs_json.py)
both apply it; Top pick stays as a tracking plan unless the top pick is itself a first-starter.

## Resuming, drawn wide, short of trip (4 Oct 2026, after Garnacho, Bendigo R8)

Settling (t_goback.py, 24,195 past runs of usual midfield settlers): first-up from the wide half and 200m+ short of
the last trip, they settle 21 points further back than usual and 64% end up in the rear third (30% normally); first-up
from the inside half moves only 2 points. As stage-2 inputs (t_goback_s2.py) holdout KL 0.0806 -> 0.0808: the model
already prices this from days off, barrier, settle and distance. Value bets on that profile: 70 bets, -1.9% at BSP.
The leak is wider (t_firstup.py): value bets on first-uppers that are 200m+ short of their last start OR coming off a
bottom-half trial lost 25.6% at BSP (198 bets) against -3.2% for the rest (newer half -55.5%, older -8.5%).
Adopted 4 Oct 2026: no value or EDGE bet on a runner resuming 60+ days after its last race start that is 200m+ short
of that trip or coming off a bottom-half trial (fu_json.py writes the list; market_tpl.html tags it FU with the reason;
paper_open.py takes it as an optional seventh argument). Bendigo 4 Oct under all the 4 Oct rules: one EDGE bet
(Shapenapit); Garnacho and Volestain blocked.

## Pro punters' ideas, round 2 (4 Oct 2026, t_pros.py, t_pros_s2.py)

Value bets at BSP on the holdout with every current rule applied (2,135 bets, -3.2%), split by older/newer half:

| idea (source) | bets | BSP | older | newer |
|---|---|---|---|---|
| bounce: last start a new career-best rating by 3+ (Ragozin / Thoro-Graph / Mordin) | 190 | -40.1% | -55.4% | -22.8% |
| second-up after a first-up run that placed or was within 2L | 200 | -32.5% | -28.7% | -37.6% |
| down 2kg+ in weight on the last start (Don Scott, weight) | 340 | -32.2% | -46.4% | -10.5% |
| up 2kg+ | 599 | -11.6% | -17.5% | -1.8% |
| lone speed (quickest away by 1+ point, Form King early speed) | 86 | -27.9% | -26.4% | -30.2% |
| hot pace (3+ quick types), on-pace or backmarkers | 524 | about -29% | | |
| backing up within 7 days | 94 | +20.9% | +9.2% | +33.2% |
| apprentice claiming 2kg+ | 268 | +15.3% | +39.0% | -24.5% |
| **clear of bounce, second-up and weight-down** | **1,500** | **+8.2%** | **+8.5%** | **+7.8%** |

As stage-2 inputs nothing moved (holdout KL 0.0806 -> 0.0806; bounce alone 0.0809): the model and BSP already price
these horses on average; the model is wrong when it calls one of them value. Adopted as no-bet rules in fu_json.py
(bounce, second-up after a good first-up, weight down 2kg+). The three were chosen from about twenty tests on the same
races, so the +8.2% is the optimistic end; the live paper book is the check. Race prize money is not in the data, so
class-by-prize was not tested. Bendigo 4 Oct under every rule: no value bets (Shapenapit blocked as a bounce).

## Rules vs one trust layer vs an overlay surcharge (4 Oct 2026, t_trust.py, t_surcharge.py)

The founder's question: fold the rules into the price instead of blocking. Two versions, value bets at BSP on the holdout:
- A learned blend of our chance and the opening market's, with the weight on ours set by the risk flags (fit on one
  half, tested on the other): closer to BSP (KL 0.0866 -> 0.0783 and 0.0744 -> 0.0715) but value bets lose 5-9% at BSP,
  and the flags' effect on trust flips sign between halves.
- An overlay surcharge (each risk flag adds to the overlay needed): 10c + 40c a flag, 2,290 bets +5.1%; 10c + 100c a
  flag, 1,832 bets +8.3%. Blocking every flagged horse (7 flags incl. wide draw): 1,329 bets +13.7% (+9.9% older,
  +20.4% newer). The softer the treatment, the worse the return: the flags mark where the model is wrong, not slightly off.

## Betting at BSP with a minimum price (4 Oct 2026, t_loc.py)

The strategy an unattended bot could run (Betfair limit-on-close: back at BSP only if BSP is at least 1.2x our price)
loses on the holdout: -9.2% at BSP over 4,183 bets with no rules, -6.6% over 2,067 with the risk flags blocked
(1.1x and 1.3x are no better). A horse whose BSP drifts past our price has usually drifted for a reason. Whatever
edge there is sits at the early price, before the market moves, which is the price a bot can least easily get.

## Research pass, 4 Oct 2026: Benter, the academic models, the Betfair Hub, Australian pros (stage-2 inputs, holdout KL to BSP, live 0.0806)

Sources read: Benter 1994 (the annotated paper), Bolton & Chapman 1986, Lessmann/Sung/Johnson, the Betfair Hub automation
tutorials, a 562,000-runner AU/NZ study (BSP is calibrated within 0.2 points across the odds range: no favourite-longshot
bias to harvest), and what is public of Lawson, Lester, Accardi, O'Sullivan and the King Zone. Benter's factor list is
covered by Form King's inputs except two adjustments to past runs (barrier drawn, bad luck) and distance preference as a
standardised slope (his DP6A). Tested, two seeds unless stated:

| input | KL | note |
|---|---|---|
| travel: km from the stable's town to the track (pros: "the stable has travelled it") | 0.0803 | 4 seeds 0.0802-0.0805; older 0.0742, newer 0.0888 |
| collateral form: how last start's rivals went next time (Benter's key race) | 0.0805 | 4 seeds 0.0804-0.0806 |
| **travel + collateral** | **0.0800** | 4 seeds 0.0800-0.0802; older 0.0740, newer 0.0886: both halves |
| Benter DP6A distance preference (slope of vsClass on distance similarity / its SE) | 0.0806 | nothing |
| past-barrier adjustment to each past run's vsClass | 0.0806 | nothing |
| bad luck: closed from the back far faster than the overall rating | 0.0807 | nothing |
| King Zone in-day bias (where earlier winners today settled / drew, x this horse's style and draw) | 0.0805 | noise |
| round-2 pro ideas (bounce, second-up, weight change, pace count, lone speed, backing up) | 0.0806 | see above; betting rules instead |

Stage 2 v6 = v5 + travel + collateral (stage2.travel, stage2.collateral, stage2.last_start; stage2f_train.py,
apply_stage2f.py). Town coordinates are approximate and hand-entered (LL in stage2.py); an unknown town takes the median.

## Focusing on the $2-$15 horses (4 Oct 2026, t_band.py, t_pricecap.py)

Band KL = KL to BSP among runners that started $15 or shorter, renormalised per race (holdout):
opening market 0.0899; live v5 0.0586 (typical gap 24%, 52% within 25% of BSP); stage 2 fitted on $20-or-shorter runners
only, roughies left at stage 1: 0.0588 (no gain); per-band calibration of v5: 0.0591 (the band shifts are all under 0.02,
the model is already calibrated by price band); oracle with every $20+ roughie set to its BSP: 0.0521. So the band error
is not capacity spent on roughies; a third of it is the roughies' share of the race, which is unknowable before the jump,
and the rest is the band itself. Value bets at BSP by OUR price: $2-$15 1,000 bets -0.1% (older -0.6%, newer +0.8%);
over $15 +59% on 318 bets, but wins/model 1.27 (2.18 at $25-$50) says those are the back-filled opening prices being
softest on roughies, not a real edge. Betting inside $2-$15 is break-even at BSP and depends entirely on beating the open.

## Second-up after a good first-up: the open under-rates them (4 Oct 2026, t_secup_open.py)

Our 200 value bets on them: won 19.5%, open-implied 14.3%, BSP-implied 20.4%, model 21.6%; they firmed 21% to the jump
(71% shortened). +17% at the open, -32% at BSP. By open price: $1-$4 +79%/+36% (30 bets), $4-$8 +18%/-35%, $8-$15
+12%/-41%, $15+ -10%/-58%. The block (built off BSP) was costing an open-price bettor, so it is now an EARLY-ONLY tag:
allowed at $8 or shorter at the open, blocked above, and the page says to take the opening price or leave it.

## Staking (4 Oct 2026, t_staking.py)

On the live bet set in the backtest (value 20c+, all rules, our price $2-$15, 1,011 bets, average bet 1 unit): flat +56.4%
at the open / -0.5% at BSP; stake by overlay (20c over = 1 unit, 60c+ = 3) +72.6% / -0.7%; quarter Kelly +71.1% / +2.5%
but a biggest bet of 8.6 units. Adopted: stake by overlay, capped at 3 units, on EDGE and value bets (paper_open.py,
market_sheet.py); top pick stays 1 unit.

## Sizing and confidence, from outside racing (4 Oct 2026, t_confidence.py, t_stakeplan.py, t_targetmix.py)

Holdout, live bet set (1,186 bets), $100 a unit. Kelly under estimation error (Baker and McHale; Chu, Wu and Swartz):
size on a chance halfway between ours and the market's. Kelly x75 on the 50/50 blend, cap 4u: +64.7% at the open and
+0.2% at BSP at an average stake of 2.0u, worst drawdown about $7,400 typical / $11,000 in a bad season, against
+61.6% / -3.3% and $10,400 / $16,200 for stake-by-overlay cap 3 (avg 2.3u). Adopted. It moves money toward the $2-$6
horses (where the edge held at BSP) and off the $9-$15 overlays. Ensemble disagreement (trees vs net vs CatBoost):
the most-disagreed third of bets is worst (open +34%, BSP -16%) but the middle third beats the most-agreed, so a watch,
not a rule. Races with 2+ bets: +74% open / +4.5% BSP against +41% / -17% for single-bet races (watch). Kelly across
the runners of one race: no different from independent stakes. Fitting stage 2 to 85% BSP + 15% winner: no gain.
Closing line value: 77% of our bets shortened from the open to BSP, median move -28%; of the horses we price UNDER
the open, 18% shortened (median +53%). That is the edge in one line: the market moves toward us.

## Residuals (4 Oct 2026, t_resid.py): where the model is far from BSP, holdout, model KL vs opening market KL

Field size 4-7 0.073 / 0.103; 8-10 0.077 / 0.134; 11-13 0.084 / 0.149; 14+ 0.093 / 0.148. Distance: sprints (900-1200m)
0.094 / 0.148 are the weakest, staying races 0.070 / 0.128 the best. First-starters in the race: none 0.072, one 0.086,
two 0.100, three or more 0.121 (open 0.184). Tracks: metro races are where the open is sharpest (Flemington 0.074 / 0.092,
Sandown 0.064 / 0.083) and the model's margin over it smallest. THE SEPTEMBER GAP: the 78 live-pulled races score 0.145
against 0.076 for back-filled races, because 80% of their raced runners carry NO last-start speed rating, sectionals or
vsClass in the export (1% in back-filled races, and 1-2% in tonight's day files). The back-filled history is cleaner
than what those September runs were priced on; the current pull is complete, but any future pull without benchmarks
prices at roughly double the error. Mass by band: the model gives favourites ($1-4) 27% of the race against BSP's 32%
and roughies 8% against 5%, but a sharpening exponent fitted on any period is 0.99-1.01 (t_temp.py), rolling 8-week
recalibration 0.0839 -> 0.0839: it is not a calibration bias, it is which favourites. Hot form (30/90-day jockey,
trainer and combo BSP-gap encodings, t_hot.py): 0.0805, nothing. A stage 2 fitted only on first-starter races
(t_fsmodel.py) is worse on them (0.1077 vs 0.1046); the general model already does best. Stage-1 tree tuning:
oof_trees_tune.py (num_leaves 63, feature_fraction 0.35, learning_rate 0.03 against the live 31 / 0.2 / 0.05).
Tuning result: num_leaves 63 / min_data 50 -> 0.0954, feature_fraction 0.35 -> 0.0935, learning_rate 0.03 -> 0.0940,
all worse than the live trees (0.0932); the live settings stay. price_day3.py now refuses to price a day where more
than 10% of raced runners lack a last-start speed rating (--allow-gaps overrides).

## Track-range caveats, 6 Oct 2026 (going_range.py)

When the track call is a range ("G4 to S6"), the day is exported twice with fk-export's `going` input and priced at
both ends. going_range.py adds a short note to the top of the market sheet naming ONLY the bets the track changes:
a bet at one end only (bet it only on that track), or a stake 1u or more apart (the stake at each end). Bets the
track does not change get no note.

## Place and each-way staking, 6 Oct 2026 (t_place.py)

No place prices in the data, so the place price is ESTIMATED: Harville place chance from the opening win market,
priced at a 1.18 place-book margin (1.12 and 1.25 as sensitivity, same ranking). Holdout, live bets, at the open:

| staking (same stakes) | ROI | worst drawdown | profit/drawdown | longest run with no return |
|---|---|---|---|---|
| win only (the plan) | +64.2% | $5,215 | 29.2 | 25 |
| place only | +20.8% | $6,129 | 8.1 | 14 |
| each-way, half and half | +42.5% | $3,075 | 32.8 | 14 |
| win under $6, each-way $6+ | +50.5% | $3,075 | 39.0 | 14 |
| win under $8, each-way $8+ | +55.2% | $3,583 | 36.5 | 15 |
| win under $10, each-way $10+ | +60.0% | $3,971 | 35.9 | 16 |

Speed map and ratings do not move the real place or win rate beyond the chance already priced: leaders/on-pace
placed 96.5% of what our chance expected (market 97.5%), midfield 104.7%, back 101.4%; wins 99% / 104% / 95%.
Top-rated last start placed 92% of our expectation (market 98%). Our Harville place chance overrates favourites
(89%) and underrates longshots (151%) for places; the market's is calibrated within 3% everywhere.

Real place prices (same day): Form King's results carry `betfairPlaceDiv` (Betfair place SP) for 97% of
placegetters; `totePlace` and `toteWin` are 0 in every stored result. scripts/place_divs.py exports them. On the
1,163 live bets with a real place price, at BSP and place SP, both less 8% commission:

| staking | ROI | worst drawdown |
|---|---|---|
| win only (the plan) | +0.6% | $11,612 |
| place only | -2.6% | $12,986 |
| each-way | -1.0% | $11,575 |
| win under $8, each-way $8+ | +0.6% | $11,634 |

Place never beats win on real prices either. Bets that settle back: win -7.7%, place -10.9% (294 bets), the same
weak spot the estimate showed. Betfair place SP pays about 7% over the fair Harville place price off BSP.
