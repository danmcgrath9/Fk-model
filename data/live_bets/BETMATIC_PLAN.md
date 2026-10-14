# BetMatic go-live plan (14 Oct 2026)

From BetMatic support's answers (14 Oct): market-open bets fire within seconds; min and max odds supported
(check_max_odds + max_odds); bets load as soon as fields are out; several bets on one runner = one bet each;
cancel via POST /notification/{id}/cancel/ (no editing); bet status and P/L by WebSocket or REST; a market-open bet
targets ONE bookmaker (no failover); the bot must run on a real machine 24/7 (bookmakers block VPS), and a bet
pending when the machine is offline at the open expires. $199/month + 1% of turnover ($10k-$300k); no trial.

Standing rule: Claude builds the order files and the API payloads; the founder's machine sends them. Claude does not
place bets.

## Phase 0: set-up (this week)
Founder:
- Take Dave's intro to Joel (BetMatic waives the subscription for a group of FK subscribers).
- An always-on mini PC at home, on a UPS if possible, wired internet.
- Sign up; connect the TAB account only.
- Paste the Create Bet and WebSocket pages (betmatic.gitbook.io is blocked from the cloud session).
- Set the bank (at least twice the worst backtest drawdown at the chosen unit).
Claude:
- betmatic_send.py: order file -> one market-open bet per price step (TAB, min_odds, max_odds, stake), with a dry-run
  mode that prints the payloads; a cancel list for scratchings and rating changes.
- A fill logger: WebSocket/REST bet status -> betmatic-book.md (price taken, stake placed, account), then the
  forward test reads real fills instead of Form King's open.
- Correct the backtest page's expenses for the 1% turnover fee.

## Phase 1: small stakes (about 2 weeks)
- First meeting through BetMatic's Simulation tab (no real bets), then live at a small unit (founder's call).
- Daily flow: 11am fields pull -> price -> order file -> founder approves -> founder's machine sends -> before the
  open, cancel and resend anything hit by a scratching or rating change -> bets fire at TAB's open -> fills logged ->
  results settled with TAB's actual deductions -> tips posted at the opening price.
- Measure every meeting: fill rate against the paper book, price taken against Form King's open, speed, partial
  stakes, any account restriction.

## Phase 2: review after about 150-200 bets
Scale to $100 a unit if: fills track the paper book, prices match the open, no TAB restriction, and results sit
within the forward test's range. Then decide: the 40% edge on long ones, a second early bookmaker, the odds feed
(oddsmatic.app) for live opens.

## Stop conditions
- TAB limits or restricts the account.
- Fills or prices fall well short of the paper book for two straight weeks.
- The machine misses a market open twice in a week (fix the machine before going on).

## Notes (14 Oct)
- Founder: TAB's opening price matches Form King's open "and it's normally slightly better", so the backtest's fills
  at Form King's open are, if anything, conservative on price.
- Account limits: deal with them when they come (founder). Every bet reports Placed / Not Placed / Rejected with the
  stake and price; the ladder sends each horse as several small bets; Victoria's MBL makes the TAB take a win bet to
  win $1,000 (country/provincial) or $2,000 (metro). Planned: a post-open check that resends a refused or cut step
  at an MBL-sized stake with the same minimum odds. Asked BetMatic whether the bot accepts a reduced offer.

## Order of play (founder, 14 Oct): "Big dog eats first"
Our orders fire at TAB's open; members get the tips (with minimum prices) once our fills are back; then the public X
post. No member cap is needed to protect our fills, because we are already on.

## Start-up checklist (14 Oct)
1. Machine: the 2019 MacBook Air (1.6GHz dual-core, under BetMatic's 4GHz spec) for sign-up and tests; buy the GMKtec
   M8 (Ryzen 5 PRO 6650H, 16GB, $549.99 Amazon AU) for live betting; confirm Windows 11 on arrival.
2. Sign up to BetMatic; install the bot; connect TAB as the only session.
3. On that machine: Python, the repo's betmatic/ folder, BETMATIC_EMAIL and BETMATIC_PASSWORD set as environment
   variables there (never in the repo, never sent to Claude). Run `betmatic_send.py check`.
4. $2,000 into TAB (covers a two-meeting day at $25 a unit if every order fired).
5. Simulation tab once, then one $1 bet to the TAB session, then the first meeting at $25 a unit.
