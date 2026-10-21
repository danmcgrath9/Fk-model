# A-League Men team model, step 1: out-of-sample results

**In short (21 Oct 2026).** On the three newest seasons, never used for any choice, the model's head-to-head
probabilities beat simple base rates clearly and are level with a plain Elo rating. For over 2.5 goals
and both teams to score it is no better than the league's long-run rates. That is the honest ceiling of
a goals-only model in a league this even: the result, not the goal count, is where it has information.
Nothing here says it beats a bookmaker; only recorded opening lines can say that.

Two things to look at next, on the 2026-27 season as it is played (the final seasons are now spent and
cannot be used to tune): **home advantage is overrated** (home wins predicted 41.4%, actual 38.0% in the
final three seasons; the league's home edge has been shrinking), and **strong favourites are overrated**
(home sides priced 50-60% won 46.8%). Both point the same way and suggest a home advantage that is
allowed to change over time.

Expected goals per side from a time-weighted Dixon-Coles model, refitted before every match day on earlier matches only; every market priced from one score matrix. "At the open" only: no line-ups in the data yet. No betting lines yet either, so this measures the probabilities against simple alternatives, not profit.

## Settings, chosen on 2016-2020 and checked on 2021-2023

Score = head-to-head log loss + over 2.5 log loss (lower is better). Top five by the tune seasons, out of 60 combinations:

|   half_life |   carry |   reg |   rho |   tune |   confirm |   confirm_rank |
|------------:|--------:|------:|------:|-------:|----------:|---------------:|
|         180 |    0.5  |     4 | -0.07 | 1.6857 |    1.7401 |             31 |
|         180 |    0.75 |     4 | -0.07 | 1.6861 |    1.741  |             33 |
|         730 |    0.25 |     4 | -0.07 | 1.6862 |    1.7399 |             28 |
|         365 |    0.5  |     4 | -0.07 | 1.6862 |    1.7413 |             34 |
|         365 |    0.25 |     4 | -0.07 | 1.6865 |    1.7401 |             30 |

Chosen: half-life 180 days, season carry-over 0.5, ridge 4.0, rho -0.070. On the confirm seasons it ranks 31 of 60 (best confirm score 1.7345, chosen 1.7401). The gap to the best setting on the confirm seasons is +0.0057 a match, 90% interval -0.0035 to +0.0147 (resampling weeks): within noise. Spread of the tune score across all 60 settings: 1.6857 to 1.7141.

## Every season, settings frozen (tune, confirm, then the final three)

| season | games | model h2h log loss | Elo | base rates | model RPS | Elo RPS | model over 2.5 | base | model BTTS | base |
|---|---|---|---|---|---|---|---|---|---|---|
| 2015-16 | 140 | 1.0022 | 1.0154 | 1.0431 | 0.2137 | 0.2180 | 0.6448 | 0.6654 | 0.6707 | 0.6678 |
| 2016-17 | 140 | 1.0150 | 1.0313 | 1.0700 | 0.2061 | 0.2084 | 0.6819 | 0.6784 | 0.6773 | 0.6784 |
| 2017-18 | 140 | 1.0157 | 1.0174 | 1.0619 | 0.2233 | 0.2252 | 0.6814 | 0.6604 | 0.6835 | 0.6707 |
| 2018-19 | 140 | 0.9882 | 0.9936 | 1.0652 | 0.2066 | 0.2071 | 0.6597 | 0.6844 | 0.6580 | 0.6704 |
| 2019-20 | 148 | 1.0327 | 1.0247 | 1.0490 | 0.2295 | 0.2273 | 0.7043 | 0.6829 | 0.6863 | 0.6699 |
| 2020-21 | 161 | 1.0597 | 1.0606 | 1.0698 | 0.2293 | 0.2296 | 0.6873 | 0.6860 | 0.6787 | 0.6769 |
| 2021-22 | 163 | 1.0744 | 1.0610 | 1.0633 | 0.2321 | 0.2276 | 0.6853 | 0.6816 | 0.6984 | 0.6869 |
| 2022-23 | 163 | 1.0468 | 1.0492 | 1.0653 | 0.2239 | 0.2233 | 0.6671 | 0.6687 | 0.6561 | 0.6612 |
| 2023-24 | 169 | 1.0653 | 1.0662 | 1.0841 | 0.2241 | 0.2234 | 0.6692 | 0.6698 | 0.6685 | 0.6647 |
| 2024-25 | 176 | 1.0465 | 1.0777 | 1.1076 | 0.2186 | 0.2316 | 0.6703 | 0.6702 | 0.6493 | 0.6675 |
| 2025-26 | 163 | 1.0989 | 1.1002 | 1.1002 | 0.2342 | 0.2334 | 0.6929 | 0.6888 | 0.6789 | 0.6750 |

## The final three seasons together (2023-24 to 2025-26), 90% intervals by week

| comparison | mean difference (negative = model better) | 90% interval | verdict |
|---|---|---|---|
| h2h log loss: model - base rates | -0.0278 | -0.0492 to -0.0069 | model better |
| h2h log loss: model - Elo | -0.0115 | -0.0245 to +0.0014 | no difference |
| h2h RPS: model - Elo | -0.0040 | -0.0084 to +0.0006 | no difference |
| over 2.5 log loss: model - base rates | +0.0011 | -0.0151 to +0.0177 | no difference |
| BTTS log loss: model - base rates | -0.0038 | -0.0156 to +0.0079 | no difference |

## Calibration, final three seasons (does a 40% home win happen 40% of the time?)

| market | predicted band | games | average predicted | happened |
|---|---|---|---|---|
| home win | (0.0, 0.2] | 9 | 0.143 | 0.222 |
| home win | (0.2, 0.3] | 80 | 0.267 | 0.200 |
| home win | (0.3, 0.4] | 157 | 0.354 | 0.376 |
| home win | (0.4, 0.5] | 137 | 0.449 | 0.401 |
| home win | (0.5, 0.6] | 94 | 0.539 | 0.468 |
| home win | (0.6, 0.7] | 26 | 0.634 | 0.577 |
| home win | (0.7, 1.0] | 5 | 0.730 | 0.400 |
| draw | (0.0, 0.2] | 28 | 0.182 | 0.214 |
| draw | (0.2, 0.3] | 459 | 0.248 | 0.266 |
| draw | (0.3, 0.4] | 21 | 0.311 | 0.333 |
| away win | (0.0, 0.2] | 42 | 0.162 | 0.310 |
| away win | (0.2, 0.3] | 160 | 0.254 | 0.263 |
| away win | (0.3, 0.4] | 159 | 0.349 | 0.314 |
| away win | (0.4, 0.5] | 115 | 0.443 | 0.496 |
| away win | (0.5, 0.6] | 24 | 0.528 | 0.542 |
| away win | (0.6, 0.7] | 6 | 0.660 | 0.667 |
| away win | (0.7, 1.0] | 2 | 0.742 | 0.500 |
| over 2.5 | (0.3, 0.4] | 22 | 0.364 | 0.500 |
| over 2.5 | (0.4, 0.5] | 84 | 0.459 | 0.524 |
| over 2.5 | (0.5, 0.6] | 163 | 0.554 | 0.577 |
| over 2.5 | (0.6, 0.7] | 166 | 0.649 | 0.639 |
| over 2.5 | (0.7, 1.0] | 73 | 0.746 | 0.630 |

Goals per game, final three seasons: predicted 3.09, actual 3.12. Home win share predicted 0.414, actual 0.380; draws 0.247 against 0.266.

