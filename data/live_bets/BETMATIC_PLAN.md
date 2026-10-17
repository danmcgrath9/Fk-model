# BetMatic go-live plan (14 Oct 2026)

From BetMatic support's answers (14 Oct): market-open bets fire within seconds; min and max odds supported
(check_max_odds + max_odds); bets load as soon as fields are out; several bets on one runner = one bet each;
cancel via POST /notification/{id}/cancel/ (no editing); bet status and P/L by WebSocket or REST; a market-open bet
targets ONE bookmaker (no failover); the bot must run on a real machine 24/7 (bookmakers block VPS), and a bet
pending when the machine is offline at the open expires. $199/month + 1% of turnover ($10k-$300k); no trial.

Standing rule: Claude builds the order files and the API payloads; the founder's machine sends them. Claude does not
place bets.

## LIVE from Monday 19 Oct 2026 (founder, Sat 17 Oct)
Founder: "I've been holding off actually betting until I saw the model work, but I think it's time to fire it up starting Monday next week. Leave all the orders but we are firing live live on Monday." Every order already on BetMatic stays. Sunday's Moe orders stay pending and are paper unless the TAB account is funded; from Monday 19 Oct (Echuca, 68 orders already scheduled at $100 a unit) the BetMatic fills are real bets, recorded in betmatic-book.md from TAB's actual fills and deductions (-deductions-actual.txt), not Form King's open. Before each first race: the account funded, and a BetMatic check showing the bot machine connected and the session running (the 17 Oct check found it offline while the app looked connected).

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
- Live model: v10 from Sat 17 Oct pricing (gear detail + past price moves; founder 15 Oct).
- Daily flow: fields pull per meeting at the time the founder gives, after its riders are declared (15 Oct: Bendigo 12:15, Avoca 12:45, Wodonga, Horsham, Moe 1:15) -> price -> order file -> founder approves -> founder's machine sends -> before the
  open, cancel and resend anything hit by a scratching or rating change -> bets fire at TAB's open -> fills logged ->
  results settled with TAB's actual deductions -> tips posted at the opening price.
- JOCKEYS AND GEAR ARRIVE AFTER THE FIELDS (found 15 Oct 2026): at Cranbourne 16 Oct's 11:21am fields pull, 27 of 105
  runners had no jockey and no runner had a gear change posted; by the 5pm market snapshot jockeys were in (4 blank) and
  37 runners carried gear changes. The model was trained on races pulled after the fact, with every jockey and gear
  change, so a fields-time price is off its training data for a quarter of the field (Strike Package $9.26 -> $3.15
  once Mark Zahra was booked). The Meeting Summary refresh (scripts/morning_odds.py, odds_only in fk-daily-pull, 5
  credits a meeting) writes the fresh entry over the stored one, jockeys and gear included, so the routine is: fields
  pull, then the refresh once riders are declared, then export, price and build the orders. Check jockey coverage on
  the export before pricing (run_meeting.sh prints it); price anyway only with the blank-jockey runners named.
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

## Sending from GitHub, not the PC (14 Oct)
The fk-betmatic workflow runs betmatic_send.py on GitHub: Claude commits the order file and starts the workflow
(dry run first), the founder sees the payloads and approves in the GitHub app, and the bets go to BetMatic; the PC
only runs the BetMatic bot. Environment "betmatic" (required reviewer: the founder) holds BETMATIC_EMAIL,
BETMATIC_PASSWORD and BETMATIC_TAB_SESSION. Ledgers and placements are committed back to data/live_bets/. The
seconds-level shortfall resend (later) is the one piece that may still need to live on the PC.

## Unit size (founder, 16 Oct): $100 a unit from Moe Sun 18 Oct and every meeting after ("we are at $100 a unit for moe and moving forward").

## Start (founder, 14 Oct): $75 units (was $50 earlier the same day), first live meeting Bendigo Saturday or a Sunday meeting (decided 15 Oct)
TAB balance about $5,600, bank about $7,500. Biggest single bet $375 (5u); a big Saturday card is about 11u ($850)
out at once. Worst losing run at $75: about $2,000 in the holdout with the live rules, $3,600 in the full backtest. Orders must be with BetMatic before TAB opens, and non-metro Saturday
fields come out on the Thursday, Sunday fields on the Friday, so the set-up (bot running with TAB connected, the
"betmatic" GitHub environment and its secrets, check run, $1 test) has to be done by about 11am on the day the
chosen meeting's fields come out.

## Keeping the volume up (14 Oct 2026, t_overlap.py)
The forward test staked half what its races support because the 5-9 Oct model files were priced before final fields:
horses that never ran held 10-19% of each race's probability, so every starter's price was ~15% too long. Rules from here:
1. Price on the FINAL field only (the 11am routine). betmatic_orders.py now drops emergencies and scratched runners
   (entry-numbers file and any SCR in the fields/prices file) and re-spreads each race's probability over the runners
   left; it prints a WARNING naming any race whose runners held under 97% before the re-spread. A warning means re-make
   the model file on the final field before sending.
2. A scratching that lands before the open: rebuild that race's orders and, once live, cancel and resend that race
   (Caulfield 17 Oct R10 Pillow Fight is the first case: three runners' minimum odds tighten).
3. Weekly check: staked per race. Expect about 1.0u a race with the live rules (holdout 1.14u); under 0.7u for a week
   means something is starving the orders again.
4. Planning figure at $75 a unit: about $2,000 a week, $8,250-9,000 a month before $359 expenses (at $50: $1,300-1,400
   and $5,500-6,000; holdout with live rules at $50: full months +$6,500 to +$14,600 net, median week +$1,825;
   t_live_monthly.py).
5. TAB limits (t_mbl.py): Victoria only guarantees a fixed-odds win bet to win $1,000 at non-metro meetings and $2,000
   at metro. At $75 units 23% of holdout bets try to win more than that (44% of the profit); at $50, 9%. If TAB cut every
   one of them to the guarantee, $75 units still makes 80% of its uncapped profit, which is more than $50 uncapped
   ($45,300 against $37,600 over the holdout). BetMatic takes a reduced offer at the reduced stake, so log every
   reduced offer: the stake TAB actually took is the number that matters.

## Approval (15 Oct 2026, founder)
The "betmatic" environment has NO required-reviewer gate, by the founder's choice ("I'm fine without approval right
now, you can send me the copy here and I'll have enough time to review"). So the approval is in the chat: Claude shows
the exact bets (meeting, race, horse, number, minimum and maximum odds, stake in dollars, total) and starts the send only
after the founder approves that exact list. Any change to the list after approval is shown again. Dry run first,
every time. TAB session: 636816 (BETMATIC_TAB_SESSION); the Sportsbet session is set up as a spare and is never sent to.

## Lessons from the first live day (15 Oct 2026)
- GitHub keeps one waiting run per concurrency group and cancels the older one when another is queued: Wodonga's live
  send was cancelled behind Horsham's and had to be resent. The group is removed; runs may overlap and the ledger push
  retries.
- Horsham (Sunday) was sent, then cancelled at the founder's word to re-price after the evening gear changes. A
  cancelled notification keeps its label, so the duplicate check now ignores cancelled ones; otherwise the re-send would
  have skipped every bet.
- Form King lags the rider declarations and posts gear changes later still: a refresh (5 credits a meeting) before
  pricing took Bendigo from 15 riderless runners to 4 and 0 gear changes to 29.

## Short opens: edge 1.15 when TAB opens under $4 (founder, 16 Oct 2026, from Moe Sun 18 Oct on)
research/form_gbm/t_short_edge.py. Each runner whose 1.15 minimum is under $4 gets a second ladder capped at $3.99; the
normal 1.2 ladder's steps under $4 are lifted to $4.00, so any opening price meets exactly one rule. Under $3 opens were
break-even at every edge tried; the 1.15 extras still beat the open (77% shortened, open 1.23x BSP). Moe: 1 runner
affected (The Minstrel Boy), Echuca: 1 (Sihaya).
