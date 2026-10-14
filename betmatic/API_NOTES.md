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
