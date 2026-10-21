# House standard for sports models

Written 21 Oct 2026 from the horse-racing model in danmcgrath9/Fk-model and adapted for sports. Every sports session
reads this first.

**Two kinds of rule here.** The *house rules* (section 5) and the *method* (price it, bet the opener, judge by CLV,
out-of-sample only) hold for every sport. **Everything else is the sport's own call**: staking fractions, caps, edge
thresholds, price bands, blocks, multipliers. The figures below are racing's, or a starting point where a sport has no
evidence yet; each sport replaces them with its own rules, proved on its own held-out data and written into its own README.

## 1. The one idea
We don't try to pick winners. We price every outcome ourselves and bet only when the bookie's price beats ours by enough.
The edge is **getting on early**, at the opening price, before the market corrects. **The proof is closing line value (CLV)**:
our taken price against the closing price, bet by bet.

Racing, for scale (docs/BACKTEST.md on main, 21 Oct 2026, the value_ev20 plan, 3,512 bets out of sample): **+65% at the
average opening price, about +5% at Betfair SP.** Read the opening figure as an upper bound: the average opener is not a
price anyone can take as one bet, and the live paper book, betting later than the open, has done worse. Quote it that
way, never as a result.

A sports model is built and judged the same way: price it, bet the opener, measure CLV. Every sport proves this for itself.

## 2. The pipeline (the shape holds for every sport; the settings are each sport's)
1. **Data in, stored once.** Pull once, keep it (parquet on the sport's GitHub release), never re-pull what we hold.
   Results settle everything.
2. **Features known before the event only.** Every input knowable at bet time; a game's own result never leaks into its
   features (a test proves it); train and test split by season, never at random.
3. **Model → probability for every outcome.** A probability, not a pick, summing to 1 across each market's outcomes (both
   sides of an over/under, all three of a soccer result). Props get a full distribution (e.g. disposals = time on ground ×
   rate, goals and tries as count models) so any line can be priced.
4. **Market blend: fitted per sport, never copied.** Racing's live price is model^0.15 × forecast-close^0.85. That weight
   was fitted on racing. A sport gets a blend only once it has (a) a forecast of the close, which needs recorded price
   paths, and (b) weights fitted on its own held-out data. Until then a sport prices on its model alone, at reduced
   stakes (section 3).
5. **Our price = 1 / probability.** An order goes in only where the bookie beats our price by the sport's edge threshold.
6. **Blocks.** Rules that remove bets the backtest showed lose. Racing's blocks (first starters, first-up, bounce off a
   career-best, early-only over $8, nothing at 3× our price) are racing's. Each sport finds its own and proves each on
   held-out data before it becomes a rule. Candidates: late outs and team changes after the open, players named as subs
   or likely to be rested, garbage-time minutes (NBA, NBL), wet weather, dead rubbers late in a season, players returning
   from injury on limited minutes.
7. **Orders at the open.** BetMatic Market Open orders with a minimum price, so they fire only if the opener is big enough.
   Never chase a price after the market has moved. Check that BetMatic fills the sport's markets this way before relying on it.

## 3. Units and staking (starting points: each sport sets its own)
- **A unit is a fixed dollar amount set by the founder** (racing: $25). Everything is recorded in units.
- **Stake = fractional Kelly.** Racing uses 5/8 of Kelly. A sport picks its own fraction; until it has a fitted market
  blend, start lower (e.g. 1/4), because a model-only price has more error.
- **Cap per bet:** racing's is 10 units (public Twitter stake halved, max 5u). A sport sets its own.
- **Edge threshold per market, not racing's $1.60 to $15 price filter.** Prop lines sit near $1.85 each way and try scorers
  run $1.50 to $10, so each market gets its own minimum edge (and, where the backtest shows it, its own price band), set
  on held-out data.
- **Correlation caps: every sport needs some, the numbers are its own.** Runners in a race exclude each other; bets in
  one game don't. Five overs on one team's players are largely one bet on the game. Each sport sets, and justifies:
  - a cap per game across all its markets;
  - a rule per player across markets (disposals and fantasy points on the same player are close to the same bet twice);
  - how same-direction bets on teammates, and a team total plus that team's player overs, are capped together.
- **Firm/drift multipliers and ladders: after the paper season.** Both need a season of recorded openers and closes for that
  sport. Ladders also need BetMatic to fill the sport's markets in steps.
- **Banks: founder's call, pending.** Proposal: a separate bank per sport (125 units each) so one bad weekend in one sport
  can't eat the racing bank, plus a total open-exposure cap across every sport and racing. While a sport is on paper it
  doesn't matter yet; decide before the first real stake.

## 4. How we know it works
- **Out-of-sample only.** Oldest seasons to find angles, the next to confirm, the newest untouched until the final check.
  Anything that works on one season only is dropped.
- Report bets, strike rate, ROI at the open, ROI at the close, CLV, longest losing run, worst month. Bootstrap the profit
  by round so a lucky streak can't pass for an edge. Say when a sample is too small.
- **Break it down** by market or stat, line size or price band, and bookie.
- **Stand-in lines are not a market test.** Before real line history exists, a recent-average line may stand in, labelled
  as a proxy and treated as an upper bound.
- **ROI matters more than losing runs.** Long losing runs happen; expect them.
- **Paper first, then small real stakes.** A season of paper openers against the close, then live small.

## 5. Rules of the house
- Nothing goes to BetMatic without the founder's OK in chat on the exact list. Dry run first.
- A bet that's been taken is never dropped. A tip is locked once it's tweeted.
- Quote prices after deductions and rules: racing scratchings; for sports, each book's void rule for a player who doesn't
  take the field, its rule for a player subbed off, dead heats, and abandoned or shortened games.
- Facts from the data, not guesses. If the sample is too small, say so.
- Keys and passwords live only in GitHub secrets, never in chat or the repo.
- Every sport gets its own folder, branch, workflows (afl-*, nrl-*, nbl-*, bbl-*, aleague-*, nba-*) and data release,
  separate from racing and from each other.
- Limits are the real ceiling: books restrict winning accounts across every sport at once.
