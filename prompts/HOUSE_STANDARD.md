# House standard for sports models

The premise, the same as our racing model in danmcgrath9/Fk-model. Every sports session reads this first. Everything
not written here (when to bet, staking, caps, filters, which markets) is the sport's own call, decided from its own data.

## The premise
- **Price it ourselves.** Turn every market into our own probability for each outcome, and so our own price
  (1 / probability). A probability for every outcome, not a pick.
- **Bet only when the bookie's price beats ours by enough.** That is the whole strategy. Where, when and how much is
  for each sport to find out: the opener, after teams are named, or close to the start, whichever its data supports.
- **Prove it before money goes on.** Out-of-sample only: train on older seasons, test on newer ones the model never saw.
  Report ROI, closing line value (our price against the closing price) and losing runs, bootstrap the profit, and say
  when the sample is too small. A stand-in line is fine before real lines exist, labelled as a proxy.
- **No leakage.** Every input must be knowable at the time of the bet, and a test proves a game's own result never
  reaches its features.
- **Paper first, then small real stakes.**

Racing, for scale (docs/BACKTEST.md on main, 21 Oct 2026): +65% at the average opening price (an upper bound, since no
one can take the average opener as one bet) and about +5% at Betfair SP.

## House rules (every sport)
- Nothing goes to BetMatic, and no real bet is placed, without the founder's OK in chat on the exact list.
- Keys and passwords live only in GitHub secrets, never in chat or the repo.
- Every sport has its own folder, branch, workflows and data release, separate from racing and the other sports.
- Facts from the data, not guesses. Every number traces to code that was run.
- Tell the founder what anything costs before paying for it.
