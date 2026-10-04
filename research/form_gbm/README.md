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
