# AFL player props (started 21 Oct 2026)

A model that prices AFL player props (disposals first, then goals, marks, tackles) better than
books that set lines off recent averages. Separate from the racing code: everything lives in
`afl/` and the `afl-*` workflows, with its own data release (`afl-history`). No Form King key,
no BetMatic orders. Paper only until the founder says otherwise.

## Where it stands

| Step | What | Status |
|---|---|---|
| Data | AFL Tables + Footywire per-game player stats 2012-2026 from fitzRoy's GitHub mirror | done: 138,255 player-games, all matched |
| Data | Fryzigg advanced stats (incl. AFL Player Ratings, spoils, pressure, weather), Squiggle games and every model's tips | on the `afl-history` release: Fryzigg 2012-2025 (2026 not published yet), Squiggle games 2012-2026, tips 2017-2025 |
| Data | Footywire betting odds | failed every season ("cannot open the connection": Footywire refuses GitHub's runners); The Odds API covers odds from 2020 |
| 1. Projection | disposals: time on ground x disposals per full game, and a direct model, on pre-game features | done, see `docs/DISPOSALS_STEP1.md` |
| 2. Probabilities | negative binomial around the projection, spread fitted on 2024 | done for disposals |
| 3. Backtest | against STAND-IN lines (recent averages), 2025 and 2026 unseen | done; real lines do not exist yet |
| 3. Backtest | against real opening and closing lines | needs recorded lines (round 1 2027) or a paid source |
| 4. Team-news repricing test | measurable from recorded prices only | from round 1 2027 |
| 5. Paper season | record openers, compare with projection and close | from round 1 2027 |
| Team model | margin, win chance and total per game, at the open (no team news) and with teams named | first cut done, see `docs/TEAM_STEP1.md` |
| Goals, marks, tackles | same machinery, count models | not started |
| Weather | rain and wind by ground | not started; Open-Meteo history may need a paid plan for this use, BOM is the free alternative |

## Disposals, step 1 results (2025 and 2026, never seen in fitting or tuning)

Projection miss per player-game: 3.74 and 3.72 disposals, against 3.86 and 3.85 for the
player's last-10 average (the nearest thing to how books are said to set lines).

Against a stand-in line built from each player's last-10 average (tuned on 2024 so a blind
over wins half the time, which it does in 2025 and 2026), at 1.87 each way:

| season | bets taken at 56%+ | hit rate | ROI | 90% interval (rounds resampled) |
|---|---|---|---|---|
| 2025 | 5,275 | 62.0% | +16.0% | +13.7% to +18.4% |
| 2026 | 5,567 | 62.6% | +17.1% | +14.6% to +19.4% |

**Read this as an upper bound, not an edge.** It says a better reading of form (recency
weighting, time on ground, disposals per minute on the ground) beats a plain recent average by
a lot. Real books see the same team news and some will price better than a plain average, so
the real figure can only be smaller, and may be zero. The edge is biggest on small lines
(under 15: +19%) and smallest on the 25.5+ lines that are the main markets (+9%). The test
that matters is against recorded openers.

What drives the projection: an exponentially weighted disposals average (68% of the direct
model's gain), then disposals per full game on the ground, then the player's share of his
team's usual disposals. Team news (outs), opponent, ground and expected margin each add a
little. That is honest: most of the signal is form, read better.

## Team model, first cut (scored against Squiggle's 30-odd public models)

| season | ours, teams named | ours, at the open | Wheelo Ratings | Punters (the betting market) |
|---|---|---|---|---|
| 2024, bits per game (rank) | 0.147 (4th) | 0.139 (7th) | 0.155 (2nd) | 0.134 (12th) |
| 2025, bits per game (rank) | 0.229 (7th) | 0.224 (9th) | 0.232 (4th) | 0.239 (1st) |
| 2026, bits per game (rank) | 0.232 (15th) | 0.240 (7th) | 0.237 (11th) | 0.246 (3rd) |

Bits: Squiggle's score for a win probability (higher is better). Competitive with the public models,
roughly level with Wheelo over three seasons, behind the market in two of them. Team news does not help yet: in games
where the named 22 moved our margin by 6+ points, the named prediction missed by more (25.8 against
24.9), so the lineup-strength measure (recent SuperCoach) is not good enough. Next: AFL Player Ratings
from Fryzigg, a proper expected-22 at the open, and the test that matters, against real opening lines.

## Data sources and their terms (checked 21 Oct 2026)

| Source | What we take | How | Terms |
|---|---|---|---|
| AFL Tables, Footywire player stats | per-game stats 2012-2026 | fitzRoy's own mirror on GitHub (`jimmyday12/fitzRoy_data`): no request to either site | no published terms found |
| Footywire betting odds | head-to-head and line per game | one page per season, 5 s apart | no published terms found |
| Fryzigg | advanced per-game stats | one API call per season, 5 s apart | free API built for fitzRoy; no terms found |
| Squiggle | games and every model's tips | one call per season per query, identified by User-Agent | free; asks bots to identify themselves and cache |
| AFL website / API | nothing | not used | its terms of use reportedly prohibit downloading and reuse |

Each run of `afl data` records every site's robots.txt on its run page. Nothing is pulled twice:
a file on the release is downloaded, not re-fetched (the `refresh` input re-pulls a named season,
for in-season updates).

To identify us to Squiggle, set the repository variable `AFL_CONTACT` (Settings > Secrets and
variables > Actions > Variables) to a contact, e.g. an email. Without it the User-Agent says
"fk-model AFL research".

## Running it

```
pip install -r afl/requirements.txt
gh release download afl-history --dir afl/cache          # or: python afl/data/mirror.py --out afl/cache
python -m afl.model.frame afl/cache                       # features -> afl/cache/frame.parquet
python -m afl.model.disposals afl/cache afl/docs/DISPOSALS_STEP1.md
python -m pytest afl/tests                                # leakage tests (need afl/cache)
```

## Risks to keep in front of us

- **Limits.** Prop limits are small and books restrict winning accounts quickly; the edge is
  worth only what can be staked.
- **Late outs and subs.** A player who does not take the field usually voids the bet; one subbed
  off injured usually does not, and loses the over. Each book's rule needs checking. In 2021-25
  the named sub was known before the bounce (excluded here); the 2026 data carries no sub flag.
- **2026 rule changes** (ball toss-up instead of the bounce, ruck changes) moved the league's
  disposal levels; the model sees this through the league average of recent games, but it has
  only one season of the new rules.
- **Proxy lines.** Every result so far is against stand-in lines. Do not stake on them.
