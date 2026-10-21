# Tails: are the big-game chances right?

From the walk-forward projections (every season predicted by models that never saw it). Scored on 2025-2026.

## One spread, or one per position?

Spread fitted on 2024, scored on 2025-2026. Change in log-likelihood per player-game from fitting it per position (higher is better), ± one standard error. Adopted where more than two standard errors better.

| stat | one spread | ruck | mid | fwd | def | gen | gain per position | adopted |
|---|---|---|---|---|---|---|---|---|
| disposals | 0.026 | 0.022 | 0.014 | 0.030 | 0.026 | 0.046 | +0.0018 ± 0.0006 | yes |
| marks | 0.064 | 0.002 | 0.092 | 0.052 | 0.062 | 0.098 | -0.0003 ± 0.0003 | no |
| tackles | 0.090 | 0.110 | 0.062 | 0.114 | 0.088 | 0.110 | +0.0003 ± 0.0002 | no |
| goals | 0.084 | 0.066 | 0.020 | 0.040 | 0.150 | 0.150 | +0.0001 ± 0.0002 | no |

## Milestones: reached minus our chance (2025-2026)

Positive: it happened more often than we said (our price too long). Each cell: gap, then our average chance. Rows with under 300 games are left out.

### Disposals

| position | games | 15+ | 20+ | 25+ | 30+ | 35+ |
|---|---|---|---|---|---|---|
| ruck | 1,130 | -0.004 (39%) | +0.004 (14%) | -0.002 (4%) | -0.003 (1%) | +0.001 (0%) |
| mid | 2,701 | -0.004 (92%) | +0.023 (72%) | +0.030 (42%) | +0.009 (19%) | -0.006 (6%) |
| fwd | 4,613 | +0.005 (30%) | +0.003 (10%) | +0.004 (3%) | -0.001 (1%) | -0.001 (0%) |
| def | 7,093 | +0.005 (60%) | +0.008 (31%) | -0.002 (13%) | -0.006 (5%) | -0.005 (1%) |
| gen | 2,984 | -0.006 (48%) | -0.008 (21%) | -0.010 (7%) | -0.009 (2%) | -0.004 (1%) |
| all | 18,521 | +0.001 (54%) | +0.006 (29%) | +0.003 (13%) | -0.003 (5%) | -0.004 (2%) |

### Marks

| position | games | 3+ | 5+ | 7+ | 9+ |
|---|---|---|---|---|---|
| ruck | 1,130 | -0.031 (51%) | -0.005 (20%) | -0.013 (7%) | -0.007 (2%) |
| mid | 2,701 | +0.002 (63%) | -0.003 (28%) | -0.002 (10%) | -0.004 (3%) |
| fwd | 4,613 | -0.008 (69%) | -0.011 (35%) | -0.008 (14%) | -0.004 (5%) |
| def | 7,093 | -0.001 (82%) | -0.000 (52%) | +0.001 (26%) | -0.004 (11%) |
| gen | 2,984 | -0.023 (58%) | -0.012 (24%) | +0.003 (7%) | -0.000 (2%) |
| all | 18,521 | -0.008 (70%) | -0.006 (38%) | -0.002 (16%) | -0.003 (6%) |

### Tackles

| position | games | 3+ | 5+ | 7+ | 9+ |
|---|---|---|---|---|---|
| ruck | 1,130 | -0.040 (53%) | -0.028 (22%) | -0.009 (7%) | -0.001 (2%) |
| mid | 2,701 | +0.015 (74%) | +0.015 (43%) | +0.003 (21%) | -0.001 (8%) |
| fwd | 4,613 | -0.010 (37%) | -0.004 (11%) | -0.000 (3%) | -0.000 (1%) |
| def | 7,093 | -0.009 (32%) | -0.006 (8%) | -0.000 (2%) | +0.001 (0%) |
| gen | 2,984 | -0.014 (51%) | -0.001 (20%) | +0.004 (7%) | +0.003 (2%) |
| all | 18,521 | -0.008 (44%) | -0.003 (17%) | +0.001 (6%) | +0.001 (2%) |

### Goals

| position | games | 1+ | 2+ | 3+ | 4+ |
|---|---|---|---|---|---|
| ruck | 1,130 | -0.010 (32%) | +0.004 (7%) | -0.001 (2%) | -0.002 (0%) |
| mid | 2,701 | -0.001 (38%) | +0.004 (10%) | +0.006 (3%) | +0.001 (1%) |
| fwd | 4,613 | +0.004 (68%) | +0.018 (36%) | +0.012 (16%) | -0.003 (7%) |
| def | 7,093 | -0.011 (13%) | +0.001 (2%) | +0.002 (0%) | +0.000 (0%) |
| gen | 2,984 | -0.025 (35%) | +0.008 (8%) | +0.005 (2%) | +0.000 (0%) |
| all | 18,521 | -0.008 (35%) | +0.007 (13%) | +0.005 (5%) | -0.001 (2%) |

## What this says

- Disposals: the spread now differs by position (a midfielder's game is steadier than a general player's), which is adopted in the walk-forward. Overall the milestone chances are within a point of what happened.
- Midfielders still reach 20+ and 25+ two to three points more often than we say. That is the level, not the spread: midfielders were under-projected by 0.3 disposals in 2026 (the year of the toss-up), and over-projected by 0.3 in 2023-24. A correction fitted on the season before (scale each projection by last season's actual over projected) helped 2024 and 2025 and hurt 2026 by more, so it is not adopted: last season's level is a poor guide in a rule-change year. The model's own league-level input follows it within a season.
- Marks, tackles, goals: one spread is enough; milestones within one to three points everywhere, with rucks the loosest (few games).

