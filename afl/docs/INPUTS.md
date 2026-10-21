# What the props models use, and what each part is worth (21 Oct 2026)

## Disposals: each group of inputs removed in turn, scored on 2025-2026 (never seen)
Average miss with everything: 3.73 disposals per player-game (a plain last-10 average: 3.86). Groups overlap, so
removing one is partly covered by another; the size of the hit is what that group adds on top of the rest.

| group | inputs | miss without it | log-lik without it |
|---|---|---|---|
| form | last 3/5/10/20, season average, recency-weighted average, trend, consistency | +0.021 ± 0.004 | -0.0056 ± 0.0008 |
| opponent | disposals and uncontested ball conceded vs the league, tackle pressure | +0.010 ± 0.002 | -0.0026 ± 0.0005 |
| role | centre clearances, contested ball, kick/handball mix, inside/rebound 50s, intercepts, ruck | +0.009 ± 0.003 | -0.0026 ± 0.0007 |
| teammates | share of the team's usual ball, who is in and out, number of mids | +0.007 ± 0.003 | -0.0018 ± 0.0006 |
| game | expected margin, blowout risk, home, venue, league trend, finals | +0.005 ± 0.003 | -0.0016 ± 0.0006 |
| time on ground | recent time on ground, disposals per full game, subbed last week | +0.003 ± 0.003 | -0.0005 ± 0.0006 |
| player | age, experience, days' rest | +0.003 ± 0.002 | -0.0005 ± 0.0004 |

## Extra inputs, tested per prop (docs/EXTRA_INPUTS.md); kept only if more than two standard errors better
| input | disposals | marks | tackles | goals |
|---|---|---|---|---|
| opponent by position (what this opponent concedes to mids, defenders, forwards, rucks; position from the player's own role stats) | kept | kept | no | no |
| weather (rain, wind, roof, temperature) | no* | kept | no | no |
| returning from absence, dead rubbers | no | no | no | no |
| player's record against this opponent | no | kept | no | no |
| player's record at this ground | no | no | no | no |
| interstate travel | no | kept | no | no |

\*Weather hurt disposals on the test only because 2026 has no weather yet (Fryzigg's tag ends at 2025), so the model
met it missing in every 2026 game. On 2024-2025, where it exists, it helped a little. It goes back in once 2026 weather is
sourced.

## Unseen-season accuracy after the kept inputs (afl/model/walkforward.py, average miss per player-game)
| season | disposals | marks | tackles | goals |
|---|---|---|---|---|
| 2025 | 3.74 | 1.78 | 1.44 | 0.53 |
| 2026 | 3.71 | 1.77 | 1.40 | 0.53 |

## Not in yet, and why
- **Centre bounce attendances**: the clearest role signal. Tracked from 2020 by DFS Australia and FootyInfo; both
  unreachable from here, terms unchecked, and the bounce itself was replaced by a toss-up in 2026. Stand-in: the player's
  share of his team's centre clearances (in the role group).
- **Taggers and individual matchups**: no data source.
- **Named teams live**: history knows who played; 2027 needs Thursday's named teams. The AFL site's terms rule out its
  API; candidates to check: ESPN/bets.com.au round pages (terms), or the players the books price (the Odds API).
- **Weather forecasts for 2027**: BOM's free feed bars commercial use under its default terms; its Registered User
  service is the paid route. Founder's call.
