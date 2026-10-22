# NBL player props: what each book does when a player does not play (checked 21 Oct 2026)

From search results only; the books' own pages are not reachable from the cloud session. **Read each book's
terms page in a browser before any real stake**: rules change, and some of these are US-basketball wording
that may or may not cover NBL markets.

| Book | Player does not take the court | Plays any time at all | Overtime | Source |
|---|---|---|---|---|
| Sportsbet | void | bet stands, whatever the minutes | counts | Sports & Novelties terms (updated about six weeks before 21 Oct 2026, per the search snippet); help article "My Player Did Not Play" |
| PointsBet | void (a regular multi loses that leg; a same-game multi is void entirely) | stands | not stated | PointsBet support article |
| Ladbrokes | void (US basketball player props page) | stands | counts (US basketball page) | Ladbrokes help, "Player Injuries"; whether it covers NBL is not stated |
| TAB | not found | not found | not found | no TAB basketball rule turned up |

What this means for the model:
- The grader (`nbl/model/grade.py`) and the backtest treat a player who did not take the court as void and a
  player who played any minutes as live. That matches Sportsbet and PointsBet.
- A player who plays two minutes and is hurt is a losing over at these books. The projection already
  counts every played game, short ones included, so this is priced in, not ignored.
- The price sheet uses each team's last squad. A late out voids his props but moves his teammates' (more
  minutes for others) and the team markets: re-run after team news before comparing with a book.
- Same-game multis: not used here; one book voids the whole multi if any player does not play.

Sources:
- Sportsbet, Sports & Novelties Rules: https://helpcentre.sportsbet.com.au/hc/en-us/articles/115013564287-Sports-Novelties-Rules-Terms-Conditions
- Sportsbet, My Player Did Not Play: https://helpcentre.sportsbet.com.au/hc/en-us/articles/18431742362125-My-Player-Did-Not-Play-What-Happens-To-My-Bet
- PointsBet: https://support.pointsbet.com.au/hc/en-au/articles/10879871051791-What-happens-to-my-bet-if-a-player-I-selected-does-not-play-any-game-time
- Ladbrokes, Player Injuries: https://help.ladbrokes.com.au/s/article/Player-Injuries
