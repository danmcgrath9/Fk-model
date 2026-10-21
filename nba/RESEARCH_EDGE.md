# Where an NBA props edge could come from (research, 21 Oct 2026)

Question: after our own tests showed the closing line beats our model, what do the best
prop bettors and the published evidence say about how to make a profit, and what can we
test?

**Honest note on the evidence.** I found no peer-reviewed study of NBA player-prop market
efficiency. Almost everything published is practitioner writing (Unabated, betting
blogs), much of it from people selling tools or tips. Each claim below is marked with how
much it can be trusted. Our own numbers are from code in this folder.

## What our own data already says

| Finding | Source |
|---|---|
| The line (roughly the close, median of 6-7 books) beats our model on points and assists and ties on rebounds and threes | `line_test_at_report.py` |
| Betting our side at every hour loses 4-6%; the +4.9% only exists if you know who actually played | same |
| A season average is already within 5% of the line on points; the line's real lead over it is 0.3 points a game, and we close 28% of that gap | chat, 21 Oct |
| Lines lean over: unders win 52.7%, but backing every under still loses 2.9% at median prices | `line_test.py` |

So at the close, there is no edge for us. Everything below is about where else to look.

## What the evidence says, ranked by how useful it is to us

**1. Bet early, not at the close (the main lead).** Several practitioner sources say the
softest prices are the first ones posted, before injury news and sharp money move them;
"one or two books move instantly, others need a few minutes" (Bettopia, one blog). Props
post on game day, usually from morning to early afternoon US time, some books later
(Bovada's own schedule: by 11am or 2 hours before tip; Sports Insights: no set time,
widely available early afternoon). *Trust: medium: consistent across sources, no study.*
This matches the racing edge (beat the opening price) and is the one thing our tests have
not been able to check, because DunkAPI holds one capture per line.

**2. Injury-news lag.** The line moves in stages as news lands (official report, beat
writers, pregame confirmation). One blogger's own tracking says the market prices about
80% of a star's absence within the first hour, slower for role players; another says
bench-player absences are undervalued. *Trust: low: single unpublished estimates.* But it
is directly testable: we now hold the official report at every hour, and The Odds API has
prices every 5 minutes, so we can measure how long a line takes to move after a status
changes. No model needed.

**3. Line shopping.** Prop margins are high (one guide: 6-10% hold, against ~4.8% on a
spread), and books disagree more on props than on game lines. Taking the best price
instead of the median adds an estimated 1-3% ROI (several guides, rough figures). *Trust:
medium on direction, low on size.* Our tests used DunkAPI's median price, so they
understate what a multi-book bettor gets. Any real edge will need this on top.

**4. Teammate-out redistribution.** Pros build two projection sets, with and without a
doubtful player, and reallocate his minutes and shots to specific teammates, not evenly
(Unabated, OddsShopper). *Trust: medium.* Our model does a crude version (vacated minutes,
share of the team's 240); a player-specific version is a known improvement.

**5. Same-game multis / correlation. Not recommended.** Claims that books misprice
correlation are blog-level, effective margins on SGMs are said to be 15-30%, and the one
academic paper found (arXiv 2607.14430, on prediction markets) argues parlay overpricing
is NOT explained by correlation. *Trust: low.*

## What will cap any edge

- **Limits.** "Getting limited on props is very easy to do if you show any resemblance
  of being sharp" (Unabated). BetMatic's Thomas expects bets at the open to be rejected.
  Australian minimum-bet rules appear to cover racing only (WA guidance; ACT sports
  bookmaking rules exist but were not checked), so a book can cap a winning sports
  punter. Australia's 2023 parliamentary inquiry questioned bookmakers on exactly this.
- **CLV is a weak scorecard for props.** Few books make prop markets, so the close is
  not a reliable "true price" (Unabated). Judge on ROI over a big out-of-sample run, and
  on Pinnacle's close where it exists.
- **New NBA rules this season (from 20 Oct 2026).** The league told its US partners
  (DraftKings, FanDuel, Fanatics, Caesars) to drop same-player under parlays, unders on
  players expected to play under 12 minutes, alternate under lines with bigger payouts,
  and opening-tip bets. Straight overs and unders on regular players are unaffected.
  Whether Australian books follow is not reported.
- **No exchange route for us.** Polymarket was blocked in Australia by ACMA in August
  2025 and Kalshi geoblocks Australia; Betfair Australia lists basketball, but no source
  shows liquid NBA player markets.
- Joel Williams says his edge is situational knowledge and pricing his own markets; no
  public detail on props. *Self-reported.*

## What to test, and what it costs

One month of The Odds API historical data (5M-credit plan, about US$119 by third-party
listings, not confirmed on their site) answers four questions with one pull:

| Question | How | Needs a model? |
|---|---|---|
| Is the opening line beatable? | Our projection from the injury report filed before the open, against the opening line and price | yes (have it) |
| Do lines lag injury news? | Line moves in the 5-minute snapshots after a report status change | no |
| How much does shopping add? | Best price across books vs the median, same bets | no |
| Which books open softest? | Each book's opener vs the later consensus | no |

Rough size: 4 stats x 2 regions (US, AU if held) x 10 credits = 80 credits per snapshot
per game; ~8 snapshots a game over 2024/25-2025/26 (~2,460 games) is about 1.6M credits.

Free alongside: BetMatic's NBA beta (about a week away) to record Australian books' own
openers from now on, paper only.

## Sources

- Unabated: [Getting precise about CLV](https://unabated.com/post/getting-precise-about-closing-line-value), [NBA prop strategy](https://unabated.com/post/fine-tune-your-nba-prop-betting-strategy-using-unabated-nba), [NBA path to profitability](https://unabated.com/post/nba-betting-path-to-profitability)
- Posting times: [Bovada schedule](https://www.bovada.lv/help/sports-faq/odds-posting-schedule), [Sports Insights](https://sportsinsights.zendesk.com/hc/en-us/articles/360036438171-What-time-are-player-props-added-to-the-tool), [SBR forum](https://www.sportsbookreview.com/forum/players-talk/29922337-what-time-does-nba-props-page-begin-to-populate), [Bettopia timing windows](https://bettopia.com/player-prop-limits-timing-windows-when-the-price-is-softest/)
- Injury news: [OddsShopper projections](https://www.oddsshopper.com/articles/betting-101/how-to-make-your-own-nba-projections), [Sports Command](https://blog.sportscommand.ai/injury-impact-betting-guide-how-the-analytics-team-reads-injury-news-before-the-market-does), [injuriesandsuspensions.com](https://injuriesandsuspensions.com/all-news/a-single-late-injury-update-can-move-the-entire-market/)
- Line shopping and hold: [Top End Sports](https://www.topendsports.com/sports-betting/guides/strategy/line-shopping/), [DeucesCracked](https://www.deucescracked.com/sports-betting/strategy/line-shopping-best-odds)
- Parlays: [arXiv 2607.14430](https://arxiv.org/pdf/2607.14430)
- NBA 2026-27 restrictions: [Legal Sports Report](https://www.legalsportsreport.com/?p=282553), [Covers](https://www.covers.com/industry/nba-bans-certain-bet-types-ahead-of-new-season-oct-16-2026), [Front Office Sports](https://frontofficesports.com/article/nba-draws-new-lines-fans-bet/)
- Australia: [ASGAM on restricting winners](https://asgam.com/2023/04/05/leading-australian-sportsbooks-face-the-music-over-practice-of-restricting-winning-players/), [WA minimum bet limits](https://www.wa.gov.au/government/publications/minimum-bet-limits), [ACT sports bookmaking rules](https://ablis.business.gov.au/service/act/rules-for-sports-bookmaking/38147), [ACMA blocks Polymarket](https://www.covers.com/industry/polymarket-barred-in-australia-over-gambling-law-breach-august-2025), [Yogonet on Kalshi](https://www.yogonet.com/international/news/2026/05/26/121713-australian-regulators-scrutinize-us-prediction-platforms-offering-markets-on-local-political-events)
- Joel Williams: [betwithjoel.com](https://betwithjoel.com/joel-williams/), [Betfair Hub](https://www.betfair.com.au/hub/author/jwilliams/)
