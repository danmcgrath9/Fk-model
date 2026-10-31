# Calibration check and stake cuts for uncertainty (1 Nov 2026)

Founder, 1 Nov 2026, on a syndicate article: "Yeah nice" to (1) a weekly check that our chances win as often as we say,
by segment, and (2) cutting stakes where the model is less sure. Script: `t_calib_unc.py`. Holdout from 3 Jun to 13 Oct
2026 (v10 never trained on it), the live open rule and stake_rule, filled at the opening price less 7% deductions.

## The bets, by flag (1,444 bets, 2,923u, +1,271u at the open, +43.5%)

| Flag | Bets | Units | P/L open | ROI open | Won / model expected | Beat BSP |
|---|---|---|---|---|---|---|
| None of the flags | 284 | 500 | +372 | +74.3% | 54 / 48.4 (1.12) | 81% |
| Metro | 268 | 556 | +38 | +6.8% | 37 / 52.6 (0.70) | 75% |
| Wet (going band 3-4) | 744 | 1,530 | +634 | +41.4% | 130 / 142.5 (0.91) | 78% |
| First up (90+ days) | 185 | 373 | +147 | +39.5% | 29 / 34.7 (0.84) | 76% |
| Lightly raced (3 or fewer starts) | 426 | 957 | +410 | +42.9% | 77 / 88.0 (0.88) | 72% |
| Thin speed data (2 or fewer ratings) | 397 | 875 | +394 | +45.0% | 73 / 80.7 (0.90) | 70% |

The model overrates every flagged group a little on the horses we bet, and metro a lot.

## Stake cuts tested

| Scheme | Units | P/L | ROI | Worst drawdown | Worst month |
|---|---|---|---|---|---|
| Live | 2,923 | +1,271 | +43.5% | 61 | +88 |
| Half when metro | 2,645 | +1,252 | +47.3% | 55 | +88 |
| Half when wet | 2,158 | +954 | +44.2% | 55 | +69 |
| Half when first up | 2,736 | +1,197 | +43.8% | 58 | +78 |
| Half when lightly raced | 2,444 | +1,066 | +43.6% | 48 | +62 |
| Half when thin speed data | 2,485 | +1,074 | +43.2% | 52 | +62 |
| Half on any non-metro flag | 1,826 | +858 | +47.0% | 40 | +51 |
| x0.75 per flag | 2,112 | +939 | +44.4% | 44 | +56 |

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
