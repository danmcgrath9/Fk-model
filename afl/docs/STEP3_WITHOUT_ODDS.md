# AFL, step 3: everything that could be done before the odds (21 Oct 2026)

## The market is free for team betting, and it is better than us
Squiggle publishes "Punters", the betting market's own win chance and margin, for every game since 2017. Against it:

| season | market bits | ours | blend | market margin miss | ours | blend |
|---|---|---|---|---|---|---|
| 2024 | 0.134 | 0.134 | 0.135 | 26.8 | 26.8 | 26.8 |
| 2025 | 0.239 | 0.223 | 0.240 | 26.2 | 26.8 | 26.1 |
| 2026 | 0.246 | 0.236 | 0.247 | 25.0 | 25.3 | 24.9 |

The best blend (chosen on 2018-2023) puts only 10% weight on our model, and adds +0.0012 ± 0.0010 bits a game to the
market over 650 games: nothing detectable. Head-to-head and line markets are as sharp as expected. Team-market effort
stops here until real line history can test totals and opening-vs-closing moves; props are where the work goes.

## Weather: small, consistent, worth keeping
Fryzigg's match weather (2012-2025; 25% of games tagged rain). Each prop model refitted with and without it, scored on
2024-2025 (2026 has no weather yet):

| stat | wet vs dry, per player-game | gain with weather (log-lik per player-game) |
|---|---|---|
| disposals | 16.46 vs 16.68 | +0.0004 ± 0.0002 |
| marks | 3.99 vs 4.15 | +0.0007 ± 0.0004 |
| tackles | 2.89 vs 2.83 | +0.0006 ± 0.0003 |
| goals | 0.53 vs 0.57 | +0.0004 ± 0.0002 |

About two standard errors each way, all the same direction: real but small. For 2027 it needs a forecast source
(Fryzigg's tag ends at 2025; BOM forecasts are the free candidate). The market's expected margin, tried in place of our
results-only margin, did not help the props.

## Correlation, for staking caps
Disposal surprises (actual minus our projection), 2025-2026, same game:
- teammates +0.031 (189,042 pairs); opponents -0.015 (395,374 pairs). Five overs on five teammates behave like about
  4.5 independent bets, so stacking teammates is a smaller problem than feared.
- a team's total disposal surprise against its margin: +0.39 (868 team-games). A player over plus a line bet on his team
  are partly the same bet: that is the pair to cap together.

## Ready for the odds
- `afl/model/walkforward.py`: every 2023-2026 player-game projected by a model that never saw that season, for disposals,
  marks, tackles and goals, with each season's spread.
- `afl/lines/odds_api.py`: the historical pull, capped, resumable (a call already saved is never bought again), priced by
  dry run with no key. 2023-2026: lean (disposals, open and close) ~16,000 credits; standard (four props at 72h/12h/close
  + team markets at 72h/close) ~149,000; full (seven snapshots) ~407,000.
- `afl/lines/parse.py`: the API's names to ours (clubs by longest matching name, players within the two sides that
  played, never guessed when ambiguous).
- `afl/lines/backtest.py`: ROI at the open and at the close, closing line value, by book, line size and season, against
  the walk-forward projections. Tested end to end on responses in the API's documented shape (afl/tests/test_lines.py).
- The `afl lines` workflow runs the probe once when the key exists, and a pull only when `afl/lines/PULL.json` is enabled
  with a new run_id. Nothing is spent until then.

## The price sheet
`python -m afl.sheet afl/cache 2026 24` writes every game's margin, win chance and total, and every player's disposals,
marks and tackles line (our median) with fair over/under prices, anytime and 2+ goals, for any past round, out of sample
(docs/SHEET_2026_R24.md, with actual results beside it). For 2027 it needs a live named-teams source: the AFL site's
terms rule out its API, so that source is still to be chosen.
