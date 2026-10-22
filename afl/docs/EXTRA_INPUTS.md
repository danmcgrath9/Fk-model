# Extra inputs: which earn a place

Per stat, fitted 2013-2023, tuned on 2024, scored on 2025-2026 (never seen). Each row adds one group to the current model; "all extra" adds every group. Change in log-likelihood per player-game (higher is better) and in average miss, paired, ± one standard error. Kept: more than two standard errors better. Weather exists to 2025 only, so its 2026 rows carry no weather (the model treats it as unknown).

## Disposals

Current model: average miss 3.725.

| added | log-lik change | average miss change | kept |
|---|---|---|---|
| opponent by position | +0.0011 ± 0.0004 | -0.004 ± 0.002 | yes |
| weather | -0.0035 ± 0.0006 | +0.020 ± 0.003 | no |
| returning / dead rubber | +0.0003 ± 0.0003 | -0.001 ± 0.001 | no |
| player vs this opponent | +0.0004 ± 0.0003 | -0.001 ± 0.001 | no |
| player at this ground | +0.0002 ± 0.0002 | -0.001 ± 0.001 | no |
| interstate travel | +0.0003 ± 0.0003 | -0.003 ± 0.001 | no |
| all extra | -0.0015 ± 0.0007 | +0.011 ± 0.003 |  |
| **kept groups together** | +0.0011 ± 0.0004 | -0.004 | |

## Marks

Current model: average miss 1.782.

| added | log-lik change | average miss change | kept |
|---|---|---|---|
| opponent by position | +0.0011 ± 0.0003 | -0.003 ± 0.001 | yes |
| weather | +0.0011 ± 0.0004 | +0.000 ± 0.001 | yes |
| returning / dead rubber | +0.0004 ± 0.0002 | -0.001 ± 0.000 | no |
| player vs this opponent | +0.0006 ± 0.0003 | -0.001 ± 0.001 | yes |
| player at this ground | +0.0005 ± 0.0003 | -0.000 ± 0.001 | no |
| interstate travel | +0.0008 ± 0.0003 | -0.000 ± 0.001 | yes |
| all extra | +0.0032 ± 0.0005 | -0.007 ± 0.001 |  |
| **kept groups together** | +0.0034 ± 0.0005 | -0.005 | |

## Tackles

Current model: average miss 1.419.

| added | log-lik change | average miss change | kept |
|---|---|---|---|
| opponent by position | -0.0005 ± 0.0002 | +0.001 ± 0.000 | no |
| weather | +0.0004 ± 0.0003 | -0.003 ± 0.001 | no |
| returning / dead rubber | -0.0002 ± 0.0002 | +0.000 ± 0.000 | no |
| player vs this opponent | -0.0003 ± 0.0002 | +0.001 ± 0.000 | no |
| player at this ground | -0.0006 ± 0.0002 | +0.001 ± 0.000 | no |
| interstate travel | -0.0004 ± 0.0002 | +0.001 ± 0.000 | no |
| all extra | +0.0003 ± 0.0003 | -0.003 ± 0.001 |  |

## Goals

Current model: average miss 0.530.

| added | log-lik change | average miss change | kept |
|---|---|---|---|
| opponent by position | +0.0004 ± 0.0002 | -0.000 ± 0.000 | no |
| weather | +0.0001 ± 0.0002 | +0.000 ± 0.000 | no |
| returning / dead rubber | +0.0000 ± 0.0002 | +0.000 ± 0.000 | no |
| player vs this opponent | +0.0002 ± 0.0002 | -0.000 ± 0.000 | no |
| player at this ground | +0.0001 ± 0.0002 | -0.000 ± 0.000 | no |
| interstate travel | +0.0001 ± 0.0002 | -0.000 ± 0.000 | no |
| all extra | -0.0000 ± 0.0003 | -0.001 ± 0.000 |  |

## Kept, per stat

- disposals: D_opp_pos_rel, pos_ruck, pos_mid, pos_fwd, pos_def, pos_gen
- marks: M_opp_pos_rel, pos_ruck, pos_mid, pos_fwd, pos_def, pos_gen, wet, windy, roof, temp, M_vs_opp, interstate
- tackles: none
- goals: none
