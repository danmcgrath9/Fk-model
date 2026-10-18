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

## Back-settlers, 6 Oct 2026 (t_backsettle.py)

Our value bets on horses that usually settle back (settle share 0.65+) win fewer races than our chance says:
wins/expected 0.83 (older holdout), 1.00 (newer holdout), and on the races BEFORE the holdout, priced with the
stage-1 out-of-fold chances that played no part in finding it, 0.83 (Jan-Mar) and 0.69 (Mar-May). Back is the
worst settle group in three of the four periods at BSP. Blocking them raises ROI but cuts profit at the open (they
still make money there). Shading their chance x0.85 and renormalising the race improves profit at the open AND at
BSP on both samples (holdout open +$10.1k, BSP +$2.8k; before the holdout open +$5.2k, BSP +$0.8k); x0.90 and x0.80
also improve both. Not switched on yet.

**Switched on 7 Oct 2026 (founder):** shade_back.py runs after apply_stage2f.py on every day file and multiplies a
back-settler's chance by 0.85 (p_unshaded kept in the json). Pipeline: drop_scr, price_day3, apply_stage2f,
**shade_back**, angles_day, fs_json, fu_json, paper_open / market_sheet.

## Bigger place stakes on the short bets, 6 Oct 2026 (t_place_short.py)

Win bet plus a place bet of 1x to 3x the win stake on live bets that opened under $8 (343 bets), place settled at
REAL Betfair place SP less 8%: the place part alone returns -1.3% (-2.5% on the ones that started $6 or shorter),
so every extra place unit lowers ROI and profit. Opening place prices are not in the data; the early-price edge on
places is untested.

## Rail position x speed map, 7 Oct 2026 (t_rail.py, scripts/rail_positions.py)

Founder's question: with the rail out 9m at Caulfield, should on-speed runners be worth more? 1,408 races carry a
rail (DB pulls from 30 Apr; the history files carry none). Position = Form King's predicted settling position.
Wins against what the market (BSP) expected, leaders + on pace combined: rail true 100%, out 1-4m 104%, out 5-8m 97%,
out 9m+ 88% (z -1.0). Leaders alone with the rail out win LESS than priced (75-83%). Caulfield with the rail out 9m+:
on pace 150% (11 wins from 72) but midfield 53% (3 from 82); five or six meetings per band, which is noise. Our model
tracks the market in every cell. Verdict: the market already prices the rail and the map; nothing to add. Revisit as
rail data builds up (every pull adds it).

### Map-wrong and rail as stage-2 inputs, 7 Oct 2026 (t_mapwrong.py, t_rail_halves.py)

Holdout KL to BSP (lower better): live v6 0.0800; + speed-map-wrong inputs (real settling history and its spread,
mapped vs usual position, habitual leaders in the race, mapped to lead but rarely leads, early-speed rank) 0.0802;
+ rail 0.0801. The rail only exists from 30 Apr, so it was re-tested inside that period, each half fitted and tested
on the other: v6 0.0819, + rail 0.0820, + rail + map 0.0821. Nothing gets closer to BSP. Not adopted.

## Weight-down rule re-checked, 7 Oct 2026 (t_weightdrop.py)

The bets the 2kg+ weight-drop rule blocks, settled as if taken (back-settler shade on, as live):

| sample | blocked bets | open ROI | BSP ROI | wins/expected |
|---|---|---|---|---|
| holdout (where the rule was found) | 201 | +52.2% | -18.6% | 0.86 |
| before the holdout (stage-1 out of fold) | 305 | +59.9% | +4.2% | 0.93 |

It does not replicate out of sample: before the holdout the blocked bets did BETTER than the ones we kept (+51.0% open,
-7.3% BSP). Dropping the rule adds open profit in both samples (holdout +$20.4k, before +$35.2k) and costs $7.3k at BSP
on the holdout while adding $2.5k before it. Forward runners dropping weight: holdout -43% BSP (56 bets), before +5.6%
(100 bets): no consistent effect, no new rule. Recommendation to the founder: remove the weight rule.
**Removed 7 Oct 2026 (founder: "if removing the weight rule works then go ahead, as long as we make money").** fu_json.py
no longer blocks a 2kg+ weight drop. Live from Caulfield 10 Oct (first bet it adds: R9 Changing Colours).

## By track, 7 Oct 2026 (t_tracks.py)

One model for every track; track enters through the bias inputs (track x distance x barrier / position), the horse's
track record and track speed. The plan by track type (open less 7% deductions / BSP / wins vs our expectation):
metro holdout +29% / -13% / 0.87, before +35% / -2% / 0.89; provincial & country +56% / 0% / 0.99 and +43% / -7% / 0.94;
synthetic (holdout only) +81% / +9% / 1.20. Metro is the one pattern in both samples: still profitable at the open,
but our metro chances run high. Single tracks flip between samples (Bendigo, Seymour, Echuca) except the consistent
good ones (Ballarat, Pakenham, Geelong, Wangaratta): too few bets per track for track-by-track rules.
Fixes, whole-plan profit open-less-deductions / BSP: metro needs 40c+ holdout $+153.7k / $+0.1k (now $+153.0k / $-4.1k),
before $+194.2k / $-23.8k (now $+196.7k / $-27.8k), with 137 and 189 fewer bets. Blending metro with the market or
dropping metro does worse at the open. Proposed to the founder: metro needs 40c+.
**Switched on 7 Oct 2026 (founder):** paper_open.py, market_sheet.py and race_check.py need 40c+ value at Flemington,
Caulfield, Moonee Valley and Sandown (from the prices file name), 20c+ elsewhere; the take-at price follows.
**Reverted the same day (founder: 'this makes us $700 more, surely not').** At the open, where we bet, metro 40c+ was
+$0.7k on the holdout and -$2.5k before it: no money in it. Back to 20c everywhere.

## Bets we price under $2, 8 Oct 2026 (t_under2.py)

Asked on Cranbourne R1 Kotahitanga (ours $1.91, market $2.40). Same live rules, only the $2 floor removed, open ROI:

| our price | holdout bets | open ROI | strike vs our chance | before-holdout bets | open ROI | strike vs our chance |
|---|---|---|---|---|---|---|
| under $1.60 | 9 | -15.0% | 33% vs 69% | 11 | +12.5% | 45% vs 68% |
| $1.60-$2 | 10 | +75.0% | 60% vs 57% | 40 | +48.5% | 53% vs 55% |
| $2-$3 (live) | 108 | +85.2% | 48% vs 40% | 186 | +68.9% | 39% vs 39% |

Under $1.60 the model is overconfident (wins far fewer than it says). $1.60-$2 is calibrated and profitable in both
samples, on 50 bets. Not live: a founder decision.

## Where the edge is, 8 Oct 2026 (t_edges.py, t_onlyride.py)

Live plan split by segment, holdout / before the holdout, open ROI (BSP ROI):

| holds in both samples | holdout | before |
|---|---|---|
| jockey's only ride at the meeting (114 / 171 bets) | +117% (+46%) | +88% (+21%) |
| field of 8 or fewer | +75% (+9%) | +71% (+5%) |
| barriers 1-4 (weakest; win 0.87x / 0.82x our chance) | +40% (-11%) | +34% (-17%) |
| bets that drifted from open to BSP | -34% | -33% |

Model vs the opening market on every runner (margin removed): where we rate a horse 2x+ the market's chance, a flat
1u at the open returns +95% / +88%; where we rate it under 0.6x, -64% / -66%, and those horses win about what WE said,
not what the market said. Inconsistent between samples (not acted on): 1600m+, class under 75, $15-$30, metro.

Adjusting our chance for the two consistent ones (only-ride x1.1 to x1.3, barrier 1-4 x0.85 to x0.9) moves profit by
1-3% and not in the same direction in both samples: not adopted. The only-ride horses are already our best bets; the
open question is staking them harder, not finding more of them.

## Batch of plan variants, 8 Oct 2026 (t_batch.py, t_batch2.py, t_batch3.py)

Raised BOTH profit and ROI at the open in both samples: only-ride stake x1.5/x2, field of 8 or fewer stake x1.5, cap
6u. Raised ROI but cut profit (less invested): value 40c+, barrier 1-4 stake x0.5. Worse or mixed: value 15c/25c/30c,
Kelly x50/x100 (profit moves with stake size, ROI falls at x100), price band to $10 or $20.

Proposed: only-ride x2, field<=8 x1.5 (both: x3), no bet over 8u.

| | holdout live | holdout proposed | before live | before proposed |
|---|---|---|---|---|
| profit at open | +$188,906 (+65.7%) | +$241,115 (+69.1%) | +$255,052 (+51.9%) | +$351,841 (+56.8%) |
| open less 7% | +54.1% | +57.3% | +41.3% | +45.9% |
| BSP less 8% | -1.2% | +2.7% | -5.8% | -2.6% |
| worst drawdown | $5,282 | $6,954 | $9,772 | $12,271 |

The only-ride AND small-field bets: 35 holdout bets +196% at the open, 65 before +98%.

## Dave's point-in-time sample vs our stored form, 9 Oct 2026 (scripts/archive_compare.py, fk-archive workflow)

Sample: 20-26 Aug 2026, all states, 38 meetings; the 8 VIC meetings (66 races, 625 runners) are all in our DB.

- Our stored race form for these races was pulled AFTER the race: 360 of 625 entries carry past runs dated on/after
  the race. export_dataset.py drops any past run dated on or after the race (`d >= race_date`), so those runs never
  reached the model. Not a leak.
- Values that DID move between our copy and the point-in-time copy, and that the model reads:
  race lws (63 of 66 races, typical 1.2 points, some 6-8: WNBL R1 76.6 -> 68.3), the expected rating on past runs
  (63% of runs, ~1.1), past-run sectional benchmarks (60%, ~0.4-0.7), peak12m (57%, ~0.5), race fieldStrength (all),
  entry exp (all, ~2.4). Features exposed: last_vs_lws, best_vs_lws, e_rat_minus_lws, e_expected_*, peak12_rel,
  field_strength, and the sectional vs-class features.
- Not yet known: whether the moved values make our historical prices sharper than a pre-race model could have been.
  Next test: price these 66 races from both copies and compare the chance each gave the winner.

## Clean archive vs our copy, priced (9 Oct 2026, t_archive_eval.py, scripts/archive_export.py)

20-26 Aug 2026 VIC, 66 races, 625 runners. Day files built from each copy by the same code (race_bundle +
export_dataset); a stage-1 tree model trained only on the 3,400 races before 20 Aug prices both.

| | chance given to the winner (mean) | mean log chance on winner |
|---|---|---|
| clean archive | 22.8% | -1.785 |
| our copy | 22.9% | -1.761 |
| market at BSP | 24.9% | -1.708 |

Our copy rates the winner higher by +0.025 log (62% of races, t = 1.56; losers -0.007). Prices differ between
copies by 10.4% on average. Opening prices are identical in both copies (100%), so the open we settle at is pre-race.

Betting rules on the 66 races (simplified: no first-up/first-starter blocks), at the same opening price:
clean copy 106 bets, 20 winners, +43.0% ROI; our copy 109 bets, 23 winners, +62.8%. 93 bets shared; the gap is five
winners only our copy backed (three at Bendigo 26 Aug, e.g. Tiger Fox clean $10.89 vs ours $7.20) against two only the
clean copy backed. Too small to measure the leak precisely; the edge holds on clean data. The full 15-month archive
is the test.

Archive quality (archive_quality.py, all 38 meetings): no past run on/after race day, no flucs after the start, no
ratings after the start, no par created after the race. 17% of benchmarked past runs not frozen by race time (known,
flagged by Dave). Missing: Swan Hill 21 Aug (VIC) and Strathalbyn 26 Aug (skipped, never resulted); Kununurra R7 no
winner/BSP; 15 runners without exp.

## Jockeys by price band, 9 Oct 2026 (t_jockeys.py, t_jockeys2.py)

Live-staked bets split by opening price (<$4, $4-8, $8-10, $10+) and jockey quality measured pre-race (Form King 12-month
win %, our rolling wins-vs-market jockey_ae, apprentice). Only one pattern holds in every band in both samples: bets
ridden by jockeys in the top third of jockey_ae (cut 1.10) return less than the band average (holdout +35% to +67% vs
+56% to +83%; before +14% to +61% vs +30% to +71%). They are still profitable, so cutting them costs money:

| variant | holdout profit / ROI | before profit / ROI |
|---|---|---|
| live | +$150,697 / +69.1% | +$219,900 / +56.8% |
| skip high-A/E jockeys | +$119,087 / +81.9% | +$159,419 / +67.0% |
| half stake on them | +$134,892 / +74.2% | +$189,660 / +60.7% |
| x1.5 on $10+ with a top-third 12m-win% jockey | +$157,411 / +68.7% | +$231,134 / +57.1% |

Not adopted: better ROI only by betting less, and the $10+ top-jockey boost adds a little profit with no ROI gain and
a deeper drawdown. Other cells (e.g. $4-$8 top jockeys) flip between samples.

## First time up in trip, by last-start sectionals, 10 Oct 2026 (t_stepup.py)

Step-up = today's trip 200m+ past the longest race in the last 10. A/E = winners over expected (BSP, renormalised).
Overall the market prices step-ups right (3,295 runners, A/E 1.01 vs BSP, 1.02 vs our model). Strong closers (last start's
last 600 in the top third vs class) step up a little better (1.05 BSP, 1.09 model); weak closers worse (0.85). Strong
MID-race sections do not carry (0.95). The one cell worth watching: strong closer stepping up at BSP under $8, 480 runners,
A/E 1.08 vs BSP (+8.5% flat at BSP, about 1 sd: not significant) and 1.20 vs our model (about 2 sd: the model underrates
them). Not adopted; recheck on the full archive (clean, point-in-time sectionals).

## The market blend, 12 Oct 2026 (t_blend_open.py): Benter's last step, finally tested

Holdout (1,369 races from 6 May with an open price and a BSP on every runner), stage-2 v6 refitted on the races before the
cut, blend weights cross-fitted on halves of the holdout. A logit blend of 0.82 x ours + 0.22 x the opening market:
KL to BSP 0.0801 -> 0.0765, winner log loss 1.9108 -> 1.9073, and it is CALIBRATED on its own bets (expected 307 wins,
got 310) where the live price overrates its picks (expected 368, got 342). Bets at the open under the live rules, blend
for selection and staking: 1,725 bets (was 2,071), strike 18.0% (16.5%), flat +49.5% at the open (+43.8%), -11.2% at BSP
(-9.4%). By opening-price band with the blend: $1.60-$4 47% strike, +54% open / +15% BSP; $4-$8 27%, +55% / -1%;
$8-$15 13%, +36% / -21%; $15+ 9%, +60% / -14%. So the under-$8 book (565 bets) is 31% strike, +55% at the open and
about break-even at BSP; $8-$15 is the weakest band on both measures. Caveat as before: back-filled opening prices may
be softer than a live open, so the open-price ROI is an upper bound; the KL and calibration gains do not depend on it.

## Rating of the day, 12 Oct 2026 (t_dayrank.py), founder's idea: NOT ADOPTED, and where the gap really is
Each past run ranked against every run we hold from its meeting (and its whole day), raw and weight-for-age rating:
last run, best of last three, top-3-of-the-meeting count in the last five, plus the same times a young-horse flag
(age 3 or under, or 5 starts or fewer). 92% of runners have a ranked last run. Holdout KL to BSP (lower is better):
live v6 0.0817, + rating of the day 0.0815, + young weighting 0.0815. Young-horse races (median age 3 or under,
368 races): 0.0928, 0.0923, 0.0924. Too small to separate from noise, so not adopted. Likely why: Form King already
hands the model the day's context (vsAllAvg, vsTrack, raceRating, track_speed), so the rank adds little on top.
THE FINDING THAT MATTERS: young-horse races are where we are weakest, and it is ours, not the race type. The opening
market is only 3% worse on them (KL 0.1426 vs 0.1382, races with every open held), we are 13% worse (0.0928 vs
0.0817). Trials would be the obvious young-horse form, and they cannot be used: trial runs carry no rating and no
sectional in our data (40,964 trial cells, 0 rated). That is the next thing to fix, not another rating transform.
Follow-up the same night (founder: "wouldn't we want to be careful with those races"): NO. Holdout bets under the live
rules (blend, full stakes, at the open): young-horse races 480 bets, 19% strike, +64% on stakes; older-horse races
1,245 bets, 17%, +63%. Young or lightly raced RUNNERS return less (+57% vs +71%) and the $15+ young-race bucket is the
weakest (137 bets, 9 won, +44% staked, -30% flat at BSP) but every slice is profitable at the open, so no rule added.
The model is less accurate on young horses, and so is the opening price, so the value gap is still there.

## From the Form King Slack, 13 Oct 2026 (#api, #bugs)
- LWS bug (Dave, 25 Sep): the API's Likely Winning Standard used the past run's weight-vs-WFA difference instead of
  today's, so LWS pulled since July was wrong in many races. Nine model inputs read LWS (last_vs_lws, best_vs_lws,
  e_rat_minus_lws and its race aggregates, c_lws, x_class_change). Our 9 Oct archive check had SEEN this (LWS moved in
  63 of 66 races, e.g. WNBL R1 76.6 -> 68.3) and filed it as point-in-time drift; it was this bug. Training data pulled
  July to 24 Sep carries the wrong LWS, live pulls since carry the right one. The clean export fixes it: retrain on it.
- Bad auto-reviewed ratings 3-5 Oct (field strengths -1.4L to -40.3L, e.g. Salamanca Six's Bendigo maiden win at
  -39.8, Seymour 11 Oct R6), a few lingering to 12 Oct. Checked: Kilmore 13 Oct and Caulfield 14 Oct inputs have no
  past race rated under 40; the training set's 22 under 40 are all older runs. Seymour 11 Oct inputs no longer on disk.
- 5,000 free top-up credits to every active API user (13 Oct) to re-pull 1 Oct to now, once Dave confirms the fixes.
- API v1.1.0 (8 Oct): point-in-time integrity for lws and exp; Dave says the fixes back to 1 Jul 2025 are live on the
  API as well as in the export, so a model trained on the export and priced off live pulls sees the same form.
- How much the LWS bug moves OUR prices (13 Oct, Caulfield 14 Oct G4 inputs re-priced through the live pipeline with
  every race's LWS shifted): +/-1.2 points (the typical bug size) moves runners under $15 by 0.1% median, 0.5% at most;
  +/-6 points (the worst seen) by 0.4% median, 1.5% at most. LWS is a race-level figure, so a shift mostly cancels when
  the race is renormalised to 100%. No emergency retrain: the clean export fixes it with the duplicates and ratings.

## When to bet: the timing study, 13 Oct 2026 (founder: "when is the best time to place a bet, when is the last available")
Two samples. HOLDOUT (1,413 races, open + BSP, blended price): value-at-open bets under the live rules, 1,725 bets,
+50% flat at the open and -11% at BSP; split by what the price did by the jump: firmed 20%+ (1,102 bets) +85% at the
open, firmed 5-20% +34%, held within 5% -36%, drifted 5-25% -50%, drifted 25%+ -27%. Bets NOT value at the open that
became value only by drifting (the "it has drifted, now it's value" bet), taken at BSP: 1,902 bets, -16% flat, -13%
staked. TIMED PATHS (scripts/fluc_timing.py, 82 races 3-11 Oct, 83 value-at-open bets on the live model's own prices):
markets open a median 66h before the jump; share of value bets still at or over take-at: 54% 20 min after the open
(nearly half gone in the first 20 minutes, the TAB-first move), 52-55% from 1h to 12h after, 47% at 24h, 26% six hours
before the jump, 17-25% in the last 3h. Runners that firm 20%+ have done 12% of it 20 min after the open, 42% by 24h
after, 83% six hours before the jump. Bets still on 12h after the open: not drifted (20) firmed 10%+ by the jump 75%,
drifted 5%+ (21) firmed 67% and kept drifting 19% (vs 5%): drift raises the risk but most still firm; 21 bets is too
few for a rule. The live rule already refuses the drift-made bet (value is judged at the open).
- SCRATCHINGS AT THE OPEN (Dave's question, 13 Oct; the founder had asked for it earlier and it was not done until now).
  The open market included runners later scratched, so starters' open prices sit higher than a final-field market and
  real open bets take deductions. Holdout, 1,369 races with every open: starters-only open book % by field size: 2-6
  runners median 104% (10th pct 54%), 7-9 110%, 10-12 123%, 13+ 124%. Value-at-open bets by the race's book %: lowest
  third (most likely scratchings) +40% flat, middle +45%, highest (full market) +68%. With a crude deduction (a race
  below its field size's median book has every starter's winnings scaled by book/median; Dave's renormalise-and-restore
  idea) 1,145 bets +55% flat, +62% staked; harsh version (deduct against the 90th-percentile book) 824 bets +51% flat,
  +52% staked, against +51% / +65% unadjusted. Scratchings are not what makes the open look good. Still to do: real
  deductions in the shadow book, which needs the opening price of every runner that is later scratched.
- Late-taken bets SETTLED (timed sample, 74 value-at-open bets with results, 15 winners): taken at the open +41%; still
  at or over take-at and NOT drifted past the open: 20 min after +14% (32 bets), 1h +77% (17), 12h +75% (19), 24h +35%
  (24), race day 6h before +37% (9); DRIFTED 5%+ but still over take-at: 20 min +34% (17), 1h +4% (26), 12h +13% (19),
  24h 0% (10), race day 0 winners from 17. Tiny samples (one $10 winner moves a cell by 40 points); direction agrees with
  the holdout (drift-made value -13% staked on 1,902 bets) and with Law & Peel 2002 (shortening prices profitable only
  when the shortening carries information).
- WRONG, kept as a record (corrected below): REAL DEDUCTIONS, same day (scripts/scratch_opens.py: every resulted VIC race since 1 Jul 2025, 4,013 races, 829
  scratched runners, 199 with an opening price, i.e. scratched after the market opened). Holdout value-at-open bets
  re-settled with the deduction a fixed-odds bet actually takes (about 0.95 / the scratched runner's last price, the
  TAB schedule's shape, summed per race, applied to the winnings): 1,725 bets +49.5% flat / +63.5% staked before,
  +47.2% / +59.3% after. Only 81 bets (5%) sat in a race with a scratching after the open (average deduction 43c);
  those 81 go from +26% to -24% flat. Caveat: the extract may not hold every scratched runner (0.2 per race is low),
  so this is a floor on the effect, not a ceiling. Shadow-book and forward-test settlement to apply it from now.
- CORRECTION, same day (founder: "This doesn't sound right at all"). The stored race records hold most scratchings
  for recent meetings (142 in 48 races) but only 23 of them still carry a price, and older records hold few scratched
  runners at all, so the +59% above settled almost every bet with no deduction. Measured instead from our own saved
  price files taken before the scratchings (7 meetings, 63 races, 6-11 Oct): 87 runners priced in the earlier file
  were scratched later; 50 of 69 value-at-open bets (72%) were in a race with a later scratching; deduction per bet
  mean 15.9c, median 12c, max 51c (0.95 / the scratched runner's earlier price, summed per race; the earlier files
  were taken hours after the open, so this misses scratchings in between and is a floor). Holdout value-at-open bets
  with that deduction on the winnings: none +50% flat / +64% staked; 12c +34% / +47%; 15.9c +29% / +41%; 20c +23%
  / +36%; 25c +17% / +29%. The open is still profitable after deductions, but about a third less than the backtest
  said, and a bet placed after the scratchings takes no deduction, which narrows the gap to a later price.
- LATE BETS WITH DEDUCTIONS (founder: "is betting 24 hours after the open still profitable, or race morning?"). Timed
  sample, 74 value-at-open bets with results, deduction per race measured from the saved earlier price files (58 bets)
  or the 15.9c average: taken at the open (deductions) +20% (74 bets); 24h after the open, still at or over take-at
  (deductions still apply, scratchings come on race morning) +3% (34 bets), not drifted +5% (24); race morning 6h
  before the jump (after scratchings, no deduction) -23% (16), not drifted +37% (9); 1h before +17% (14). The 24h bet
  is about break-even after deductions; race morning is too few bets to call. Bounds from the holdout: the open after
  a 16c deduction +29% flat, BSP (no deduction) -11% flat. This overturns the earlier "still fine 24h after the open"
  (that was settled without deductions). The proper answer needs timed prices on a large sample: Dave's export.

## Where the value is, 13 Oct 2026 (t_segments_open.py): value-at-open bets by segment, two samples, after deductions
HOLD = holdout (1,349 bets with every open and a BSP), OLD = the races before it, stage-1 out-of-fold blended with the
open the same way (3,148 bets). Flat ROI at the open after the measured 16c average deduction, HOLD / OLD; in brackets
the median BSP/open (under 1 = the market firmed after the open, i.e. the open underrated the horse).
ALL +28% / +24% (0.69 / 0.75). HOLDS IN BOTH, strongest to weakest:
- edge at the open 70%+: +59-60% / +35-90% (0.43-0.61): the bigger the edge, the better, and the more the open is wrong.
  Edge 20-40%: +17% / +11% (0.80 / 0.85).
- jockey's only ride +45% / +34%; open 2nd-3rd favourite +56% / +33%; open favourite +36% / +20%.
- country +39% / +31% and provincial +30% / +25% against metro +8% / +13% (metro opens firm least: 0.76 / 0.77).
- midweek +35% / +28% against Saturday +14% / +12% (Saturday 0.74 / 0.82).
- racing fit (under 70 days) +36% / +27% against first up +6% / +20%.
- barrier 1-4 weakest of the barriers +2% / +12%; open 4th-6th in the market +0% / +15%; open $12+ +13% / +19%.
INCONSISTENT between samples (not acted on): field size (8 or fewer +18% / +42%), 1801m+ (-3% / +31%), going (the
holdout is mostly wet), age. Every consistent segment is still positive after deductions, so nothing is cut; the
deduction is a flat 16c here and really varies by race.

## Do the early bettors miss the sectionals? 13 Oct 2026 (founder: "does the first 24h miss the big mid-race sectionals
## but the late bettors get it"). All runners in races with every open and BSP (36,087), last start's section vs class
## benchmark, actual wins against the opening market's chance and BSP's chance (A/E, 1.00 = priced right):
- LATE section (400 to finish), top 15%: A/E 1.12 vs the open, 1.04 vs BSP. Holds in every open price band ($1-4
  1.08/0.99, $4-8 1.13/1.07, $8-15 1.18/1.11, $15+ 1.05/1.01) and in both periods (holdout 1.10/1.04, earlier
  1.12/1.04). The early market underrates last-start closers; the late money fixes about two thirds of it.
  Bottom-15% closers: 0.88 vs the open, 0.93 vs BSP (overrated early).
- MID-RACE (800 to 400), top 15%: 0.94 / 0.94, no early-vs-late gap. Big mid-race then finished 5th or worse: 0.80 /
  0.84, overrated by BOTH markets (the "it ran a big middle section" story is priced in, and then some).
- EARLY section top 15%: 0.95 / 0.93, slightly overrated by both.
So the early market misses the closing sectionals, not the mid-race ones.

## The bounce block at the OPEN, 13 Oct 2026 (it was only ever tested at BSP)
Value-at-open bets whose last start was a new career-best rating by 3+ points, against the rest; flat at the open,
after the 16c deduction, and at BSP. HOLD: bounce 146 bets +24% / +7% / -15%, rest 1,203 +52% / +31% / -12%.
OLD: bounce 205 bets +61% / +39% / +3%, rest 2,943 +43% / +23% / -8%. Inconsistent between samples and profitable at
the open in both, so the BSP-tested block does not carry over to betting at the open. (Founder query: Regal Ambition,
Thousand Guineas, was blocked by it, not by the first-up rule as the take-at list mislabelled it.)
- Bounce block REMOVED from fu_json.py (13 Oct 2026, founder: "just want to have the best model possible to bet").
  The first-up block (resuming 60+ days 200m+ short, or off a bottom-half trial) was re-tested at the open the same
  day and HOLDS: HOLD 92 bets -1% at the open / -15% after deductions / -42% BSP, rest +53% / +32%; OLD 251 bets
  -11% / -23% / -38%, rest +49% / +28%. Kept.

## Is BSP sharp? 13 Oct 2026 (t_bsp_sharp.py; founder: "test if BSP is actually sharp and where the edges are")
36,239 runners in 3,693 races with every BSP; median BSP book 100.4%; two halves by date (split 29 Mar 2026).
A/E vs BSP (1.00 = priced right): ALL 1.00 / 1.00. Flat 1u on everyone at BSP: -5% / -8% gross, -12% / -14% after 8%.
Small, consistent leans: BSP favourite 1.02 / 1.01, 2nd-3rd in the BSP market 1.05 / 1.04 (+5% / +3% gross, -2% / -4%
after 8% commission); 4th and out 0.93 / 0.96; last-start top-15% closers 1.04 / 1.05, bottom-15% 0.93 / 0.94;
barriers 1-4 0.98 / 0.97. Nothing clears an 8% commission in both halves.
OUR MODEL AGAINST BSP (our chance / BSP's chance, holdout live model and earlier out-of-fold): where we rate a horse
1.6-2.5x BSP, it wins 0.88 / 0.93 of what BSP says and 0.46 / 0.49 of what we say; where we rate it under 0.6x BSP it
wins 1.04 / 1.02 of BSP and 2.17 / 2.13 of ours. When the model and BSP disagree, BSP is right. Our edge is that the
OPEN is soft (the model beats the open, KL 0.100 vs 0.152), not that the model beats BSP; BSP has the late money,
the scratchings and the day's track, which no form model sees.
- LIVE prices against the open and BSP, 5-11 Oct 2026 (42 races where every runner had the live model price, a
  Form King open and a BSP): KL to BSP open 0.142, live model 0.092, live model blended with the open 0.086. Winner
  log loss: open 1.871, live model 1.826, blend 1.814, BSP 1.789. The blend closes about 70% of the gap between
  the opening market and BSP at picking winners (model alone about 55%); BSP is still the best price there is.

## What makes our value bets drift? 13 Oct 2026 (t_drift_why.py)
Value-at-open bets, HOLD 1,349 / OLD 3,148; DRIFT = BSP 1.25x+ the open (9% / 14% of our bets), FIRM = BSP 0.8x or
less (66% / 56%). Groups where (drift rate - firm rate) is 2.5+ points off our average in the same direction in both
samples, with flat ROI at the open after a 16c deduction:
MORE DRIFT: edge only 20-40% (drift 15% / 18%, firm 50% / 44%, ROI +17% / +11%); low Neural rating (+32% / +25%);
few career starts (+19% / +24%); early in the preparation (+20% / +20%); best rating BELOW today's standard (+26% / +21%).
LESS DRIFT: edge 100%+ (drift 1% / 6%, firm 91% / 81%, +60% / +90%); best rating ABOVE today's standard (+59% / +40%);
experienced (+35% / +34%); ran recently (+28% / +31%); on-pace types (+50% / +28%).
Reading: the market drifts the bets whose case is uncertainty (lightly raced, unproven at the level, small edge) and
firms the ones whose case is proven ability (rated above today's standard, fit, experienced, big edge). Every group is
still profitable at the open after deductions, so nothing is excluded; it says which bets to be on first.

## BetMatic-style orders, tested (13 Oct 2026, t_betmatic.py; founder: "why haven't we done a test on this method?")
An order sent before the market exists carries a minimum odds from our chance alone, (1.2 / p_model^0.82)^(1/0.78)
(the blend without the per-race rescale), fires if the open is at or over it, and carries one stake. Against the sheet
(exact blend at the open), flat ROI after the 16c deduction, profit at $100 a unit:
- HOLD: sheet 1,378 bets +30.4% flat, +45.8% staked, +1,014u. Orders at the raw minimum: 1,068 bets +35.1%, miss 386
  of the sheet's bets and add 76; fixed stake +482u, stake by price (ladder) +824u. Minimum shaded 5%: 1,245 bets
  +34.7%, miss 220, add 87; fixed +534u, ladder +893u (88% of the sheet). Shaded 10%: misses 100 but adds 185 and the
  flat ROI falls to +28.7%.
- OLD: sheet 3,148 bets +24.2%, +1,844u; shaded 5%: 2,822 bets +29.1%, fixed +1,026u, ladder +1,828u (99%).
Reading: the formula is stricter than the exact blend, so the orders take fewer bets at a higher ROI; shading the
minimum 5% recovers most of the missed ones without letting weak ones in. The stake matters more than the price: one
fixed stake (set at the minimum odds) earns about 55-60% of what staking by the price got does, because the best
overlays open well above their minimum. If BetMatic cannot take a stake that scales with price, send each horse as
two or three orders at rising minimum odds (each its own slice of the stake). Assumes every fill is at Form King's
average open, with no bookmaker limits.

## BetMatic staking: getting closer to the sheet's stake (14 Oct 2026, t_betmatic_tiers.py; founder: "we wanted to be 8.6 invested but on the BetMatic theory we have less")
Holdout, orders at the 5%-shaded minimum, the stake a ladder of orders at rising prices: 3 steps (x1, x1.25, x1.5) each
sized at its own price staked 1,366u for +679u (+49.7%); sized at the NEXT step's price 1,758u, +801u (+45.6%); 8 steps
(x1 to x2) sized at the next step 1,691u, +801u (+47.4%). The sheet (exact stake at the real open) is 2,214u, +1,014u
(+45.8%); a stake that follows the price exactly (if BetMatic offers one) is +893u (t_betmatic.py). Checking the $15 band
on the blended price at the order's own price instead of the model price drops a profitable class of long ones (-40u),
so it stays on the model price. betmatic_orders.py now uses the 8 steps sized at the next step.

## Bet at the open, top up after scratchings? (14 Oct 2026, t_topup.py; founder: "Bet at opening. Adjust our market after scratchings and we can top up bets")
Stage 1: the BetMatic orders at the open (16c deduction). Stage 2: our market re-priced on the final field; every
value-at-open bet topped up to the full sheet stake at the later price if that price is still at or over take-at (and
missed value-at-open bets struck in full the same way), no deduction. The stage-2 slice on its own: holdout, later price
Betfair SP less 8%: 266 bets, -7.6%; older races: 875 bets, -18.4%; live timed sample (52 races, corporate fluc 6h before
the jump): 13 bets, -75%. Adding the top-up takes the holdout from +803u to +788u and the older races from +1,569u to
+1,455u. A bet still over take-at after the scratchings is mostly one the market drifted (the drift finding again); the
ones we would want more of have firmed past take-at by then. Not a top-up rule. Limit: the datasets hold final fields
only, so the moment scratchings shorten our price before the market moves is not simulated; the saved race-morning price
files (from 14 Oct) will allow a proper test after a few weeks.
- Timed replay (t_topup_timed.py, 41 resulted races since 3 Oct with timed flucs and live model prices; the field before
  the scratchings rebuilt by putting the scratched runners' share of the opening market back; the real price at 9:30am
  race day): orders at the open 31 bets, 4 won, +37.5% staked; with the 9:30am top-up 37 bets, +28.5%; the top-up slice
  alone 6 bets, 2 won, -27% (one 3.75u top-up that ran 2nd decides it). Same direction as the backtest, far too small to
  settle. Tracked live from 14 Oct (topup.py, betmatic-book.md).

## Month by month with expenses, and a stricter edge on long ones (14 Oct 2026, t_monthly.py)
BetMatic orders (8 steps, 5% shade, 16c deduction), $100 a unit, less $359 a month (BetMatic $199 + Form King $160).
Holdout (live model): Jun +$14,849, Jul +$15,950, Aug +$33,545, Sep +$7,840 (129 races held), Oct to the 9th +$6,111;
total +$78,295 net on $169,106 staked (+47%), worst drawdown 48u ($4,764), no losing month. Earlier races (out-of-fold
stage 1, Oct 2025 to May 2026): every month positive, +18% to +67%, total +$153,154 net, worst drawdown 66u.
Long ones ($8-15 on our price) are the thin slice: holdout +19u on 456 bets, earlier +293u on 970. Requiring a 40% edge
on them instead of 20%: holdout 1,033 bets +813u (+51.1%) vs 1,245 bets +801u (+47.4%); earlier 2,359 bets +1,578u
vs 2,822 bets +1,564u. Same profit on 17% fewer bets in both samples. 30% and 50% land in the same place.

## Forward test, BetMatic method only (14 Oct 2026, fwd_betmatic.py; founder: "Forward test I only want the model that we would be using with betmatic")
5-13 Oct, 9 meetings, orders rebuilt from each meeting's first priced file and filled at the first saved open: 32 horses,
7 won, 32.61u, +26.28u (+81%), 23/32 opened above BSP. Using each meeting's LAST pre-race price file instead: 36 horses,
the same 7 winners, +20.06u (+55%): the result does not hang on which price file is used. From 14 Oct the test reads the
real pre-open order file instead of rebuilding it (the first priced Warrnambool file still held an emergency and would
have filled Endless Fury at $6 against the real order's $6.02); with that, 14 and 15 Oct match the BetMatic book bet for bet.
3 fills opened past 3x our price (-3.97u): order files now carry max_odds.

## A member who gets the tip after the open (14 Oct 2026, t_follower.py; founder: "run a test of 2 minutes after opening, 5, 10 and 20 minutes")
41 resulted races with timed Form King flucs (Form King's average across the corporate books, so an average book, not
the best one; no bookmaker count in the data) and the live model's prices. On the runners our BetMatic orders got at the
open, the average price stood at x0.927 of the open after 2 minutes, x0.901 after 5, x0.874 after 10, x0.823 after 20
(median 3 price moves in the first 10 minutes). The same orders still clearing their minimum: 29 bets at the open,
27 at +2, 25 at +5, 21 at +10, 21 at +20. Profit by time on this sample swings on single winners (3-4 per row) and
says nothing; the price decay is the result. Applied to the holdout's +47% staked at the open, (1.47 x ratio) - 1 gives
roughly +36% at 2 minutes, +32% at 5, +28% at 10, +21% at 20, before the member's own fill and limits. Re-run on the
historical export's timed flucs (back to July 2025) when it arrives.

## Is live tracking the backtest? (14 Oct 2026, t_vol.py; founder: "are we sure we are tracking toward back test")
Holdout with every live rule applied (no first starters, the first-starter race rule, first-up/bounce blocks, EARLY
runners $8 or shorter, 3 steps): 0.80 bets a race, 1.14u staked a race, +0.68u a race (+60%); without the rules
1.13 bets a race. Live, the six meetings 11-17 Oct (51 races): 0.90 value-at-open runners a race before the rules
(80% of the backtest's 1.13), 0.55 bets a race after them (69% of 0.80). The back-settler shade is not the cause
(46 fires with it, 47 without). About two standard deviations short on 51 races: watch it, not yet a finding.
Forward test 5-13 Oct: +24.66u on 79 races (0.31u a race against the backtest's 0.68u), on 7 winners.
Why live runs light (same day, t_margin.py): the opening BOOK. The holdout's recorded opens sum to a median 1.19 per
race; the live first snapshots run 1.18-1.32 (Seymour 1.31, Kilmore 1.18, Caulfield Wed 1.25, Warrnambool 1.32,
Cranbourne 1.32, Caulfield Sat 1.25). Same number of candidates a race (5.2 holdout, 5.3 live) and the same spread of
disagreement with the market (sd of log open/ours 0.448 vs 0.438), but live opens sit about 4% shorter against our
prices (median open/ours 0.965 vs 0.928), so fewer clear the minimum (21.7% vs 17.2% of candidates). Shortening the
holdout's opens until each race's book is 1.25 (crude: margin spread evenly, where bookmakers load longshots): 0.66
bets a race, +39% staked, +368u (against 1.13, +46%, +801u). The ROI a bet holds; the number of bets is what the
bigger live margin costs. Live sits between the two: plan on roughly 60-80% of the backtest's bets and profit.

## t_overlap.py: why the forward test stakes a quarter of the backtest (14 Oct 2026)
Same 50 races (5-9 Oct, in both the backtest data and the forward test), inputs swapped one at a time. The opening
prices are identical (the backtest's 'open' is Form King's open), so the market is not the cause. The cause is the model
file: the 5-9 Oct files were priced before final fields, so 11.0 runners a race against 10.3 that ran, and the horses
that ran held only 0.81-0.90 of the probability; every starter's price came out about 15% too long. Backtest model:
49 bets, 73.4u (1.47u a race). Live files as made: 41 bets, 56.4u. Live files re-spread over the runners that ran:
67 bets, 97.9u (1.96u a race); with every live rule 39 bets, 50.5u (1.01u a race), +48.7u, against the forward test's
24.8u and +22.9u on the same meetings. The live rules remove 25u of turnover with about 0u of profit on these races.
Files from 14 Oct are priced on final fields (probabilities of the runners left total 1.00 at Caulfield 14, Warrnambool,
Cranbourne 16; 0.996 at Caulfield 17), so this is already fixed going forward. Caveat: re-spreading over the runners
that ran also uses late scratchings, which a pre-open order cannot know.

## The races the models never trained on (14-15 Oct 2026, mk_newraces.py, t_new75.py)
Form King's history starts 1 Jul 2025 (an earlier date answers HTTP 400 "Date is earlier than the minimum allowed
meeting date"). Backfilled 14 Oct for about 3,330 credits: 1 Jul to 7 Oct 2025, 1-11 Sep 2026 and 2 Oct 2026, 1,147
resulted races. Priced through the live day pipeline on the final field (price_day3 -> apply_stage2f -> shade_back,
1% of raced runners missing a last-start speed rating), then the BetMatic live-rules backtest. Jul to 7 Oct 2025:
1,033 races, 885 bets, 128 won, +20.7% on turnover (Jul +3%, Aug +26%, Sep +18%, Oct 1-7 +82%), against +60% on the
holdout with the same rules. Those races precede the dataset, so the rolling jockey/trainer/horse encodings built from
our own history are empty for them; that may understate the method. Sep and Oct 2026 additions (with history):
121 bets, +13.4% (Sep -2% on 110 bets). Plan on +20% to +45% on turnover, not +60%.
Why (t_newgap.py, KL to BSP, ours / opening market / our margin): Jul 2025 0.107 / 0.117 / +0.010, Aug 0.091 / 0.107 /
+0.015, Sep 0.096 / 0.113 / +0.017; holdout 0.082 / 0.142 / +0.060; Sep-Oct 2026 additions 0.078 / 0.153 / +0.075.
Our price is somewhat weaker on the 2025 races (the missing own-history encodings), but the bigger change is the
OPENING PRICE: in the 2025 data it sits far closer to BSP than in the holdout, so there is a quarter of the edge to
take. Whether 2025 opens were genuinely sharper or Form King's avgOpen for older races is a different quantity is
not known; the live forward test's fills beat BSP by 1.67x on average, which looks like the holdout, not 2025.
Against WINNERS (t_winners.py, log loss, lower = better): holdout ours 1.896, opening market 1.957, BSP 1.800; Jul to
7 Oct 2025 ours 1.898, open 1.919, BSP 1.822. Our price picks winners equally well in both periods (and is well
calibrated in every price band); what changed is the 2025 opening market, 1.919 against 1.957, so the gap we bet
into was much smaller. BSP beats us on winners in both: it carries every late move, which is the point of betting
at the open, before the market finds out.
More history helps (t_more_data.py, stage-1 trees, all9 settings, 2 seeds, holdout of 1,231 races from 3 Jun): trained
on 8 Oct 2025 to 2 Jun 2026 (2,603 races) KL 0.0958, log loss 1.9049; with 1 Jul to 7 Oct 2025 added (3,636 races)
KL 0.0937, log loss 1.9033 (open 0.1429 / 1.9478). The next daily retrain's challenger trains on them.
Where the live price is still furthest from BSP (t_gap_now.py, holdout, ours / open): 2+ first starters 0.138 / 0.189,
one 0.103 / 0.164, none 0.075 / 0.135; sprints to 1200m 0.093 / 0.153, 1700-2000m 0.062 / 0.126; metro 0.065 /
0.097, non-metro 0.086 / 0.152; fields 14+ 0.090, up to 7 0.073.
Gear (15 Oct 2026, founder asked): IS in the model, from Form King's gearChanges on each entry: blinkers_first,
gear_first_time, gear_changes (export_dataset.py). Holdout: runners with first-time gear 2,282, our average chance 9.2%,
BSP's 9.1%, won 8.9%; first-time blinkers 670, ours 9.0%, BSP 9.0%, won 8.1%. The market does not move on gear in a way
our price misses. Not in: which item (tongue tie, nose roll, lugging bit), gear coming OFF, and the horse's gear in past
runs (past-run rows carry no gear), so "raced well in blinkers before" cannot be learnt yet.
Gear detail trial (15 Oct 2026, t_gear.py, stage-1 trees, 2 seeds, trained before 3 Jun 2026, holdout 1,231 races):
F9 KL 0.0937 / log loss 1.9033; F9 + gear detail (per item worn, on first time, off; counts on, off, on again; and from
the horse's earlier races in our data: gear last start, same as last start, rating with vs without each key item)
KL 0.0930 / log loss 1.8996. Keep. Blinkers worn ranks 65th of 817 inputs by gain. Next: build it from each past
run's own gear field (Form King sends it) instead of joining our races, for full coverage, and fix the FIRST bug in
export_dataset.py in the same change.
Unread fields, group by group (15 Oct 2026, t_wide.py over scripts/wide_table.py, stage-1 trees, 2 seeds, holdout from
3 Jun 2026), KL to BSP / log loss vs winners: current F9 0.0937 / 1.9033; + past-run price flucs (last start move,
first fluc, mean move and times backed over the last 5) 0.0923 / 1.9015, KEEP; + past-run gear from Form King's own
field 0.0938 / 1.9042, no help (the gain in t_gear.py is today's gear detail); + position at 1200m, spell, night
meetings 0.0934 / 1.9048, mixed, drop; + age in days, foal month, home track 0.0934 / 1.9056, mixed, drop; all four
0.0923 / 1.9027. Race-review comments not tested (only in recently pulled races) and dropped by the founder as
subjective; acceptances never populated.
The market clock (15 Oct 2026, t_market_clock.py, the 40 races in fluc_timing.py's sample with every runner priced at
every point), KL to BSP / log loss vs winners: our price 0.103 / 1.658; open 0.161 / 1.740; +2 min 0.152; +5 min 0.145;
+10 min 0.144; +20 min 0.136; +1 hour 0.118; +4 hours 0.108; +12 hours 0.112; 3 hours before the jump 0.069; 1 hour
before 0.054; last fluc 0.041. Our price is about where the market stands 4 to 12 hours after the open; the market
only passes us on race day.
Combined (t_combo.py, 3 seeds, same holdout): F9 0.0929 / 1.9043; + gear detail 0.0920 / 1.8995; + past price flucs
0.0915 / 1.9000; + both 0.0912 / 1.8991 (1.8% closer to BSP than F9, 0.27% lower log loss). Both go into the next
challenger.
Rail x track x run style, 15 Oct 2026 (rails for 4,750 of 4,858 races from scripts/race_rails.py; table in
data/live_bets/rail-bias.md). Actual leaders win 154% of what the open implied on a true rail and 129% with the rail out
9m+; by Form King's predicted position (known before the race), rail out 9m+ (396 races): mapped on pace 82% of the
open, midfield 112%. As a model input (t_rail_feat.py: rolling earlier-meetings-only A/E by track x rail band x mapped
style, rail band x style, track x rail band x barrier, plus rail metres; 3 seeds): KL 0.0929 -> 0.0929, log loss
1.9043 -> 1.9033. No gain; not adopted (same verdict as 7 Oct, now on 3x the races). As a betting rule (t_rail_bets.py):
our own bets with the rail out 9m+ on runners mapped on pace returned +40% in the holdout (16 bets) and +40% earlier
(33 bets), so the model already avoids the ones that matter; no rule.

## Challenger inputs v10 (15 Oct 2026)
scripts/export_dataset.py now exports 40 more columns (gd_* gear detail with Form King's real change codes, fl_* past-run
price moves), and feats.build takes every exported column, so they reach training and day pricing by the same path.
F9_names.txt / F7_names.txt are the v10 lists (809 / 769 + trials + sections); nothing else in the input list changed.
Check on the new export (t_v10_check.py, 3 seeds, holdout from 3 Jun): without the new columns KL 0.0929 / log loss
1.9043, with them 0.0916 / 1.9027. (The trial's 0.0912 / 1.8991 also had gear from the horse's earlier races joined from
our own data; not in v10 because a live day export cannot do that join yet.)
THE LIVE MODEL IS STILL v9: day pricing runs from the scratch model directory with the v9 name lists and the v9
training set. On promotion of a v10 challenger, copy F9_names.txt and F7_names.txt from here and model_ds.npz from the
models branch together with the models, or price_day3.py's name check stops the pricing (by design).

## v10 inputs on profit (15 Oct 2026, t_v10_profit.py)
Stage-1 trees, 3 seeds each, trained before 3 Jun 2026, races from 3 Jun under the live BetMatic rules (3 steps, 5% shade,
3x ceiling, $1.60-$15, 16c deduction) at Form King's open:
| inputs | KL to BSP | bets | winners | staked | profit | ROI |
|---|---|---|---|---|---|---|
| v9 (live inputs) | 0.0928 | 1419 | 234 | 1988.4u | +618.3u | +31.1% |
| v10 (+ gear detail, price moves) | 0.0916 | 1421 | 241 | 1999.3u | +711.8u | +35.6% |
+93.5u (+15%) on almost the same bets; 7 more winners. One sample and stage 1 only (the live price is the blend plus
stage 2), so the size is indicative; the direction agrees with the KL and log-loss checks.

## v10 LIVE (15 Oct 2026, founder: "lets send this model live then")
The challenger retrained 15 Oct (models branch 9d6fdfc, trained through 14 Oct, 4,875 races, 809 inputs, holdout KL
0.0792) is now the day pricer, starting with Bendigo Sat 17 Oct. The v9 files are kept beside it (scratch model_v9) to
switch back. Profit backtest behind the decision: t_v10_profit.py (+618u -> +712u on the holdout, same rules). The
models branch root still holds the v9 "live" copy; promote there with the next fk-retrain promote=yes run.

## A smaller edge on short-priced horses (16 Oct 2026, t_short_edge.py; founder: "why do we never bet sub $4 horses")
We do bet them: on the holdout (1,231 races from 3 Jun, v10, live BetMatic rules at the open) runners we price under $4
are the best part of the book (under $3: 157 bets, +35%; $3-$4: 175 bets, +62%; $4 and over +25%), and 84 bets filled
at an opening price under $4. What blocks a short one is the edge: at 1.2 a horse we price $3.33 needs $4.26 at the open.
Lowering the edge for runners we price under $4 only: 1.15 adds 49 runners (19 won, +29% flat, total +712u -> +735u);
1.10 adds 56 more that lose (-19% flat, total +703u); 1.05 and 1.00 add break-even to losing runners. So the extra
edge is earning its keep below 1.15, and 1.15 itself is a 49-bet gain inside the noise of one holdout. Not changed.
By the MARKET's opening price instead (founder: "Not we price the market does"): the edge applied when the open is
under $4. Live (1.2): 20 bets opened under $3 (+8%), 64 opened $3-$4 (+42%), 1,337 opened $4+ (+36%). Lowering the edge
helps only in the $3-$4 band: at 1.05 it holds 120 bets at +38% (+26u more than live); under $3 every setting is about
break-even (+0.4u to +5.5u). Buildable as one extra order per runner with max odds $4 (fires only when TAB opens under $4).

## Stake rules head to head (18 Oct 2026, t_stakes.py; founder: "surely there can be max bets without stupid rules, can we test everything?")
Same bets as live (v10, BetMatic rules at the open, edge 1.2), only the stake function changes. Units at $100.

| stake rule | holdout profit | ROI | worst drawdown | 4.5u+ bets | earlier races profit | ROI | drawdown |
|---|---|---|---|---|---|---|---|
| live (cap 4, x2 only ride, x1.5 field<=8, x5/8) | +711u | +35.6% | 62u | 15 | +3,708u | +60.3% | 43u |
| plain Kelly x75, max 2.5u (no multipliers) | +541u | +33.4% | 46u | 0 | +2,828u | +57.9% | 38u |
| plain Kelly x100, max 5u | +766u | +33.6% | 49u | 50 | +4,095u | +57.9% | 58u |
| plain Kelly x125, max 5u | +935u | +33.6% | 68u | 103 | +4,932u | +57.9% | 66u |
| plain Kelly x150, max 5u | +1,083u | +33.4% | 91u | 169 | +5,655u | +57.9% | 75u |
| live multipliers on Kelly x125, base cap 8 | +1,115u | +34.8% | 91u | 198 | +5,694u | +58.4% | 70u |
| flat 1-5u by edge bands | +1,472u | +29.5% | 187u | - | +7,535u | +56.7% | 115u |

ROI barely moves with stake size (33-36% holdout, 58-60% earlier): a bigger stake buys more profit and a bigger
drawdown in about equal measure. The only-ride and small-field multipliers are not noise: they lift ROI about 2 points,
and the bets they push to the max are the best in the book (live 4.5u+ bets: +80% holdout, +124% earlier). A max bet
"without rules" comes from a bigger Kelly multiplier: x125 makes 103 holdout bets 4.5u+ instead of 15. Not changed.

## Getting closer to BSP, and why it moves (18 Oct 2026, t_drift_gbm.py, t_weekend_bsp.py; founder: "a backtest with the data we pulled this weekend, for getting closer to bsp, always keeping the model the sharpest etc and looking for betting angles / why bsp is moving")
HOLDOUT (1,194 races from 3 Jun with every open and BSP, v10 stage-1 price out of sample, two date halves each scored by
a model fitted on the other). The move y = log(BSP chance / opening chance), sd 0.73.
- Predictable share of the move (R2): our price vs the open, straight line 0.45 (BSP goes 0.88-0.92 of the way from
  the open to our price); form inputs + the open, no price of ours, 0.31; both 0.50. The market moves to where the
  form says, and our price is most of that.
- Drivers after our price (gain share): our price vs the open 35%, then the opening chance, jockey win rate, trip vs
  the horse's best, Neural rating, market class (past BSPs), WFA, peak ratings. Firm: good jockeys, high-rated horses,
  in their trip. Drift: horses whose past prices drifted (fl_mean5_move top fifth x0.66 against x0.95) and horses that
  ran better than their price last time (x0.71 against x1.02).
- SHARPER PRICE: "predicted BSP" = the open moved by the drift model (with our price as an input): KL to BSP 0.0823,
  winner log loss 1.8924, against the live-style blend 0.0840 / 1.8964 and ours alone 0.0897 / 1.9046.
- ANGLE: value-at-open bets (1,422, live rules on the blend, 16c deduction) by the forecast: forecast to firm most
  (top third) +60% at the open and +1% at BSP, in both halves (+60% / +59%); middle +6%; drift third +12% (-14% / +35%,
  inconsistent). Within every edge band the forecast-to-firm half beats the other half: edge 20-50% +23% vs +12%,
  50-100% +44% vs -1%, 100%+ +113% vs +53%. So it adds to the edge, it is not the edge again.
- VALUE ON THE PREDICTED BSP instead of the blend: 1,528 bets +31% flat at the open (live rule 1,422, +26%), flat at
  BSP +2% (live -9%). Half by half, staked on the live stake rule: Jun-Jul +23% / +439u (live +25% / +446u, a tie);
  Aug-Oct, where the drift model saw only earlier races, +58% / +975u (live +50% / +741u). Not adopted yet: one honest
  half, and the drift model is trained on stage 1, not the live stage-2 price. Next: refit on the live price and
  forward-test it beside the live orders.
LIVE MEETINGS (5 to 18 Oct, 66 races where every starter had our pre-market price, the race-morning re-price, the open,
the race-day best price and BSP; the weekend, Thu 15 to Sun 18, 27 races with 9:35am pulls):
- KL to BSP, all / weekend: open 0.150 / 0.175, ours before the market 0.096 / 0.111, our race-morning re-price
  (blended with the open) 0.096 / 0.111, race-morning market 0.054 / 0.061. BSP moved 0.86 of the way to our price;
  where we were 25%+ off the open it moved our way 79% / 83% of the time. 43-44% of the open-to-BSP move is done by
  the race-morning pull.
- The morning-to-BSP move keeps going the way the open-to-morning move went (slope +0.32 / +0.42): momentum, not
  reversal. Our re-price against the morning market still points the way to BSP (correlation 0.26 / 0.28).
- RACE-MORNING PRICE: blending the re-price with the OPEN adds nothing on the day (0.096 either way). Blended with the
  MORNING market instead (0.20 ours + 0.90-0.95 morning, fitted on one half of the meetings, scored on the other): KL
  0.054 -> 0.049 (weekend 0.061 -> 0.056). The 9:30 top-up price should lean on the morning market, not the open.
- Filled bets (24 with full races): median open/BSP 1.53, morning/BSP 0.95; 88% had firmed by race morning, so a
  9:30 top-up on a filled bet is usually below the BSP it ends at.
- WEIGHTING THE STAKE BY THE FORECAST (founder: "why aren't we weighting those more"), live bets, P/L at the open, Jun-Jul
  / Aug-Oct (only Aug-Oct is honest): live stakes +446u / +741u; x1.5 forecast-to-firm and x0.5 forecast-to-drift
  +621u / +731u; x2 / x0.5 +682u / +778u; the live stake rule on the predicted-BSP chance +490u / +831u. The honest half
  gains little from a hand multiplier and most from pricing the chance better, which weights the firmers by itself.
- RE-RUN ON THE LIVE-STYLE PRICE (PRICE=stage2: stage 2 v6 refitted before 6 May, t_blend_open.py's blend_hold.npz; 1,373
  holdout races, halves split at 15 Jul). CLOSER TO BSP: NO. KL to BSP stage 2 alone 0.0801, blended with the open
  0.0767, predicted BSP 0.0791 (winner log loss 1.9062 against the blend's 1.9082, a hair better). The stage-1 gain
  above was against a weaker price; stage 2 already carries most of it. PROFIT: YES, in both halves. Value on the
  predicted BSP, live stakes: +878u / +1,055u against the live rule's +776u / +760u (staked +38% / +59% against +37% /
  +45%). Forecast-to-firm third +56% flat at the open, middle +20%, drift third +9%. Stake x2 forecast-to-firm and x0.5
  forecast-to-drift on the live bets: +899u / +952u against +776u / +760u. So it does not price the whole field closer
  to BSP; it sorts OUR bets better: which of them the market will come to. Not live yet: the orders go in before the
  market, so the open is not known when the order is built; the minimum odds have to be solved per runner against the
  drift model, then forward-tested beside the live orders.
- DROP THE FORECAST-TO-DRIFT THIRD? (founder: "why would we bet on drifters"). Live-style price, by half: the drift
  third alone made +64u / +171u at the open (318 / 260 bets), so dropping it cuts profit: +776u / +760u becomes +712u /
  +589u. Dropped with x2 on the firm third +867u / +867u; kept at x0.5 with x2 on the firm third +899u / +952u (best).
  "Forecast to drift" means the least likely of our value bets to firm, not a horse expected to lose money: they are
  still value at the open, and a smaller stake on them beats none.
- LIVE FROM 19 OCT 2026 (founder: "Yeah fine, let's do it", on dropping the forecast-to-drift third and doubling the
  forecast-to-firm third). drift_forecast.py holds the model (trained on every holdout race from 6 May to 9 Oct with an
  open and BSP, 13,990 runners, stage-2 v6 price; models/drift_model.txt + drift_meta.json, copied to the live model
  dir) and betmatic_orders.py --drift DAY_NPZ applies it (run_meeting.sh passes it). The orders go in before the
  market, so the forecast is worked out at each step's own price (opening chance there = 1/price over the median
  opening book for the field size) and the thirds are set at the bets' minimum odds. t_drift_orders.py tests exactly
  that, cross-fitted by date halves (before / from 15 Jul), 16c deduction:
  live stakes 1,589 bets, 3,170u invested, +1,347u (+42%; halves +682u / +665u); founder's pick 1,301 bets, 3,797u,
  +1,860u (+49%; +981u / +880u); half on the drift third and x2 on firmers 1,589 bets, 4,080u, +1,899u (+47%);
  drop the drift third, firmers at normal stakes 2,604u, +1,270u (+49%). The pick wins both halves. Because the
  forecast firms as the price rises, a horse is usually "drift" only at its lowest step: in effect the bottom step is
  dropped for those horses and the higher steps are doubled. More money goes in (about 20% more turnover in the
  backtest; Kyneton 20 Oct 51.8u to 73.1u if every order fired). Not modelled in the test, same for every version:
  first starters, first-up blocks, the race-level first-starter rule. Re-fit the drift model when stage 2 is retrained.
- MORE VARIANTS, as the orders fire (founder: "what's the ROI if we only double the top third"), halves before / from
  15 Jul: everyone normal and x2 on firmers 4,363u, +1,937u (+44%; +983u / +954u); firm third only at normal stakes
  911 bets, 1,847u, +1,027u (+56%; +581u / +447u); firm third only x2 3,040u, +1,617u (+53%). Best ROI = bet only the
  firm third; most profit = keep everyone and double the firmers; the live pick (+1,860u, +49%) sits between.
- SWITCHED THE SAME NIGHT to everyone at normal stakes and x2 on the firm third (founder: "wouldn't betting more money
  until we start to get limited make the most sense?"): drift_forecast.DRIFT_MULT 0 -> 1. As the orders fire it makes
  the most (+1,937u on 4,363u, +44%) and its worst losing run is SMALLER than the drop-the-drifters version (78u
  against 86u; live stakes 58u, firm third only 51u). Every version keeps the 5u ($500) cap per horse, under the
  Racing Victoria minimum bet limit ($1,000 country / $2,000 metro to lose).
- FINAL, 18 Oct (founder: "ROI is more important... double the top third bets, keep mid tier the same and then lower
  tier half"; the money goes to the best bets first, spread wider once the accounts get limited): DRIFT_MULT 0.5.
  As the orders fire: 1,589 bets, 4,080u, +1,899u (+47%), worst losing run 81u; halves +982u / +917u.
- CASH FLOW AT $50 A UNIT (t_cashflow.py; founder: "how much is normally out for $50 a unit"), backtest 6 May to 9 Oct,
  live stakes, every VIC meeting: per meeting with a bet 8.9 bets, typical $1,048 (1 in 10 over $1,924); per racing day
  $1,380 (1 in 10 over $2,363, most $4,071); per week $9,649 staked, typical profit +$4,509, 4 losing weeks of 23 (worst
  -$463); money out at once (next 3 days' races) typical $4,074, 1 in 10 over $6,023, most $7,220; worst losing run
  $4,293. Upper bound on volume: no first-starter or first-up filters here, and the live forward test fills far fewer
  bets a meeting.
  On the founder's timings (winnings back at once; Saturday metro markets up from Wednesday afternoon, the rest 2 days
  before): money out at once typical $4,150, 1 in 10 over $6,259, most $7,795; Wednesday the heaviest (typical $4,799).
  Live meetings have filled about a third of the backtest's bets a meeting, so live is roughly a third of these.
