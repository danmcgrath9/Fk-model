# Tipster bot (agreed with the founder 15 Oct 2026, not built yet)

Bet a followed tipster's tips through BetMatic at the best price across the founder's bookie accounts. Runs on the
always-on laptop beside the BetMatic bot. Free: no X API, no subscriptions.

Inputs (both feed one bet path):
- X: post notifications on in the X app; the founder taps Share -> our Telegram bot (his tap is the approval). The bot
  reads the tweet text from X's public oEmbed service (publish.twitter.com/oembed; UNTESTED that it still returns text).
- Patreon: Patreon emails each new post to patrons; the bot holds a Gmail IMAP IDLE connection (pushed instantly, no
  polling) with a Gmail app password, and fires with no tap. UNTESTED: whether his emails carry the tip text or only a
  link, and how fast Patreon sends them (measure on the first posts before real money).

Bet path: parse venue / race / horse / price -> match to GET /competition/namecodes/ (start_time pinned, runner number
and name checked) -> POST /notification/create/ to every running bookie session with choose_best_odds = 1 (BetMatic
keeps only the session paying the most), min odds = his tweeted price (or ~5% under), fixed stake cap, no second bet
on a runner already backed; ensure_total_wager to fill a limited stake at the next-best bookie (re-read that doc
section before relying on it). Reply to the founder on Telegram with what was taken.

Secrets: the Telegram bot token and the Gmail app password live ONLY on the laptop, never in the repo or a message.
His paid tips are for the founder's own betting; never reposted through Mercer Tipping or X.
Waiting on: token and app password set up on the laptop, 2-3 sample tweets and one forwarded Patreon email, extra
bookie accounts added to the BetMatic bot.
