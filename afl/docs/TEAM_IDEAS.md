# Results-only rating: learning from scoring shots, and travel

Chosen on 2018-2023 by average margin miss; scored once on 2024-2026. Win chance = normal around the margin, spread 34.9. Bits: Squiggle's score (higher is better). Punters = the betting market.

| rating | 2024-26 margin miss | bits per game | change in bits vs current | ± |
|---|---|---|---|---|
| current rating (K 0.08, carry 0.7, no shots, no travel) | 26.33 | 0.1984 | +0.0000 | 0.0000 |
| best without shots (K 0.08, carry 0.6, travel 0.0) | 26.36 | 0.1933 | -0.0051 | 0.0025 |
| best without travel (K 0.08, carry 0.6, shots 0.75) | 26.39 | 0.1902 | -0.0082 | 0.0056 |
| best overall (K 0.08, carry 0.6, shots weight 0.75, home 6.0, travel 0.0) | 26.39 | 0.1902 | -0.0082 | 0.0056 |
| Punters (market), same games where present (650) | 25.98 | 0.2064 | | |

Shots weight 1 means the rating learns from the shot margin alone; 0 from the score alone.

## Verdict

Neither idea earns a place. The settings chosen on 2018-2023 (learn three quarters from the shot margin) did worse on
2024-2026 than the current rating, and travel added nothing once the rating was refitted. The market still beats every
results-only rating by about 0.01 bits a game; for the props, the market's margin is tested as an input in
docs/RESEARCH_TESTS.md instead.
