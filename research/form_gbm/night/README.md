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
