## First try scorer (Champion Data score flow)

| set | games | model -log p(first scorer) | position-share stand-in | model top pick right | stand-in top pick right |
|---|---|---|---|---|---|
| dev | 772 | 3.169 | 3.222 | 10.5% | 8.0% |
| confirm | 426 | 3.221 | 3.253 | 9.6% | 9.6% |

### Backtest against the position-share PROXY at its fair price (upper bound)

| set | edge needed | bets | strike rate | avg price | ROI | 90% interval |
|---|---|---|---|---|---|---|
| dev | 10% | 8,081 | 4.4% | 52.3 | +36.6% | +23.7% to +49.4% |
| dev | 25% | 5,182 | 4.4% | 54.8 | +40.6% | +24.1% to +57.9% |
| dev | 50% | 2,432 | 4.1% | 61.3 | +46.2% | +19.7% to +74.7% |
| confirm | 10% | 4,387 | 4.1% | 49.7 | +25.1% | +9.7% to +40.8% |
| confirm | 25% | 2,692 | 4.1% | 52.1 | +27.6% | +6.9% to +49.3% |
| confirm | 50% | 1,058 | 3.7% | 61.4 | +36.3% | +1.9% to +73.8% |
