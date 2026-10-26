# Run metres and tackles, step 1 (stand-in lines only)

## run metres

Stand-in line offset +2.25 (fitted on FIT); trees 292; spread sd = 17.65 + 0.165 x projection.

| set | player-games | projection miss | last-10 miss | blind over wins | bets at 56%+ | hit rate | ROI at 1.87 | 90% interval |
|---|---|---|---|---|---|---|---|---|
| dev | 12,131 | 28.07 | 29.91 | 50.8% | 8,112 | 64.4% | +20.5% | +18.4% to +22.7% |
| confirm | 13,700 | 27.34 | 28.66 | 50.7% | 9,149 | 62.3% | +16.6% | +14.8% to +18.5% |

### run metres: by role against the previous game (56% threshold)

| set | role | bets | hit rate | ROI at 1.87 | 90% interval |
|---|---|---|---|---|---|
| dev | same as last game | 6,225 | 63.5% | +18.7% | +16.5% to +21.2% |
| dev | changed | 1,887 | 67.6% | +26.4% | +22.8% to +29.8% |
| confirm | same as last game | 7,123 | 61.2% | +14.4% | +12.3% to +16.6% |
| confirm | changed | 2,026 | 66.4% | +24.1% | +21.2% to +27.1% |

### run metres: against the smarter stand-in (career average in this position, offset +3.00)

| set | bets at 56%+ | hit rate | ROI at 1.87 | 90% interval |
|---|---|---|---|---|
| dev | 8,192 | 64.4% | +20.4% | +18.7% to +22.1% |
| confirm | 9,042 | 61.9% | +15.8% | +14.2% to +17.4% |

### run metres: by threshold

| set | threshold | bets | hit rate | ROI |
|---|---|---|---|---|
| dev | 54% | 9,394 | 62.9% | +17.6% |
| dev | 56% | 8,112 | 64.4% | +20.5% |
| dev | 58% | 6,888 | 65.9% | +23.2% |
| dev | 60% | 5,701 | 67.8% | +26.8% |
| confirm | 54% | 10,664 | 61.0% | +14.2% |
| confirm | 56% | 9,149 | 62.3% | +16.6% |
| confirm | 58% | 7,752 | 63.9% | +19.4% |
| confirm | 60% | 6,471 | 65.2% | +21.9% |

What drives it: group_avg 44%, ew_fast 20%, last10 11%, ew_slow 11%, position_code 4%, opp_conc 2%

## tackles

Stand-in line offset +0.20 (fitted on FIT); trees 173; spread sd = 2.64 + 0.170 x projection.

| set | player-games | projection miss | last-10 miss | blind over wins | bets at 56%+ | hit rate | ROI at 1.87 | 90% interval |
|---|---|---|---|---|---|---|---|---|
| dev | 12,131 | 5.15 | 5.87 | 51.5% | 8,629 | 68.8% | +28.7% | +27.1% to +30.2% |
| confirm | 13,700 | 4.98 | 5.58 | 50.3% | 9,596 | 67.3% | +25.8% | +24.2% to +27.4% |

### tackles: by role against the previous game (56% threshold)

| set | role | bets | hit rate | ROI at 1.87 | 90% interval |
|---|---|---|---|---|---|
| dev | same as last game | 6,517 | 67.1% | +25.4% | +23.6% to +27.1% |
| dev | changed | 2,112 | 74.2% | +38.8% | +36.2% to +41.3% |
| confirm | same as last game | 7,385 | 65.9% | +23.2% | +21.3% to +25.1% |
| confirm | changed | 2,211 | 72.0% | +34.6% | +31.2% to +38.0% |

### tackles: against the smarter stand-in (career average in this position, offset +0.10)

| set | bets at 56%+ | hit rate | ROI at 1.87 | 90% interval |
|---|---|---|---|---|
| dev | 7,938 | 65.9% | +23.3% | +21.6% to +25.0% |
| confirm | 8,568 | 64.1% | +19.9% | +18.1% to +21.6% |

### tackles: by threshold

| set | threshold | bets | hit rate | ROI |
|---|---|---|---|---|
| dev | 54% | 9,781 | 66.9% | +25.2% |
| dev | 56% | 8,629 | 68.8% | +28.7% |
| dev | 58% | 7,590 | 70.2% | +31.2% |
| dev | 60% | 6,683 | 71.7% | +34.0% |
| confirm | 54% | 10,895 | 65.8% | +23.0% |
| confirm | 56% | 9,596 | 67.3% | +25.8% |
| confirm | 58% | 8,444 | 68.9% | +28.8% |
| confirm | 60% | 7,391 | 70.2% | +31.2% |

What drives it: group_avg 64%, position_code 20%, ew_fast 9%, ew_slow 1%, last10 1%, last3 1%
