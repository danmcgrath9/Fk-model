# Tails: are the big-game chances right?

From the walk-forward projections (every season predicted by models that never saw it). Scored on 2025-2026.

## One spread, or one per position?

Spread fitted on 2024, scored on 2025-2026. Change in log-likelihood per player-game from fitting it per position (higher is better), ± one standard error. Adopted where more than two standard errors better.

| stat | one spread | ruck | mid | fwd | def | gen | gain per position | adopted |
|---|---|---|---|---|---|---|---|---|
| disposals | 0.026 | 0.020 | 0.014 | 0.028 | 0.026 | 0.044 | +0.0017 ± 0.0006 | yes |
| marks | 0.064 | 0.002 | 0.092 | 0.052 | 0.062 | 0.098 | -0.0002 ± 0.0003 | no |
| tackles | 0.090 | 0.110 | 0.062 | 0.112 | 0.086 | 0.110 | +0.0003 ± 0.0002 | no |
| goals | 0.074 | 0.038 | 0.008 | 0.034 | 0.150 | 0.150 | +0.0001 ± 0.0002 | no |

## Milestones: reached minus our chance (2025-2026)

Positive: it happened more often than we said (our price too long). Each cell: gap, then our average chance. Rows with under 300 games are left out.

### Disposals

| position | games | 15+ | 20+ | 25+ | 30+ | 35+ |
|---|---|---|---|---|---|---|
| ruck | 1,130 | +0.019 (36%) | +0.020 (13%) | +0.005 (3%) | -0.001 (1%) | +0.001 (0%) |
| mid | 2,701 | +0.000 (92%) | +0.032 (71%) | +0.039 (41%) | +0.014 (18%) | -0.004 (6%) |
| fwd | 4,613 | +0.010 (29%) | +0.005 (9%) | +0.005 (3%) | -0.000 (1%) | -0.001 (0%) |
| def | 7,093 | +0.015 (59%) | +0.016 (31%) | +0.002 (13%) | -0.005 (4%) | -0.004 (1%) |
| gen | 2,984 | -0.001 (47%) | -0.004 (21%) | -0.008 (7%) | -0.008 (2%) | -0.004 (1%) |
| all | 18,521 | +0.009 (53%) | +0.013 (29%) | +0.007 (13%) | -0.001 (5%) | -0.003 (1%) |

### Marks

| position | games | 3+ | 5+ | 7+ | 9+ |
|---|---|---|---|---|---|
| ruck | 1,130 | -0.025 (50%) | -0.002 (20%) | -0.013 (7%) | -0.007 (2%) |
| mid | 2,701 | +0.004 (63%) | -0.003 (28%) | -0.002 (10%) | -0.004 (3%) |
| fwd | 4,613 | -0.006 (69%) | -0.008 (35%) | -0.006 (14%) | -0.003 (4%) |
| def | 7,093 | +0.000 (81%) | +0.002 (52%) | +0.003 (26%) | -0.002 (11%) |
| gen | 2,984 | -0.019 (58%) | -0.009 (24%) | +0.004 (7%) | +0.000 (2%) |
| all | 18,521 | -0.005 (70%) | -0.003 (38%) | -0.001 (16%) | -0.003 (6%) |

### Tackles

| position | games | 3+ | 5+ | 7+ | 9+ |
|---|---|---|---|---|---|
| ruck | 1,130 | -0.036 (53%) | -0.025 (22%) | -0.008 (7%) | -0.001 (2%) |
| mid | 2,701 | +0.016 (74%) | +0.016 (43%) | +0.004 (20%) | -0.001 (8%) |
| fwd | 4,613 | -0.004 (36%) | -0.001 (10%) | +0.001 (2%) | +0.000 (0%) |
| def | 7,093 | -0.005 (32%) | -0.004 (8%) | +0.000 (2%) | +0.001 (0%) |
| gen | 2,984 | -0.010 (50%) | +0.002 (20%) | +0.005 (6%) | +0.003 (2%) |
| all | 18,521 | -0.004 (43%) | -0.001 (17%) | +0.001 (6%) | +0.001 (2%) |

### Goals

| position | games | 1+ | 2+ | 3+ | 4+ |
|---|---|---|---|---|---|
| ruck | 1,130 | -0.016 (32%) | +0.001 (8%) | -0.003 (2%) | -0.003 (0%) |
| mid | 2,701 | -0.000 (37%) | +0.004 (10%) | +0.005 (3%) | +0.001 (1%) |
| fwd | 4,613 | +0.004 (68%) | +0.017 (36%) | +0.011 (16%) | -0.003 (7%) |
| def | 7,093 | -0.022 (14%) | -0.001 (2%) | +0.001 (0%) | +0.000 (0%) |
| gen | 2,984 | -0.027 (35%) | +0.008 (8%) | +0.005 (2%) | +0.000 (0%) |
| all | 18,521 | -0.013 (35%) | +0.006 (13%) | +0.005 (5%) | -0.001 (2%) |

## What this says

- Disposals: the spread now differs by position (a midfielder's game is steadier than a general player's), which is adopted in the walk-forward. Overall the milestone chances are within a point of what happened.
- Midfielders still reach 20+ and 25+ two to three points more often than we say. That is the level, not the spread: midfielders were under-projected by 0.3 disposals in 2026 (the year of the toss-up), and over-projected by 0.3 in 2023-24. A correction fitted on the season before (scale each projection by last season's actual over projected) helped 2024 and 2025 and hurt 2026 by more, so it is not adopted: last season's level is a poor guide in a rule-change year. The model's own league-level input follows it within a season.
- Marks, tackles, goals: one spread is enough; milestones within one to three points everywhere, with rucks the loosest (few games).

