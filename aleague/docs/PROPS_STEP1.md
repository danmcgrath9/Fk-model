# Player props, step 1: anytime scorer and player carded, out of sample

45,202 player-matches with minutes on the pitch, seasons 2017-2027; a named player who never came on is left out (a void bet at most books). Every rate from earlier matches only. Log loss, lower is better; differences with 90% intervals resampling weeks.

## anytime scorer (happened in 9.1% of player-matches)

| season | rows | model | raw rate | flat rate |
|---|---|---|---|---|
| 2016-17 | 3,817 | 0.2645 | 0.2688 | 0.3081 |
| 2017-18 | 3,773 | 0.2632 | 0.2654 | 0.3040 |
| 2018-19 | 3,812 | 0.2805 | 0.2854 | 0.3228 |
| 2019-20 | 4,101 | 0.2568 | 0.2606 | 0.2908 |
| 2020-21 | 4,683 | 0.2576 | 0.2607 | 0.2939 |
| 2021-22 | 4,796 | 0.2577 | 0.2617 | 0.2855 |
| 2022-23 | 4,891 | 0.2640 | 0.2689 | 0.2967 |
| 2023-24 | 5,032 | 0.2748 | 0.2772 | 0.3041 |
| 2024-25 | 5,330 | 0.2759 | 0.2805 | 0.3001 |
| 2025-26 | 4,878 | 0.2730 | 0.2767 | 0.2892 |
| 2026-27 | 89 | 0.2339 | 0.2373 | 0.2403 |

settings chosen on, 2016-17 to 2020-21: model minus raw rate -0.0037 (-0.0047 to -0.0025); model better.

settings chosen on, 2016-17 to 2020-21: model minus flat rate -0.0392 (-0.0426 to -0.0358); model better.

untouched test, 2021-22 on: model minus raw rate -0.0039 (-0.0049 to -0.0029); model better.

untouched test, 2021-22 on: model minus flat rate -0.0260 (-0.0288 to -0.0234); model better.

Calibration, test seasons:

| predicted band | rows | average predicted | happened |
|---|---|---|---|
| (0.0, 0.05] | 10,445 | 0.027 | 0.033 |
| (0.05, 0.1] | 7,555 | 0.072 | 0.077 |
| (0.1, 0.15] | 3,155 | 0.121 | 0.115 |
| (0.15, 0.2] | 1,581 | 0.173 | 0.183 |
| (0.2, 0.3] | 1,607 | 0.242 | 0.270 |
| (0.3, 0.4] | 520 | 0.339 | 0.315 |
| (0.4, 0.6] | 153 | 0.461 | 0.458 |

## player carded (yellow or red) (happened in 13.8% of player-matches)

| season | rows | model | raw rate | flat rate |
|---|---|---|---|---|
| 2016-17 | 3,817 | 0.4302 | 0.4399 | 0.4397 |
| 2017-18 | 3,773 | 0.4123 | 0.4194 | 0.4247 |
| 2018-19 | 3,812 | 0.4142 | 0.4197 | 0.4227 |
| 2019-20 | 4,101 | 0.3836 | 0.3924 | 0.3890 |
| 2020-21 | 4,683 | 0.3885 | 0.3943 | 0.4023 |
| 2021-22 | 4,796 | 0.3929 | 0.3997 | 0.3952 |
| 2022-23 | 4,891 | 0.4145 | 0.4206 | 0.4216 |
| 2023-24 | 5,032 | 0.3759 | 0.3803 | 0.3841 |
| 2024-25 | 5,330 | 0.3448 | 0.3452 | 0.3518 |
| 2025-26 | 4,878 | 0.3632 | 0.3671 | 0.3657 |
| 2026-27 | 89 | 0.4459 | 0.4686 | 0.4641 |

settings chosen on, 2016-17 to 2020-21: model minus raw rate -0.0074 (-0.0090 to -0.0058); model better.

settings chosen on, 2016-17 to 2020-21: model minus flat rate -0.0100 (-0.0121 to -0.0079); model better.

untouched test, 2021-22 on: model minus raw rate -0.0043 (-0.0059 to -0.0026); model better.

untouched test, 2021-22 on: model minus flat rate -0.0055 (-0.0072 to -0.0037); model better.

Calibration, test seasons:

| predicted band | rows | average predicted | happened |
|---|---|---|---|
| (0.0, 0.05] | 5,093 | 0.033 | 0.062 |
| (0.05, 0.1] | 6,768 | 0.075 | 0.100 |
| (0.1, 0.15] | 5,518 | 0.124 | 0.142 |
| (0.15, 0.2] | 4,524 | 0.174 | 0.176 |
| (0.2, 0.3] | 2,935 | 0.233 | 0.214 |
| (0.3, 0.4] | 178 | 0.321 | 0.270 |

## Verdict

Settings were chosen on 2016-17 to 2020-21 and then scored once on 2021-22 onwards.

- **Anytime scorer:** beats a player's raw goals-per-appearance rate in every test season
  (-0.0039 log loss, interval clear of zero) and is well calibrated across the range.
- **Player carded:** beats the raw rate in every test season (-0.0043) but is too spread: low-risk players
  are carded more often than predicted (3.3% predicted, 6.2% happened) and the highest band less often.
  A shrink of the card rates towards the league is the fix to make on the selection seasons and check on
  2026-27 as it is played.
- These are probabilities, not profit. A book's price beats the raw rate already; whether it beats ours
  is what the recorded prices will tell.
