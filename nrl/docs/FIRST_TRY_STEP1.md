## First try scorer (Champion Data score flow)

| set | games | model -log p(first scorer) | position-share stand-in | model top pick right | stand-in top pick right |
|---|---|---|---|---|---|
| dev | 772 | 3.168 | 3.222 | 10.5% | 7.9% |
| confirm | 426 | 3.219 | 3.253 | 9.2% | 10.1% |
| final | 426 | 3.163 | 3.225 | 10.6% | 5.6% |

### Backtest against the position-share PROXY at its fair price (upper bound)

| set | edge needed | bets | strike rate | avg price | ROI | 90% interval |
|---|---|---|---|---|---|---|
| dev | 10% | 8,102 | 4.4% | 52.2 | +35.1% | +21.8% to +48.6% |
| dev | 25% | 5,156 | 4.4% | 54.3 | +39.2% | +23.0% to +55.5% |
| dev | 50% | 2,376 | 4.2% | 61.2 | +45.7% | +20.9% to +74.7% |
| confirm | 10% | 4,398 | 4.3% | 50.1 | +33.6% | +16.3% to +52.0% |
| confirm | 25% | 2,689 | 4.2% | 52.8 | +24.8% | +4.2% to +45.9% |
| confirm | 50% | 1,050 | 3.5% | 62.2 | +19.3% | -16.6% to +59.2% |
| final | 10% | 4,472 | 4.5% | 52.5 | +36.5% | +17.9% to +55.4% |
| final | 25% | 2,831 | 4.4% | 56.1 | +37.8% | +13.9% to +61.4% |
| final | 50% | 1,148 | 4.3% | 67.6 | +68.0% | +24.8% to +115.4% |
