Proxy shrinkage k = 10 (fitted on 2003-2018); trees = 510.

## Who scores: log loss on P(anytime), lower is better

| set | games | model | naive proxy | position-aware proxy | position average (same season, hindsight) | model 2+ log loss |
|---|---|---|---|---|---|---|
| dev 2019-2022 | 772 | 0.4229 | 0.4375 | 0.4264 | 0.4313 | 0.1083 |
| confirm 2023-2024 | 426 | 0.4372 | 0.4486 | 0.4382 | 0.4423 | 0.1203 |

## Backtest against the PROXY at its fair price (an upper bound, not a market test)

| set | proxy | edge needed | bets | strike rate | avg price | ROI | 90% interval (rounds resampled) |
|---|---|---|---|---|---|---|---|
| dev | naive | 5% | 12,384 | 19.3% | 14.34 | +57.3% | +51.2% to +63.2% |
| dev | naive | 10% | 11,124 | 19.1% | 15.00 | +64.1% | +57.4% to +70.7% |
| dev | naive | 20% | 8,865 | 17.8% | 16.46 | +72.4% | +63.8% to +80.7% |
| dev | naive | 30% | 7,052 | 16.9% | 17.84 | +85.1% | +74.5% to +95.6% |
| dev | position-aware | 5% | 9,632 | 22.0% | 9.10 | +20.4% | +15.6% to +25.0% |
| dev | position-aware | 10% | 7,160 | 21.6% | 9.59 | +23.5% | +17.9% to +29.1% |
| dev | position-aware | 20% | 3,604 | 19.1% | 10.97 | +23.5% | +15.2% to +31.7% |
| dev | position-aware | 30% | 1,831 | 18.7% | 12.65 | +35.9% | +22.3% to +49.9% |
| confirm | naive | 5% | 6,449 | 19.6% | 14.55 | +59.3% | +47.9% to +71.4% |
| confirm | naive | 10% | 5,686 | 18.6% | 15.40 | +64.1% | +51.8% to +77.0% |
| confirm | naive | 20% | 4,450 | 17.3% | 17.07 | +79.2% | +63.9% to +94.7% |
| confirm | naive | 30% | 3,562 | 16.0% | 18.52 | +84.9% | +67.4% to +102.7% |
| confirm | position-aware | 5% | 3,417 | 23.1% | 8.18 | +15.2% | +7.0% to +23.5% |
| confirm | position-aware | 10% | 2,276 | 21.4% | 8.87 | +15.6% | +6.0% to +25.9% |
| confirm | position-aware | 20% | 890 | 19.2% | 10.84 | +26.8% | +6.2% to +50.5% |
| confirm | position-aware | 30% | 404 | 17.3% | 12.83 | +40.3% | +11.8% to +68.2% |

## By price band, position-aware proxy, 10% edge (where books charge most is the long end)

| set | fair price | bets | strike rate | ROI | 90% interval |
|---|---|---|---|---|---|
| dev | 1-2.5 | 361 | 53.2% | +16.9% | +6.3% to +27.6% |
| dev | 2.5-4 | 1,258 | 36.8% | +16.8% | +9.1% to +24.6% |
| dev | 4-7 | 2,058 | 26.1% | +34.1% | +25.7% to +42.2% |
| dev | 7-15 | 2,189 | 13.1% | +27.6% | +15.8% to +38.8% |
| dev | 15-+ | 1,294 | 5.3% | +8.1% | -12.9% to +28.7% |
| confirm | 1-2.5 | 124 | 46.8% | +4.8% | -12.7% to +23.0% |
| confirm | 2.5-4 | 493 | 37.1% | +16.9% | +4.3% to +30.0% |
| confirm | 4-7 | 685 | 21.6% | +10.8% | -1.9% to +24.5% |
| confirm | 7-15 | 601 | 13.3% | +27.8% | +6.0% to +49.1% |
| confirm | 15-+ | 373 | 4.8% | +6.5% | -34.4% to +53.3% |

## Calibration (all non-final sets): predicted vs actual anytime rate by decile

| decile | predicted | actual | players |
|---|---|---|---|
| 1 | 0.042 | 0.045 | 4,070 |
| 2 | 0.057 | 0.061 | 4,070 |
| 3 | 0.074 | 0.076 | 4,069 |
| 4 | 0.096 | 0.097 | 4,070 |
| 5 | 0.124 | 0.132 | 4,070 |
| 6 | 0.163 | 0.164 | 4,069 |
| 7 | 0.211 | 0.219 | 4,070 |
| 8 | 0.267 | 0.277 | 4,069 |
| 9 | 0.343 | 0.348 | 4,070 |
| 10 | 0.456 | 0.458 | 4,070 |

## What drives it (share of gain)

position_code 44%, opp_conceded_group_ew 19%, career_rate 12%, try_ew_slow 4%, group_rate 4%, exp_for 3%, opp_strength_named 2%, career_games 2%, exp_margin 2%, opp_conceded_ew 1%
