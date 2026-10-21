# Late changes: Tuesday's list against who took the field

666 games where both sides' Tuesday lists were parsed, seasons 2009, 2010, 2013, 2014, 2018. One margin model (ratings + player strength, fitted on who played, 2003-2018), fed three line-ups:

| line-up fed in | bits/game | log loss | margin miss |
|---|---|---|---|
| last game's 17 (open) | 0.042 | 0.6641 | 13.62 |
| Tuesday's 1-17 | 0.050 | 0.6587 | 13.46 |
| who took the field | 0.051 | 0.6578 | 13.44 |

Named 1-17 who did not take the field: 6.1% of players; per team-game 1.02 on average, none in 35%, three or more in 7%.
Late changes moved our predicted margin by 0.67 points on average, by 2+ points in 6% of games.
