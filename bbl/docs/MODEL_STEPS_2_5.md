# BBL model, steps 2 to 5 (21 Oct 2026): data layer, team model, player props, stand-in backtest

> **Correction (same day): the prop figures below were made with a leak.** Cricsheet lists each XI in the
> order it batted, and the prop model used that list position. Fixed, with a test; league adjustment then
> added. Current, leak-free figures: runs against the stand-in line on 2024/25, BBL +12.6% (-1.8% to +21.8%,
> 88 bets), WBBL +9.6% (-1.8% to +25.3%, 116 bets). Details in `docs/RESEARCH.md` sections 4 and 5. The data
> layer and team model sections are unaffected.

Everything here is built from Cricsheet alone (no odds yet). Every figure is from `python -m bbl.model.team`
and `python -m bbl.model.backtest` on the 21 Oct pull; the full reports are `TEAM.md` and `PROPS.md` on the
`bbl-history` release (the `bbl model` workflow rebuilds them).

**How the seasons are used.** Every BBL or WBBL season is predicted by models fitted only on club T20
games of the same gender that started before it (IPL, Blast, PSL, CPL, SA20 and the rest carry the
fitting, since a BBL season is ~44 games). Choices were made on **2022/23 and 2023/24** only, **2024/25**
confirms them, and **2025/26 is held back**, untouched, for one final score once nothing else will change
(`final=yes` on the `bbl model` workflow).

## Step 2: data layer

| table | rows | what |
|---|---|---|
| `player_frame` | 324,126 (BBL 14,613, WBBL 11,419) | one row per player per T20 match, all leagues, both genders |
| `team_frame` | 29,372 (BBL 1,324, WBBL 1,038) | one row per team per match |

- Checks on the real data: batter runs plus extras equal the innings total in all 1,324 BBL team-games;
  every batter in the ball-by-ball is in his side's XI; 98% of BBL player-games carry prior T20 history
  (median 48 prior games).
- Leakage: `bbl/tests/test_frame.py` changes a game's balls and result and checks that its own features
  do not move while later games' do, on a made-up league and on the real 2024/25 data. A second test
  checks a fixture not yet played is not counted as a game (it was, for venue and team game counts; fixed).
- Men's and women's clubs share names, so a side is keyed by name and gender.
- Ground names collapse to one each (the Gabba was under three). Super overs are left out of every figure.

## Step 3: team model

**Head-to-head is close to a coin flip on everything we can see.** Bits: 1 + log2(chance given to the
winner), averaged; 0 is a coin flip (AFL's model scores 0.15 to 0.24).

| | BBL choose (99 games) | BBL confirm (41) | WBBL choose (111) | WBBL confirm (40) |
|---|---|---|---|---|
| chosen model, bits | 0.062 | -0.020 | 0.036 | -0.100 |
| rating alone (Elo), bits | 0.054 | -0.041 | 0.036 | -0.064 |
| tips correct | 62.6% | 48.8% | 62.2% | 42.5% |

- Chosen on the choose seasons: the rating plus how often the side has played at the ground (a home
  signal that needs no fixture list), fitted on all club T20. Lineup strength, the toss, and who is in or
  out since the last game each scored at or below this, so **"teams named" uses the same inputs as "at the
  open" for win chance**. That is a finding, not a gap: by these measures team news does not move a T20
  result enough to see in ~100 games. The team-news test on recorded prices (step 6) checks it from the
  market's side.
- 2024/25 came out below a coin flip for both. 41 games is a small sample, and the honest reading is that
  we have no head-to-head edge to expect against a market that sees the same things.
- Likely improvement, not built: lineup strength treats a run in every league the same (a Nepal Premier
  League run counts as an IPL run). Rating each league's strength would give the XI features a fair test.

**Totals** (full first innings, no rain rule):

| | BBL choose | BBL confirm | WBBL choose | WBBL confirm |
|---|---|---|---|---|
| first-innings runs, average miss | 22.9 | 19.9 | 23.1 (named) | 20.2 (named) |
| the ground's own average, average miss | 22.9 | 19.9 | 24.7 | 21.6 |
| spread used (sd) | 28 | 29 | 27 | 28 |
| match runs, average miss | 43.0 (named) | 41.6 (named) | 38.0 | 33.7 |

For BBL nothing beat the ground's own running average, so BBL first-innings runs IS that average; WBBL
uses the full model, which beats it by about 1.5 runs. About 70% of results land within one sd, close to
the 68% a correct spread gives. Runs lines (handicaps) are not priced: a chase stops when it wins, and
Australian books rarely offer them; revisit if the probe finds them.

## Step 4: player props

Runs: P(bats) x a negative binomial for runs if he bats; sixes the same; wickets: P(bowls) x a negative
binomial if he bowls. Means from LightGBM on pre-game form (ewm over his last games in every league),
usual batting position, list order, both sides' strength and the ground. Spreads fitted per batting
position band. Each season's means are rescaled by how far off the model ran in EARLIER seasons of the
same competition (a BBL six is not an IPL six), so nothing is learned from the season being scored.
Top team batter: simulated from each player's distribution (ties dead-heated).

Against each player's last-10 average (the stand-in for how books are said to set lines), average miss:

| | BBL choose | BBL confirm | WBBL choose | WBBL confirm |
|---|---|---|---|---|
| runs: ours / last-10 | 17.8 / 18.3 | 17.5 / 17.8 | 15.8 / 16.5 | 15.6 / 16.3 |
| wickets: ours / last-10 | 0.86 / 0.90 | 0.85 / 0.89 | 0.84 / 0.88 | 0.80 / 0.86 |

Our distribution beats one centred on the last-10 average on every market and season (log-likelihood
gain 0.03 to 0.36 per player-game). Calibration is close for runs and wickets; **sixes run high** (we say
21% where 17.5% happens in the lowest band, 36% where 30% happens in the next) and need work before any
sixes price is trusted.

## Step 5: backtest against a stand-in line (a proxy, not a market test)

Runs only. Line = floor(k x last-10 average) + 0.5, k tuned on 2018/19-2021/22 so a blind over wins half
the time (it does: 50.1% BBL, 50.2% WBBL; 50.9% and 49.6% later). 1.87 both ways. Graded only if he batted.
Top-order batters (usual position 5 or higher, 10+ prior innings). Threshold chosen on the choose seasons.

| | bets | hit | ROI | 90% interval (game weeks resampled) |
|---|---|---|---|---|
| BBL choose (threshold 62%) | 192 | 62.0% | +15.9% | +7.0% to +25.0% |
| **BBL confirm 2024/25** | 96 | 60.4% | **+13.0%** | **-5.4% to +27.5%** |
| WBBL choose (threshold 60%) | 431 | 63.1% | +18.0% | +12.7% to +23.1% |
| **WBBL confirm 2024/25** | 138 | 62.3% | **+16.5%** | **+9.3% to +26.7%** |

**Read this as an upper bound, not an edge**, as with AFL: it says a better reading of form beats a plain
recent average, and real books are better than a plain average. BBL's confirm sample (96 bets, 8 weeks)
is too small to rule out zero. The test that matters is against recorded openers.

**Sixes and wickets have no reported return.** Their counts are too small for a fixed line at 1.87 (a
blind over on a WBBL sixes line wins about a fifth of the time), and a stand-in price built from a ten-game
average showed +40% to +70%, which is the stand-in failing, not an edge. They wait for real prices.

## Ready for the paper season (step 7), waiting on odds

- `bbl/live/price.py`: prices fixtures not yet played from a fixtures CSV (`bbl/live/fixtures_template.csv`)
  and, when known, the named XIs; a side with no named XI is priced on its last XI (the "at the open"
  price). Output: fair odds for head-to-head, first-innings and match runs, and per player the chance to
  bat, runs over 9.5 to 34.5, sixes, wickets and top team batter.
- `bbl/live/names.py`: maps a bookmaker's name ("Steve Smith") to Cricsheet's ("SPD Smith") within a
  side's recent players, refuses rather than guesses on two candidates, with a hand-kept override file.
- `bbl/live/compare.py`: reads a saved odds snapshot in The Odds API shape, no network call, and writes
  a paper list where our chance x price - 1 clears the edge. Only `h2h` is mapped; every other market key
  is reported as unmapped until the probe shows what it is.
- Step 6 (team-news repricing) needs prices recorded through the week; nothing to build until they exist.

## Open items

- `ODDS_API_KEY` secret, then the probe (up to 300 credits, your OK).
- Sixes calibration.
- League-strength adjustment for lineup features.
- 2025/26 final score, once every choice above is frozen.
- WBBL 2026/27 is close (WBBL 2025/26 ran 9 Nov to 13 Dec): the first paper season could be WBBL.
