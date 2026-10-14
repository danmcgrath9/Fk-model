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
