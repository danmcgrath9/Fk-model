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
