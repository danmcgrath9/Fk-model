Proxy shrinkage k = 10 (fitted on 2003-2018); trees = 520.

## Who scores: log loss on P(anytime), lower is better

| set | games | model | naive proxy | position-aware proxy | position average (same season, hindsight) | model 2+ log loss |
|---|---|---|---|---|---|---|
| dev 2019-2022 | 772 | 0.4229 | 0.4375 | 0.4264 | 0.4313 | 0.1083 |
| confirm 2023-2024 | 426 | 0.4373 | 0.4486 | 0.4382 | 0.4423 | 0.1203 |
| final 2025-2026 | 426 | 0.4393 | 0.4501 | 0.4411 | 0.4458 | 0.1322 |

## Backtest against the PROXY at its fair price (an upper bound, not a market test)

| set | proxy | edge needed | bets | strike rate | avg price | ROI | 90% interval (rounds resampled) |
|---|---|---|---|---|---|---|---|
| dev | naive | 5% | 12,439 | 19.4% | 14.35 | +57.4% | +51.5% to +63.2% |
| dev | naive | 10% | 11,155 | 19.0% | 15.03 | +63.2% | +56.6% to +69.8% |
| dev | naive | 20% | 8,969 | 18.1% | 16.45 | +74.5% | +65.7% to +82.9% |
| dev | naive | 30% | 7,199 | 16.8% | 17.78 | +84.0% | +73.6% to +93.9% |
| dev | position-aware | 5% | 9,750 | 22.0% | 9.16 | +20.3% | +15.7% to +25.0% |
| dev | position-aware | 10% | 7,201 | 21.6% | 9.59 | +22.9% | +17.9% to +27.9% |
| dev | position-aware | 20% | 3,634 | 19.8% | 10.92 | +26.7% | +18.3% to +34.8% |
| dev | position-aware | 30% | 1,813 | 18.8% | 12.34 | +33.2% | +20.4% to +46.3% |
| confirm | naive | 5% | 6,477 | 19.4% | 14.59 | +57.6% | +46.4% to +69.2% |
| confirm | naive | 10% | 5,721 | 18.7% | 15.41 | +64.4% | +52.3% to +77.2% |
| confirm | naive | 20% | 4,502 | 17.2% | 17.02 | +77.5% | +63.3% to +92.2% |
| confirm | naive | 30% | 3,599 | 16.0% | 18.51 | +86.3% | +68.3% to +104.2% |
| confirm | position-aware | 5% | 3,409 | 22.4% | 8.28 | +9.9% | +1.7% to +18.2% |
| confirm | position-aware | 10% | 2,207 | 21.7% | 8.92 | +18.1% | +7.3% to +30.3% |
| confirm | position-aware | 20% | 891 | 19.6% | 10.79 | +34.0% | +13.7% to +55.9% |
| confirm | position-aware | 30% | 402 | 17.9% | 12.57 | +42.1% | +6.8% to +82.1% |
| final | naive | 5% | 6,112 | 19.7% | 13.04 | +53.7% | +44.4% to +62.8% |
| final | naive | 10% | 5,334 | 19.4% | 13.76 | +62.1% | +51.8% to +72.2% |
| final | naive | 20% | 4,072 | 18.2% | 15.15 | +73.4% | +59.2% to +87.3% |
| final | naive | 30% | 3,088 | 16.2% | 16.69 | +75.9% | +59.1% to +93.0% |
| final | position-aware | 5% | 3,214 | 24.2% | 7.62 | +18.5% | +11.5% to +26.3% |
| final | position-aware | 10% | 2,039 | 23.7% | 8.24 | +26.7% | +17.0% to +36.7% |
| final | position-aware | 20% | 827 | 19.1% | 9.49 | +15.5% | -0.4% to +33.6% |
| final | position-aware | 30% | 349 | 16.3% | 10.62 | +17.8% | -9.1% to +48.3% |

## By price band, position-aware proxy, 10% edge (where books charge most is the long end)

| set | fair price | bets | strike rate | ROI | 90% interval |
|---|---|---|---|---|---|
| dev | 1-2.5 | 384 | 52.9% | +16.3% | +6.1% to +26.6% |
| dev | 2.5-4 | 1,279 | 36.9% | +17.1% | +9.3% to +24.7% |
| dev | 4-7 | 2,043 | 25.6% | +31.1% | +22.8% to +39.6% |
| dev | 7-15 | 2,190 | 12.9% | +26.7% | +16.4% to +37.2% |
| dev | 15-+ | 1,305 | 5.4% | +11.2% | -7.2% to +30.1% |
| confirm | 1-2.5 | 125 | 47.2% | +5.8% | -9.5% to +21.0% |
| confirm | 2.5-4 | 474 | 37.6% | +18.0% | +4.9% to +31.5% |
| confirm | 4-7 | 644 | 21.6% | +11.4% | -1.3% to +25.9% |
| confirm | 7-15 | 604 | 13.7% | +32.3% | +9.3% to +56.4% |
| confirm | 15-+ | 360 | 5.3% | +11.1% | -27.6% to +55.2% |
| final | 1-2.5 | 129 | 53.5% | +19.2% | +4.3% to +33.7% |
| final | 2.5-4 | 446 | 35.4% | +11.0% | -1.8% to +23.4% |
| final | 4-7 | 543 | 27.3% | +39.1% | +23.1% to +56.8% |
| final | 7-15 | 661 | 14.1% | +37.7% | +19.0% to +55.1% |
| final | 15-+ | 260 | 5.8% | +3.9% | -41.4% to +53.6% |

## Calibration (all non-final sets): predicted vs actual anytime rate by decile

| decile | predicted | actual | players |
|---|---|---|---|
| 1 | 0.042 | 0.044 | 4,070 |
| 2 | 0.057 | 0.061 | 4,070 |
| 3 | 0.074 | 0.077 | 4,069 |
| 4 | 0.096 | 0.097 | 4,070 |
| 5 | 0.125 | 0.133 | 4,070 |
| 6 | 0.163 | 0.163 | 4,069 |
| 7 | 0.212 | 0.222 | 4,070 |
| 8 | 0.268 | 0.277 | 4,069 |
| 9 | 0.342 | 0.346 | 4,070 |
| 10 | 0.457 | 0.456 | 4,070 |

## What drives it (share of gain)

position_code 46%, opp_conceded_group_ew 17%, career_rate 12%, group_rate 4%, try_ew_slow 4%, exp_for 3%, opp_strength_named 2%, exp_margin 2%, career_games 2%, opp_conceded_ew 1%
