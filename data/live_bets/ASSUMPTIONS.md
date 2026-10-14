# What the model and the BetMatic method assume, and what has been checked (15 Oct 2026)

Founder, 15 Oct 2026: "make sure what we are doing is right and we aren't assuming anything". Each line says how it
was checked. CHECKED = tested against raw data or a live record; NOT CHECKED = still an assumption; WRONG = found wrong.

## Model inputs
| Assumption | Status | How |
|---|---|---|
| Every input matches Form King's raw data | CHECKED, one exception | research/form_gbm/t_verify_inputs.py recomputes the inputs from the raw race files for 4 race days (9 Sep 2026, 2 Aug 2025, 24 Jan 2026, 13 Jun 2026: 602 runners, 5,333 past runs): finish, BSP, opening price, barrier, weight, days since last run, apprentice claim, and each past run's days before, finish, margin, BSP, barrier, settling position all match exactly |
| Gear inputs mean what their names say | WRONG | gear_first_time and blinkers_first match the word FIRST, so OFF_FIRST_TIME (gear taken off for the first time) counts as gear on for the first time: wrong on 29 of 602 runners checked (5%). Fix in export_dataset.py, then retrain |
| No input carries information from after the race | CHECKED for past runs | every past run in the whole dataset is at least 2 days before the race it feeds |
| Form King's ratings and LWS are as they stood before each race | NOT CHECKED by us | Form King says v1.1.0 (8 Oct 2026) made LWS and exp point in time back to 1 Jul 2025; the LWS bug moved our prices 0.1% median (13 Oct check) |
| Jockey and trainer 12-month figures are as they stood before each race | NOT CHECKED | ask Dave whether lastTwelveMonthWinPercentage is point in time in history pulls |
| The opening price is never a model input | CHECKED | export_dataset.py bars open, exp and every market-derived column; the betting price p_model is before the open blend |
| Every Form King field that might help is tested | NOT YET | unread fields listed 15 Oct: race-review comments (videoComment), past-run gear and price flucs, pos1200m, spell, race type, foal date, home track, acceptances, track penetrometer and rain; scripts/wide_table.py exports them for trials |

## Backtest and betting
| Assumption | Status | How |
|---|---|---|
| Form King's opening price (avgOpen, an average of bookmakers' first prices) is what TAB offers at its open | NOT CHECKED | record TAB's own opening price beside Form King's for every live bet from the first BetMatic day |
| Every order fills in full | NOT CHECKED | BetMatic takes a reduced offer at the reduced stake; log every one |
| 16c deduction on every winner | CHECKED, cautious | TAB's actual deductions at Caulfield 14 Oct were about 40% of our estimate |
| The 2025 races' opening prices are the same quantity as 2026's | UNKNOWN | the 2025 opens sit much closer to BSP (KL 0.11 vs 0.14); the live TAB opens will show which era they resemble |
| Order files are built on the final field | CHECKED | betmatic_orders.py drops emergencies and scratchings and warns on a pre-final-field file (14 Oct) |
| The order builder bets what the backtest bets | CHECKED | Cranbourne 16 and Caulfield 17 order files rebuild identically under the same rules |
| The holdout's rules were not tuned on the holdout | WRONG | the 20% edge, 5% shade and 3 steps were chosen looking at it, so it flatters; the 2025 races (+21%) are the cleaner test |

## Field coverage (15 Oct 2026, scripts/wide_table.py over 51,492 runners)
Checked rather than assumed: how often each unread field is actually filled, by race month.
- Race-review comments (videoComment): 63-68% of last starts for races pulled in the 14 Oct backfill (Jul-Sep 2025) and
  55% in Oct 2026, but 0% for every race pulled from Nov 2025 to Aug 2026. The field depends on WHEN a race was pulled,
  not when it was run, so it cannot be tested or trained on until the year is re-pulled (about 25 credits a meeting).
- Acceptances: never populated (0%).
- Past-run price flucs 61-72%, past-run gear 52-64%, position at 1200m 34-43%, home track 92-98%, foal date 100%.
- September 2026 is thinner than its neighbours on flucs (34%) and spell (56%): the races pulled live that month
  (the "September gap" of 4 Oct) carried less.
