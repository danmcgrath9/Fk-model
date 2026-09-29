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
