# BetMatic API notes (from BetMatic's documentation, pasted by the founder 14 Oct 2026)

Base: https://betmatic.app/api/
Login: POST /api/account/login/ {"email", "password"} -> {"token"}. Every call: header "Authorization: Token <token>".

## WebSocket (real-time/websocket)
- wss://betmatic.app/ws/private?token=<token>. Invalid/missing token -> HTTP 403 at the handshake.
- NOT enabled by default: request access by emailing support@betmatic.io.
- Messages are JSON; branch on "category":
  - "bet_history": a bet-history update, payload in "data" (fields not documented on this page: log raw).
  - "odds_update_anwser" (spelt that way by the API): odds answer, payload in "data".
  Ignore unknown fields, log unknown categories.
- POST /api/notification/odds/request/ {"code": "Galloping"|"Harness"|"Greyhounds", "competition": venue from
  GET /api/competition/namecodes/ (e.g. "HAMILTON"), "event_number": race number}. 200 "OK" only means relayed;
  the odds come back on the WebSocket, read by OUR OWN running bots from their live bookmaker sessions (no bot
  online = no answer). 404 "Competition not found".
  Use for us: read TAB's own price at the open from our session, to record the real opening price per fill.
- Example client: requests + websocket-client + rel; run_forever(dispatcher=rel, reconnect=5).

## From support's email (14 Oct)
- Market-open bets fire within a couple of seconds of the open; min odds; check_max_odds + max_odds.
- One bet per (runner, bookmaker, criteria): resend for each price step.
- Cancel a scheduled bet: POST /notification/{id}/cancel/ ; no editing (cancel and recreate).
- Market-open bets target one bookmaker; no failover. "High Odds First" only for standard bets.
- Pending bets expire if the bot machine is offline at the open.

## Still needed
Create a Bet (placing-bets/create-bet): fields, market-open flag, bookmaker, stake, min/max odds, response id.
API Overview (api-reference/overview): rate limits, errors.

## API Overview and Create a Bet (pasted 14 Oct)
- Base https://betmatic.app/api; token valid 60 days (refresh only within 7 days of login). No webhooks; polling has
  no enforced rate limit (keep it to a few requests a second). WebSocket optional.
- No sandbox or dry-run flag in the API: every accepted instruction can place real money. Dry run = the website's
  Simulation tab (Tip Connect page). Safe start: simulate, then $1 bets to ONE session with a unique label.
- POST /notification/create/ only broadcasts to running bot machines; 200 can still mean nothing placed (check the
  message: "no signal was sent to the bot" = failure). Bot offline = signal lost, never replayed.
- No duplicate detection: unique label per bet; on a timeout, GET /notification/?label=... before retrying.
- Racing fields: type "Fixed Wager", sports "RACING", competition = exact UPPERCASE name from
  GET /competition/namecodes/, code "Galloping", event_number, market "Fixed Win", selection = saddlecloth number as
  a string, stake (dollars PER SESSION: target one session or the stake multiplies), start_time optional.
- Odds: check_odds + odds (minimum), check_max_odds + max_odds.
- Targeting: bookies "id&id" (IDs from GET /bookie/names/), target_session "id&id" (from GET /bookieaccount/).
- Market Open: is_market_open true (no is_scheduled/auto_trigger); max_attempts and delay_between_attempts for retries
  (website uses 60 x 1s). One notification per bookmaker, id returned as "a&b&c". If the bookmaker's market is ALREADY
  open when the bet is created, it fires immediately at the current price (odds checks still apply), so orders must
  be in before TAB opens. Pending ones: GET /notification/scheduled/; cancel POST /notification/{id}/cancel/;
  POST /notification/{id}/trigger/ fires now.
- Check placement: GET /bet/notification/{id}/ (per-session submit_result and odds taken). GET /bet/ = per-bookmaker
  history; GET /notification/ = one row per instruction.
- 400 "Internal error." usually means a wrong venue name, a race already run, a bad market string or a wrong type.
- Support, 14 Oct (replied 81 seconds after the question, so probably an automated assistant: confirm on the first
  live meetings): if the TAB offers a reduced amount, the bot accepts the reduced stake, and the accepted amount (not
  the attempted one) is what is recorded and sent on the WebSocket feed. So a post-open check can read the shortfall
  and resend it.

## API Overview and Authentication pages (pasted by the founder 15 Oct)
- Pagination: lists page at 10-20 rows by default (page_size max 100); an out-of-range page returns page 1, not an
  error; "count" is never below 1, so count from "results". betmatic_send.py now walks every page (get_all) for
  sessions, bookmakers and the race schedule; before this it read page 1 only, so TAB or a venue on page 2 would
  have stopped the send.
- Login: send "version": "API" (now sent). Rate limit on login 30/min; betting and data endpoints unlimited.
- Tokens are stateless JWTs: logging in again does not invalidate the bot's or website's tokens, so a login per run is
  fine. A leaked token cannot be revoked by logging in again: tell support@betmatic.io.
- POST /account/logout/ disconnects a bot session: never call it from the sender.
- Diagnostics worth using: GET /account/readiness/ (used by `check`), GET /account/connect_activity/, GET /bot/logs/
  and GET /bot/logs/{notification_id}/ (what the bot did with one bet), GET /bet/summary/.
- POST /bookieaccount/control/{id}/ starts or stops one session from the API.
- Errors: 400 validation ({"error": ...} or {"field": [...]}), 401 token, 403 subscription inactive, 404, 500.

## Bookmakers page (pasted 15 Oct)
- GET /bookie/names/ is a plain array of {id, title, markets_unavailable, enabled, bonus_enabled, sports, maintain}.
  The bookmaker's NAME is "title": the sender matched "name" and would have stopped on the first live send with
  "bookmaker 'TAB' not in GET /bookie/names/". Fixed: matches title, and refuses to send when TAB is disabled or in
  maintenance, because BetMatic skips bets to a bookmaker in maintenance without an error. `check` prints TAB's row.
- bookies field: numeric ids joined with "&". GET /bookie/{id}/ adds home_link, note, support_manual_login.

## Race Schedule, Create a Bet, Bet Types, Bet Examples, Session Targeting, Scheduling (pasted 15 Oct)
- start_time: "copied directly from GET /competition/namecodes/; if omitted, the system matches the NEXT race" for the
  venue + code + race number, and the schedule runs 5-6 days ahead. The sender now matches each bet to the schedule
  entry on the ORDER'S date and pins it with that race's startTime; a bet is skipped (and the skip written to the
  ledger) if that race is missing, the saddlecloth is no longer in "runners" (scratched), or the name at that number
  is not our horse. Before this, Saturday's Caulfield orders sent before a midweek Caulfield meeting would have fired
  on the midweek race.
- target_session must be numeric: anything else is IGNORED and the bet goes to every running session. The sender
  refuses a non-numeric --session.
- Fixed Wager to one session: each order bets exactly its stake. ensure_total_wager / allow_double_bets only matter
  across several sessions; we send allow_double_bets false.
- Market open: max_attempts / delay_between_attempts are retries if the first placement fails; BetMatic's own
  example uses 60 x 1s. Our default is now 60 (every retry still keeps min and max odds).
- GET /bet/notification/{id}/ returns {"bets": [...]}; status is "" until Won / Lost / Refund. `status` reads "bets".
- GET /notification/scheduled/ lists only the last 24 hours: the ledger keeps every notification id for cancels.
- Response id for a market-open create is "&"-joined (one per bookmaker); we target TAB only, so one id.

## Scheduled bets, Market Open, Trigger & Cancel (pasted 15 Oct)
- GET /notification/scheduled/ is a plain array of pending notifications (last 24 hours only); fields as GET
  /notification/ ("tip": {"competition": {...}}, "label", "is_canceled"). New sender command `pending LEDGER`
  (also a workflow action): every ledger id must be pending before the open; anything not pending is named so it can
  be resent while there is time.
- Market Open: one notification per bookmaker; a 404 "The market is not available for the specified bookies" means
  TAB does not offer the market (logged as FAIL). Markets are often posted early morning: the bot must be running
  then, or the bet is missed (BetMatic suggests scheduled session start times in the bot's settings).
- Trigger: fires now; 400 if already triggered or the market is closed (about 5 hours after the start). Cancel: "OK";
  400 if already placed or cancelled; a bet already sent to the bookmaker cannot be undone.

## List Bets (pasted 15 Oct)
- GET /notification/ pages at 10 by default; filters include label, date_from / date_to (Sydney days; date_to is
  exclusive, so use the day after), code, market, source (MANUAL for our own API bets; source_type is "API").
- The duplicate check now treats a bet as already sent only when a returned notification's label is EXACTLY ours (the
  docs do not say whether ?label= is exact or partial).
- Bet state: no records yet = queued or nothing placed; total_accepted 0 after the bot reports = failed (see
  submit_result); total_accepted > 0 with empty status = placed, unsettled; status Won / Lost / Refund = settled.
- stake / target_profit / total_wager default to 1: for Fixed Wager read stake; actual dollars per session are in the
  bet records' "amount".

## Bet Records (pasted 15 Oct)
- One record per session per bet: amount (dollars actually staked), current_odds (odds taken), submit_result
  ("Success" or an error code), submit_error (message), status (Won / Lost / Refund, "" = unsettled or failed), profit,
  bookie (numeric id), display_name.
- The sender's `status` command now reads those fields (it read "odds" and "stake", which do not exist) and flags a
  REDUCED bet (TAB took less than asked: the limiting record), a FAILED submission, and any fill below our minimum
  odds; it totals asked against taken.

## Bet Lookup (pasted 15 Oct)
- GET /bet/notification/{id}/ -> {"bets": [...], "logs", "session_info", "bot_logs", "average_deduction_percentage"}.
  An empty "bets" right after firing = still in flight (seconds); staying empty = no session received it.
- average_deduction_percentage is TAB's actual scratching deduction on the bet: `status` now prints it and saves it in
  -placed.jsonl, replacing the founder's manual TAB deduction readings and the 16c estimate for live bets.
- POST /bet/search/ {"ids": [...]} fetches known bet record ids. GET /notification/{id}/race/detail/ gives the race's
  result ("5/1/8/3") for settling without Form King.

## Bet Summary (pasted 15 Oct)
- GET /bet/summary/ -> {"won", "lost", "pending"}; filters date_from / date_to (Sydney days, date_to exclusive),
  bookie, market, code, label. New command `summary DAY [--ledger LEDGER]` (also a workflow action): the day's counts
  next to the number of bets the ledger sent. It counts every BetMatic racing bet that day, ours and any placed by hand.

## Sessions (pasted 15 Oct)
- GET /bookieaccount/ is a plain array: id, display_name, bookie (display name, e.g. "TAB"), balance (real money),
  bonus_balance, bot_running, update_time. `check` now prints balance and update_time per session.
- `send` now refuses when the session's real-money balance is below the total stake the file would place, because a
  Market Open bet that finds no money fails at TAB. `--allow-short` overrides (deliberately not exposed in the workflow).
  The balance is BetMatic's last reading (update_time), not live.
- POST /bookieaccount/control/{id}/ {"command": "ON"|"OFF"} starts or stops one session (30-60 s to show); control/
  with all_on / all_off does every session. Only works while the bot machine is running. NOT wired into the sender:
  session start times stay in the bot's own settings, so a script cannot switch the account off by mistake.

## Bot Diagnostics (pasted 15 Oct)
- GET /account/readiness/: problems, bot_session_running (connected bot machines), accounts_running. A session can show
  bot_running while no bot machine is connected; then nothing places. `send` now refuses when bot_session_running is 0,
  and `check` prints readiness plus the last five connect/disconnect events (GET /account/connect_activity/).
- GET /bot/logs/{notification_id}/: the bot's own lines for one bet. `status` prints them under any FAILED bet and any
  bet with no placement, so a failure arrives with its reason ("none" = the bot never received it).

## Tip Connect publishing (pasted 15 Oct) - NOT BUILT, founder decision
- POST /pick/tipster/publish/ with a package API key publishes tips (venue, race, saddlecloth, amount_units, min/max
  odds, start_time) to a BetMatic tip package; subscribers' bots bet them automatically. POST /pick/tipster/message/ sends
  a pre-alert to wake subscribers' sessions a few minutes before. Duplicates are skipped silently.
- Needs approved-tipster status and a package API key from BetMatic support. If taken up, the key goes in the GitHub
  "betmatic" environment like the others, never in a file or a message.
- Clashes with the standing order of play (our TAB bets first, then members, then X): a published tip fires on every
  subscriber's bot at once and competes with us at the same bookmakers at the open. It would have to publish only after
  our own fills are in (status), and members' fills would come at worse prices.

## WebSocket and odds request (pasted 15 Oct) - NOT BUILT
- wss://betmatic.app/ws/private?token=... (access by email to support). POST /notification/odds/request/ asks our own
  running bot to read a race's live odds from the TAB session; the answer arrives only on the WebSocket
  (category "odds_update_anwser", spelled as sent). Would give TAB's own price per runner from our own session, a check
  on the fill price before the open. Not needed for Market Open bets, which carry min/max odds already.

## Creating a Bet, website (pasted by the founder 18 Oct 2026)
- Bet types: Fixed Wager (flat stake as-is); Fixed Profit (stake from a target profit at current odds); HIGH ODDS FIRST
  (one total budget, "allocated starting with the highest-priced bookmaker"; Best Odds / Random Accounts filters are
  ignored for it, because it already picks accounts by price).
- Stake allocation for Fixed Wager / Fixed Profit: "Each account" (every account bets the full amount, so $10 x 5
  accounts = $50) or "Split total" ($10 over 5 accounts = $2 each). High Odds First always works from one total.
- Allow Double Bets (with Split total): a stake that fails at one account is re-placed at accounts that succeeded,
  at most two bets per bookmaker.
- Odds checks per bookmaker: Check Min Odds (default on, 2.00) skips any bookmaker below it; Max Odds skips above.
- Timing: Now / Schedule (seconds before the jump, auto trigger) / Market Open ("triggers when each bookmaker's market
  first becomes available"; Market Open bets are split per bookmaker, retry delay 1s, max attempts 60).
- Built-in templates include "Market Open TAB" and "Best Odds (Top 5)" (the 5 bookmakers with the best prices).
- Selection filter "Best Odds (top N)": only the N accounts with the best current odds place the bet.
- Live odds: "Get live odds" pulls prices from the running bot (up to a minute); the All prices grid shows EVERY
  bookmaker's price for the runner. Same source as POST /notification/odds/request/ + the WebSocket: a per-bookmaker
  price feed from our own bot, free of Form King credits (WebSocket access must be requested from support).
- Targeting: Machines / Bookies / Accounts filters; empty = all; a targeting that resolves to no account is created
  and silently never sent. Per-account delays exist for staggering.
- Outcomes per account: Bet Placed / Bet Not Placed / Bet Rejected (below min odds, account not running, market
  closed, bookmaker refused).
- NOT stated: whether High Odds First can be combined with Market Open (support, 14 Oct: "High Odds First only for
  standard bets"), and how far High Odds First fills the top bookmaker before moving to the next.

## Create a Bet, API, full page (pasted by the founder 18 Oct 2026)
- Stake fields by type: stake (Fixed Wager, dollars PER SESSION), target_profit (Fixed Profit), total_wager (High Odds
  First: the total distributed across sessions).
- Session targeting: bookies "id&id"; target_session "id&id" (numeric only); choose_best_odds N (only the N sessions
  with the best current odds, 0 = all); choose_random_accounts N; ensure_total_wager (treat the stake as a TOTAL across
  sessions); enable_group_bot (needs choose_best_odds / choose_random_accounts / ensure_total_wager).
- Odds: check_odds + odds (min), check_max_odds + max_odds, boost_if_available, spg_if_available (Same Price Guarantee).
- Market Open: is_market_open true, max_attempts / delay_between_attempts; ONE notification per bookmaker (ids "a&b&c");
  bookies omitted = every bookmaker that posts that venue's markets where we have a running session; a market already
  open fires at once; odds checks apply at placement; don't combine with scheduling; /trigger/ fires a pending one.
- A 200 can still mean nothing was placed ("no signal was sent to the bot"); bot offline = signal lost, never replayed.
- NOT stated on this page: High Odds First with is_market_open, and ensure_total_wager across the per-bookmaker split
  of a Market Open bet. Session Targeting / Bet Types / Market Open Bets pages should say.

## Support, 18 Oct 2026 (Thomas)
- WebSocket access ENABLED on the account.
- High Odds First, choose_best_odds and ensure_total_wager do NOT work with Market Open bets (a Market Open bet targets
  one bookmaker); use Fixed Wager or Fixed Profit for Market Open.
- High Odds First: the FULL stake goes to the highest-priced bookmaker; it moves down to lower-priced ones only if the
  bet is rejected, limited, or the stake is not fully filled.
- (14 Oct, same thread) oddsmatic.app: BetMatic's separate odds WebSocket service, streaming live prices as markets open.
