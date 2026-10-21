# Weather: does it help? (dev and confirm only; actual weather, so an upper bound on a forecast)

3,634 games with weather; 15 under a roof.

| market | set | version | result |
|---|---|---|---|
| totals | dev | ratings only | miss 10.061 points |
| totals | confirm | ratings only | miss 10.747 points |
| totals | dev | ratings + weather | miss 9.911 points |
| totals | confirm | ratings + weather | miss 10.613 points |
| | | coefficients | rain in game -1.39 pts/mm, rain before +0.13, wind -0.129 pts per km/h, temp +0.337, dew point -0.503 |
| totals | dev+confirm | games with 2mm+ of rain during the game | 31 games, average total 35.3 against 43.9 |
| anytime try | dev | without weather | log loss 0.42294 |
| anytime try | confirm | without weather | log loss 0.43725 |
| anytime try | dev | with weather | log loss 0.42284 |
| anytime try | confirm | with weather | log loss 0.43658 |
| run metres | dev | without weather | projection miss 28.075 |
| run metres | confirm | without weather | projection miss 27.341 |
| run metres | dev | with weather | projection miss 28.157 |
| run metres | confirm | with weather | projection miss 27.334 |
| tackles | dev | without weather | projection miss 5.152 |
| tackles | confirm | without weather | projection miss 4.980 |
| tackles | dev | with weather | projection miss 5.147 |
| tackles | confirm | with weather | projection miss 4.980 |
