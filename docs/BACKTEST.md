# Back-test against Betfair SP

Fitted 2026-09-12 01:02 UTC over 209 resulted races (2095 runners), 2026-04-30 to 2026-08-31. Out of sample = fitted on the first 146 races by date, scored on the last 63.

Each model is a conditional logit fitted to minimise the cross-entropy against the BSP-implied chances. 'KL to BSP' is how far it sits from BSP (0 = BSP itself); 'log loss' is scored on the actual winners (lower is better); 'top pick won' is the share of races the model's highest-rated runner won.

| model | KL to BSP (in / out) | log loss vs winners (in / out) | top pick won (in / out) |
|---|---|---|---|
| bsp_itself | 0.0000 / 0.0000 | 1.7528 / 1.8102 | 39.7% / 33.3% |
| opening_market | 0.1367 / 0.1341 | 1.8497 / 1.9125 | 34.9% / 27.0% |
| neural_only | 0.2410 / 0.2653 | 2.0231 / 2.0546 | 21.9% / 30.2% |
| ratings_only | 0.2786 / 0.3133 | 2.0126 / 2.1169 | 24.7% / 17.5% |
| ratings_plus_distance | 0.2540 / 0.2897 | 1.9804 / 2.0896 | 30.1% / 25.4% |
| all_form **(deployed)** | 0.1877 / 0.2152 | 1.9114 / 2.0110 | 27.4% / 27.0% |
| all_form_plus_open_market | 0.1234 / 0.1278 | 1.8214 / 1.9136 | 35.6% / 20.6% |

Deployed: **all_form**, the form-only model closest to BSP out of sample, refitted on all 209 races.

## Coefficients of the deployed model

- neural_rel: +1.7464
- last_rel: -0.0303
- peak_rel: +0.0094
- peak12_rel: +0.0424
- wfa_rel: +0.0571
- wfa_best_rel: -0.0129
- ohr_rel: -0.0046
- dist_rel: +0.0479
- dist_win: +0.6029

Features, all relative within the race: neural_rel = Neural points / the race's top (top = 1); last_rel, peak_rel, peak12_rel = points below the race's best of the latest rated run (adjusted to today's weight), the career peak and the 12-month peak; wfa_rel, wfa_best_rel = points below the best of the latest and the best WFA rating; ohr_rel = points below the top official handicap rating; dist_rel = points below the best mean rating of runs within 200m of today's trip; dist_win = the record at the distance as a shrunk win rate, against the race mean; open_logit = log of the opening-market chance (comparison only, never deployed, so Value keeps meaning disagreement with the market).

## Calibration of the deployed model

| rated chance | runners | mean rated | share that won |
|---|---|---|---|
| 0% to 5% | 594 | 3.1% | 1.3% |
| 5% to 10% | 780 | 7.2% | 7.3% |
| 10% to 20% | 494 | 13.9% | 15.4% |
| 20% to 30% | 153 | 24.1% | 24.8% |
| 30% to 50% | 64 | 36.4% | 37.5% |
| 50% to 100% | 10 | 58.8% | 70.0% |
