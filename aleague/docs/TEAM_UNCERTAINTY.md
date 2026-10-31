# Parameter uncertainty in the expected goals (tested 31 Oct 2026, not adopted)

Idea (from a syndicate write-up): price each match over a spread of expected goals rather than the single
best estimate, log lambda ~ Normal(log lambda_hat, sigma^2) for each side independently, integrated exactly
(9-point Gauss-Hermite on each side, mean-preserving). It should pull probabilities towards the middle,
which is where step 1 found the model weak (strong favourites overrated).

| sigma | h2h log loss 2015-16 to 2019-20 (choice) | 2020-21 to 2022-23 | 2023-24 to 2025-26 | over 2.5, choice seasons |
|---|---|---|---|---|
| 0 (current) | 1.0075 | 1.0565 | 1.0688 | 0.6709 |
| 0.1 | 1.0076 | 1.0564 | 1.0687 | 0.6710 |
| 0.2 | 1.0079 | 1.0561 | 1.0685 | 0.6716 |
| 0.3 | 1.0085 | 1.0558 | 1.0682 | 0.6727 |

Chosen on the first seasons: sigma 0, so not adopted. The later gains are at most 0.0007 a match, noise.
The ridge penalty and the early-season shrink already pull strengths to average, which does the same job.
Where uncertainty does belong is staking: fractional Kelly and a minimum edge (model/benter.py).

Also from the same write-up, and why not: a Monte Carlo of a million matches adds sampling noise to the
exact score matrix we already compute; bivariate Poisson and machine learning were covered by the
literature review (docs/RESEARCH.md: no reliable gain for goals-only models).
