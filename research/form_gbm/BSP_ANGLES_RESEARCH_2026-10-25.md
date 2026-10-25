# Theories for an edge at Betfair SP, and what our data can test (25 Oct 2026)

Founder: "do some research on theories to find BSP angles". Read from the literature and the trade press, each source
rated for strength; then matched against what we hold (open, BSP, result, and timestamped corporate flucs in the archive)
and what we do not (the exchange's own pre-off prices, volumes and order book; place BSP).

## What we already know from our own tests (this folder)
- Backing at BSP with our price: zero, every way tried (23 and 25 Oct). Blending our price with BSP: worse than BSP.
- Laying at BSP where we rate a horse 1.6x+ the BSP chance: A/E 0.37 at $15-$30, holds $8-$30 and $30-$50. The one
  BSP angle that has held in both halves of the holdout.
- Late corp moves (last 10/30/60 min) are already in BSP: late firmers win 1.15x BSP's expectation but return -12%
  backed at BSP; drifters 0.77x, lay -5% (one week of timestamped flucs).

## 1. Favourite-longshot bias (strong evidence, weak money)
The most replicated finding in betting markets: longshots return less per dollar than favourites. Green, Lee and
Rothschild put an evens favourite at 85c in the dollar and a 30/1 shot at 63c (US tote); Snowberg and Wolfers (NBER
w15923) find it "equally evident" in 2.7 million Australian starts, bookmaker and tote. On exchanges the bias is
smaller than at bookmakers because there is no margin to hide in, and studies of Betfair find prices "closely track"
win probabilities (Brown and Yang, 225m order-book observations). WHAT IT MEANS FOR US: at BSP the bias is a few cents
in the dollar at the long end, so "lay every $30+ runner" is roughly break-even after 8% commission, not an edge; our
own table agrees ($30-$1000 lay with no model: -2% / +6%). The bias is only money when a model says WHICH longshots
are the overbet ones, which is what the roughie lay already does (A/E 0.37 against a market-wide 0.9-1.0).
TESTABLE NOW: yes, and done. Nothing more to find here without the model.

## 2. Steamers and drifters (mixed evidence; our data says the move is priced by the jump)
Trade press treats late steam as "sharp money". The one horse-racing dataset found (Houghton, 65,000 UK runners, 2006,
2h-out price v SP): steamers LOST at level stakes, drifters won. Football studies split both ways; a 2025 Betfair
football paper finds closing prices unbiased. Brown and Yang (2017, 9,560 races) find no evidence that exchange laying
has corrupted racing, i.e. drifters are not systematically "dead". OUR TEST (t_late_market.py): late moves carry real
information about the result (firmers 1.15x, drifters 0.77x) and BSP already carries it, so there is no return at BSP
either way. WHAT IS LEFT: the move BEFORE it is priced. A steamer is only money if you are on before it steams, which
is the open-price edge again, and the drift forecast (drift_forecast.py) is the tool for it: it sorts the open return
(+30% / +48% on the forecast-to-firm third) and does nothing at BSP.
TESTABLE NOW: done. NEEDS: exchange prices 10-30 min out to test a "back the steamer before BSP" rule properly.

## 3. Order-book imbalance and weight of money (good evidence for prediction, none for profit after commission)
A 2025 preprint forecasts the last two minutes of price movement from Betfair's market depth with a neural net; Brown
and Yang show back and lay queues track win probability; older work notes money "particularly" moves prices in the
final ten minutes. All of it is about predicting the PRICE, not beating it: nobody shows a return after commission, and
the predictable part of the move is small and fast, which is market-making territory (quant firms, API latency, both
sides of the book), not a tipping business. WHAT IT MEANS FOR US: a back-at-X, lay-at-BSP trade on the horses our drift
forecast says will firm hardest is the only version worth a look, and it is a trading edge measured in cents, not the
40%+ we get at the open.
TESTABLE NOW: no (no exchange order book). NEEDS: Betfair historical exchange data (PRO tier has depth), or our own
recorded stream from Wednesday's lay book.

## 4. BSP against bookmaker SP (strong evidence BSP is the better price; no edge, just a venue choice)
UK: BSP beat bookie SP in 86% of 11,300 races by about 14.5% after commission (FlatStats, 2010); every guide agrees BSP
beats SP from about 3/1 up. Australia: corporate books run 115-130% at the jump against 101-105% on Betfair (Krokodds,
unsourced), which matches our own measurement (corps 30% shorter than BSP ten minutes out, only 9% of runners with a
corp price above BSP). WHAT IT MEANS FOR US: if a bet is ever taken late, it is taken on the exchange, never at a
bookmaker. Not an edge; a rule about where to stand.
TESTABLE NOW: done (section 3 of t_late_market.py).

## 5. Place market and each-way (no exchange studies found; the mispricing argument is sound)
No published work on Betfair place-market efficiency. The theory: place prices are set by less money and more casual
money than win prices, and the win market's favourite-longshot shape does not carry over cleanly to place terms (a
horse's place chance is not a fixed function of its win chance; it depends on the field's shape). Our own 23 Oct note
ruled place bets out at the OPEN because the corp place margin is large. On the exchange the margin is commission only.
TESTABLE NOW: partly. The archive sample carries betfairPlaceDiv (place BSP) and finishPosition, so a first look at
"our win probability -> place probability v Betfair place SP" is possible on 292 races; a real test needs the full
archive. NEEDS: a place-probability method (Harville or a fitted one) on our win probabilities, then the same A/E and
half-split test as the lay.

## 6. In-play (evidence of surprise-news mispricing in football; nothing for racing)
In-play football prices misprice for several minutes after a surprise goal (Reading, 1,004 EPL matches). Racing
in-play lasts one to three minutes with no clean "news" event, is dominated by latency and pictures-delay traders, and
Australian in-play betting is phone-only by law for bookmakers and not offered on the exchange in-play for racing.
NOT FOR US.

## 7. Cross-market: back at the bookmaker, lay at BSP (sound, and the hedge we already tested)
The structure exists (Racing & Sports describes it); a BSP lay is not a guaranteed lock because BSP is unknown when
the lay is placed, and commission eats the gap. OUR TEST (t_bsp_angles.py A): back our value at the open, lay at BSP
for a level result: +18.5% locked per bet, 57% of bets lock a profit, std 0.60u against 3.38u. The founder declined it
(25 Oct: "we make more profit than that"), correctly for a punter who can carry the variance. It stays the right
answer if the bank ever has to be smaller than the swings.

## What this adds up to
1. The literature agrees with our tests: BSP is close to fair, the open is not. Every documented BSP "angle" is either
   a few cents (favourite-longshot) or a trading edge that needs the order book and speed. The exception is a model
   that is right about WHICH horses the market has wrong, and we have one: the roughie lay.
2. The two things worth testing that we have not: (a) PLACE on the exchange, from our win probabilities, on the
   archive once it lands (place BSP is in the data); (b) the drift-forecast steamer trade, which needs exchange prices
   before the jump: either Betfair's historical data or a recorded stream, which the Wednesday lay book can start
   capturing at no cost.
3. Not worth time: lay-the-field, lay every favourite, late corp bets, in-play.

Sources (web search summaries; the full texts are egress-blocked from this environment and were not read):
favourite-longshot: Ottaviani & Sørensen survey; Snowberg & Wolfers NBER w15923; Green, Lee & Rothschild "Favorite-
Longshot Midas". Exchange efficiency: arXiv 2402.02623 (UK Betfair time series); Brown & Yang, J. Sports Economics 2017
(UEA eprint 56841). Order book: arXiv 2510.16008; Brown & Yang order-book paper. Steamers: Houghton 2008 via geegeez
"Steamers and Drifters Part 2"; football-data.co.uk closing-efficiency notes. BSP v SP: FlatStats 2010; theracelab;
Krokodds AU guide (unsourced). In-play: Reading EMDP 2019-20. Cross-market: Racing & Sports back-to-lay FAQ.
