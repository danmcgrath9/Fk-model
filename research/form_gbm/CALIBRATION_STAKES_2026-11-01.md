# Calibration check and stake cuts for uncertainty (1 Nov 2026)

Founder, 1 Nov 2026, on a syndicate article: "Yeah nice" to (1) a weekly check that our chances win as often as we say,
by segment, and (2) cutting stakes where the model is less sure. Script: `t_calib_unc.py`. Holdout from 3 Jun to 13 Oct
2026 (v10 never trained on it), the live open rule and stake_rule, filled at the opening price less 7% deductions.

## The bets, by flag (1,444 bets, 2,923u, +1,271u at the open, +43.5%)

| Flag | Bets | Units | P/L open | ROI open | Won / model expected | Beat BSP |
|---|---|---|---|---|---|---|
| None of the flags | 243 | 462 | +249 | +53.9% | 42 / 44.3 (0.95) | 75% |
| Metro | 268 | 556 | +38 | +6.8% | 37 / 52.6 (0.70) | 75% |
| Wet (soft or heavy) | 974 | 2,003 | +820 | +40.9% | 171 / 187.2 (0.91) | 79% |
| First up (90+ days) | 185 | 373 | +147 | +39.5% | 29 / 34.7 (0.84) | 76% |
| Lightly raced (3 or fewer starts) | 426 | 957 | +410 | +42.9% | 77 / 88.0 (0.88) | 72% |
| Thin speed data (2 or fewer ratings) | 397 | 875 | +394 | +45.0% | 73 / 80.7 (0.90) | 70% |

The model overrates every flagged group a little on the horses we bet, and metro a lot.

Corrected the same day: the first run took going bands 3-4 as wet, which is heavy and synthetic (export_dataset.py
GOING_CODE: good 1, soft 2, heavy 3, synthetic 4). Wet is soft or heavy (2-3). The decision did not change.

## Stake cuts tested

| Scheme | Units | P/L | ROI | Worst drawdown | Worst month |
|---|---|---|---|---|---|
| Live | 2,923 | +1,271 | +43.5% | 61 | +88 |
| Half when metro | 2,645 | +1,252 | +47.3% | 55 | +88 |
| Half when wet | 1,921 | +861 | +44.8% | 54 | +83 |
| Half when first up | 2,736 | +1,197 | +43.8% | 58 | +78 |
| Half when lightly raced | 2,444 | +1,066 | +43.6% | 48 | +62 |
| Half when thin speed data | 2,485 | +1,074 | +43.2% | 52 | +62 |
| Half on any non-metro flag | 1,703 | +761 | +44.7% | 40 | +53 |
| x0.75 per flag | 2,016 | +891 | +44.2% | 44 | +59 |

**Decision: only metro earns the cut** (already live since 31 Oct, with the metro price fix). It gives up 19u of 1,271
and takes 6u off the worst drawdown. Every other cut gives up profit in proportion to the stake it removes: those bets
still make about 40% at the open, because the opening-price edge is bigger than the model's overrating of them.
The idea was sound and the test says no; no stake change.

## The weekly check

Replayed each Sunday over the trailing 8 weeks of bets, flagging a segment whose wins sit 2 SD under the model's
expected wins (15+ expected): metro flagged on 5 Jul (11 won v 19 expected) and 26 Jul (19 v 28), three months before
Derby Day, and nothing else after July. Whole-race segments (metro, wet) are always calibrated across ALL runners
because chances are normalised per race, so the check runs on the bets, where the question lives. Run it at each
Sunday settle; a flagged segment goes to the founder that day with the figures.

## Backed and failed last start (t_backed_failed.py, same holdout)

Founder, 1 Nov, on forgiving a blocked run: "It would be taken into account of well supported and failed though?" Yes:
beat_market_last carries it. Horses at BSP under $5 last start that finished 4th or worse won 43 next start against the
model's 44.1 and the market's 44.3 (under $3: 9 v 9.3 v 9.2). Calibrated, and already in the price: the live rule's 40 bets
on them made +4%. A forgive list would only add information for an unsupported horse that was blocked; not built
(founder: "no all good").

## Input audit and stage 3 (1 Nov 2026 evening, founder: "keep doing tests on all inputs and make sure they make sense...
get closer to BSP and winning ROI")
t_input_calib.py (193 continuous inputs, full history out of fold, five bands each): no input where the model's expected
winners drift from the actual across the input's range in both date halves, and no band outside 0.80-1.20 with 40+ expected
winners. t_flag_calib.py (binary flags): winkers on for the first time 0.81 (97 expected, 0.84 / 0.78 by half) and
emergency runners 1.13 (166) are the only ones off, both small. The inputs make sense; the one real defect was the
undeclared-rider zeros, fixed in drop_scr.py. Straight-course model input (t_straight_feat.py, 4-fold cross-fit, 74
straight races): worse (log loss 2.108 -> 2.143), trees use it 0.0-0.04%; the x0.7 direct markdown stays instead.
t_stage3.py (a logistic layer over the out-of-fold log-odds plus metro, straight, style, prep, first starters, field,
distance, going, and the model-v-open gap; fitted on one date half, scored on the other): with the market gap, KL to BSP
0.0884 -> 0.0824 and ROI +47.7% -> +51.1%, but 1,300 fewer bets and 860u less profit; without market inputs, no gain
(KL 0.0898, +4,726u v +4,716u). Getting closer to BSP means leaning on the market, which is what the metro fix does
where the model is wrong and costs profit where it is right. Not adopted beyond metro. Its fitted weights agree with
the live rules' direction: straight forward -0.51 log-odds (we use x0.7 = -0.36), metro lean, back-settlers -0.16
(the old shade, which ROI rejected: calibration and profit pull apart there).

## BSP campaign (1 Nov 2026 evening, founder: "find a way for us to get closer to BSP. I have so much time, just run")
campaign.py, full table in campaign_2026-11-01.md. Stage-1 trees member on the lab split (fit on the oldest 56% of races,
stopped on the next 14%, scored on the newest 30% from 12 May, which no decision touched). 22 experiments. KL to BSP on the
unseen 30%, live settings 0.0987. HELPS: 3 seeds averaged 0.0966; learning rate 0.03 (was 0.06) 0.0973 and the plan's ROI
+30.3% -> +34.4%; min leaf 50 (was 100) 0.0979. COMBINED (lr 0.03, min leaf 50, 3 seeds, 9,000-round cap): 0.0955, the best
of the campaign, plan +31.5%. NOTHING: L2, leaves, feature fraction, extra-trees off (0.1007), the blanking augmentation off
(0.1003: it earns its place) or at 50%, DART (0.1153), pruning inputs (top 50% 0.1015, top 25% 0.1060), the prep-pattern
inputs (0.1010), a ridge conditional logit alone (0.1255) or blended (KL 0.0979 but the plan falls to +27.6%).
THE DATA CURVE: trained on the newest 50% of the training races 0.1060, 75% 0.1018, 100% 0.0987: about 0.003 of KL per
added quarter and not flattening. More races is the biggest lever found; the Form King national archive is the way to get
them.
IN PLAIN TERMS, on the horses we bet (rated $1.60-$15), unseen races: the opening market's typical miss against BSP is 40%
(28% of horses within 20% of BSP); the live settings 34.9% (32%); the combined settings 34.0% (33%); we are closer to BSP
than the open on 54-55 of every 100 such horses, 57 of 100 under $5. The settings gain is small in these terms; the edge is
being closer than the open on the horses we pick and getting on before the market moves.
NOT PORTED YET: the winners go into oof_trees.py and train_all_f9.py (lr 0.03, min_data_in_leaf 50, 3 seeds averaged in log
space) on the founder's word; 3 seeds roughly triples stage-1 training time in retrain.sh; the deploy gate (holdout KL,
t_b9_s2) decides, and the daily retrain only ever saves a challenger.
